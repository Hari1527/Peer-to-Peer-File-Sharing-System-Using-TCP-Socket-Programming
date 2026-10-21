"""TCP File Client module for downloading files from peer nodes.

Connects to remote peer TCP file servers, sends file requests, downloads
binary chunks into temporary files, verifies SHA-256 integrity, and moves
completed files to the final destination directory.
"""

import hashlib
import json
import logging
from pathlib import Path
import socket
from typing import TYPE_CHECKING, Any

from app.config import PeerConfig
from app.core.security import sanitize_filename
from app.core.tcp_protocol import (
    ErrorCode,
    MessageType,
    ProtocolError,
    recv_file_response,
    recv_message,
    send_cancel,
    send_file_request,
)
from app.schemas.transfer import TransferStatus

if TYPE_CHECKING:
    from app.core.transfer_manager import TransferManager

logger = logging.getLogger(__name__)


class TCPFileClient:
    """Client for downloading files from remote peers via TCP sockets."""

    def __init__(self, config: PeerConfig) -> None:
        """Initialize the TCP File Client.

        Args:
            config: Peer configuration object.
        """
        self.config = config

    def download_file(
        self,
        host: str,
        port: int,
        file_id: str,
        filename: str,
        expected_checksum: str,
        expected_size: int,
        transfer_id: str,
        transfer_manager: Any,
    ) -> Path:
        """Download a file from a remote peer TCP server.

        Args:
            host: Remote peer host/IP.
            port: Remote peer TCP port.
            file_id: SHA-256 hash identifier of the requested file.
            filename: Target file name.
            expected_checksum: Expected SHA-256 hex digest.
            expected_size: Expected file size in bytes (0 if unknown).
            transfer_id: Active transfer UUID for progress tracking.
            transfer_manager: TransferManager instance.

        Returns:
            Path: Final destination Path of the downloaded and verified file.

        Raises:
            ProtocolError: If a protocol violation or remote error occurs.
            ConnectionError: If network connection is severed.
            ValueError: If size or checksum validation fails.
            RuntimeError: If the transfer was cancelled.
        """
        download_dir = Path(self.config.download_dir).resolve()
        download_dir.mkdir(parents=True, exist_ok=True)

        sock: socket.socket | None = None
        temp_path: Path | None = None

        try:
            # 1. Update transfer status to CONNECTING
            transfer_manager.update_status(transfer_id, TransferStatus.CONNECTING)

            logger.info("Connecting to %s:%d for file_id=%s filename=%s", host, port, file_id, filename)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(float(self.config.socket_timeout))
            sock.connect((host, port))

            # 2. Send FILE_REQUEST
            send_file_request(sock, file_id, filename)

            # 3. Receive and validate FILE_RESPONSE
            resp = recv_file_response(sock)
            status = resp.get("status", "").lower()
            if status != "ok":
                err_msg = resp.get("error_message") or f"Server returned error status: {status}"
                raise ProtocolError(err_msg, code=ErrorCode.FILE_NOT_FOUND if "not found" in err_msg.lower() else ErrorCode.SERVER_ERROR)

            remote_filename = resp.get("filename") or filename
            remote_size = int(resp.get("file_size", expected_size))
            remote_checksum = resp.get("checksum") or expected_checksum

            if expected_size <= 0 and remote_size > 0:
                expected_size = remote_size
            if not expected_checksum and remote_checksum:
                expected_checksum = remote_checksum

            # 4. Prepare temporary file
            safe_filename = sanitize_filename(remote_filename)
            temp_filename = f"{safe_filename}.{transfer_id[:8]}.tmp"
            temp_path = download_dir / temp_filename

            hasher = hashlib.sha256()
            bytes_received = 0
            server_checksum = ""

            # 5. Receive chunks in loop
            transfer_manager.update_status(transfer_id, TransferStatus.DOWNLOADING)

            with open(temp_path, "wb") as f:
                while True:
                    if transfer_manager.is_cancelled(transfer_id):
                        logger.info("Transfer %s was cancelled by user", transfer_id)
                        try:
                            send_cancel(sock)
                        except Exception:
                            pass
                        raise RuntimeError(f"Transfer {transfer_id} cancelled by user")

                    msg_type, payload = recv_message(sock)

                    if msg_type == MessageType.FILE_DATA:
                        if not payload:
                            continue
                        f.write(payload)
                        hasher.update(payload)
                        bytes_received += len(payload)
                        transfer_manager.update_progress(transfer_id, bytes_received, expected_size)

                        if transfer_manager.is_cancelled(transfer_id):
                            logger.info("Transfer %s was cancelled by user after chunk", transfer_id)
                            try:
                                send_cancel(sock)
                            except Exception:
                                pass
                            raise RuntimeError(f"Transfer {transfer_id} cancelled by user")

                    elif msg_type == MessageType.TRANSFER_COMPLETE:
                        try:
                            complete_payload = json.loads(payload.decode("utf-8"))
                            server_checksum = complete_payload.get("checksum", "")
                        except Exception as e:
                            logger.warning("Failed to decode TRANSFER_COMPLETE payload: %s", e)
                        break

                    elif msg_type == MessageType.ERROR:
                        try:
                            err_payload = json.loads(payload.decode("utf-8"))
                            code = err_payload.get("code", ErrorCode.SERVER_ERROR)
                            msg = err_payload.get("message", "Error from peer server")
                        except Exception:
                            code = ErrorCode.SERVER_ERROR
                            msg = "Unknown error message from peer"
                        raise ProtocolError(msg, code=code)

                    elif msg_type == MessageType.CANCEL:
                        raise ProtocolError("Transfer cancelled by remote peer", code=ErrorCode.TRANSFER_CANCELLED)

                    else:
                        raise ProtocolError(
                            f"Unexpected message type during transfer: {msg_type.name}",
                            code=ErrorCode.INVALID_REQUEST,
                        )

            # 6. Verify checksum and size
            transfer_manager.update_status(transfer_id, TransferStatus.VERIFYING)
            local_checksum = hasher.hexdigest().lower()

            if expected_checksum and local_checksum != expected_checksum.lower():
                raise ValueError(
                    f"Checksum mismatch: expected {expected_checksum}, received {local_checksum}"
                )

            if server_checksum and local_checksum != server_checksum.lower():
                raise ValueError(
                    f"Checksum mismatch with server finish payload: expected {server_checksum}, received {local_checksum}"
                )

            if expected_size > 0 and bytes_received != expected_size:
                raise ValueError(
                    f"File size mismatch: expected {expected_size} bytes, received {bytes_received} bytes"
                )

            # 7. Atomic rename temp file to final destination
            final_path = download_dir / safe_filename
            if final_path.exists():
                stem = final_path.stem
                suffix = final_path.suffix
                counter = 1
                while True:
                    candidate = download_dir / f"{stem}_{counter}{suffix}"
                    if not candidate.exists():
                        final_path = candidate
                        break
                    counter += 1

            temp_path.replace(final_path)
            temp_path = None  # Prevent cleanup in finally block

            # 8. Mark completed
            transfer_manager.update_progress(transfer_id, bytes_received, bytes_received)
            transfer_manager.update_status(transfer_id, TransferStatus.COMPLETED)
            logger.info("Download completed successfully: %s (%d bytes)", final_path, bytes_received)

            return final_path

        except (socket.timeout, TimeoutError) as te:
            logger.warning("Socket timeout while downloading transfer %s: %s", transfer_id, te)
            transfer_manager.update_status(transfer_id, TransferStatus.FAILED, "Connection timed out")
            raise

        except (ConnectionRefusedError, ConnectionResetError, BrokenPipeError, ConnectionError) as ce:
            logger.warning("Connection error while downloading transfer %s: %s", transfer_id, ce)
            transfer_manager.update_status(transfer_id, TransferStatus.FAILED, f"Connection error: {ce}")
            raise

        except Exception as e:
            logger.error("Download failed for transfer %s: %s", transfer_id, e, exc_info=True)
            transfer_manager.update_status(transfer_id, TransferStatus.FAILED, str(e))
            raise

        finally:
            # Clean up temp file on failure
            if temp_path is not None and temp_path.exists():
                try:
                    temp_path.unlink()
                except OSError:
                    pass

            # Always close socket
            if sock is not None:
                try:
                    sock.close()
                except OSError:
                    pass
