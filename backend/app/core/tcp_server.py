"""TCP File Server module for peer-to-peer file serving.

Accepts incoming TCP connections from other peers, handles file requests,
streams binary file data in chunks, and tracks upload progress.
"""

import logging
from pathlib import Path
import select
import socket
import threading
from typing import TYPE_CHECKING, Any

from app.config import PeerConfig
from app.core.security import validate_file_id, validate_file_path
from app.core.tcp_protocol import (
    DEFAULT_CHUNK_SIZE,
    ErrorCode,
    MessageType,
    ProtocolError,
    recv_file_request,
    recv_message,
    send_cancel,
    send_error,
    send_file_data,
    send_file_response,
    send_transfer_complete,
)
from app.schemas.transfer import TransferDirection, TransferStatus
from app.utils.hashing import compute_file_sha256

if TYPE_CHECKING:
    from app.core.file_index import FileIndex
    from app.core.transfer_manager import TransferManager

logger = logging.getLogger(__name__)


class TCPFileServer:
    """Multi-threaded TCP server for handling peer file transfer requests."""

    def __init__(
        self,
        config: PeerConfig,
        file_index: Any,
        transfer_manager: Any,
    ) -> None:
        """Initialize TCP File Server.

        Args:
            config: Peer configuration object.
            file_index: Local FileIndex instance for file resolution.
            transfer_manager: TransferManager instance for tracking transfer states.
        """
        self.config = config
        self.file_index = file_index
        self.transfer_manager = transfer_manager

        self._server_socket: socket.socket | None = None
        self._running = threading.Event()
        self._thread: threading.Thread | None = None
        self._active_connections: list[socket.socket] = []
        self._connections_lock = threading.Lock()
        self._bound_port: int = config.tcp_port

    @property
    def is_running(self) -> bool:
        """Return True if the server accept loop is running."""
        return self._running.is_set()

    @property
    def address(self) -> tuple[str, int]:
        """Return the host and bound TCP port."""
        if self._server_socket:
            try:
                return self._server_socket.getsockname()
            except OSError:
                pass
        return self.config.host, self._bound_port

    def start(self) -> None:
        """Bind, listen, and start the accept loop in a background thread."""
        if self._running.is_set():
            logger.warning("TCPFileServer is already running on %s:%d", *self.address)
            return

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((self.config.host, self.config.tcp_port))
        sock.listen(128)
        # 1-second timeout on accept to periodically evaluate running event
        sock.settimeout(1.0)

        self._server_socket = sock
        self._bound_port = sock.getsockname()[1]
        self._running.set()

        self._thread = threading.Thread(
            target=self._accept_loop,
            name=f"TCPFileServer-{self._bound_port}",
            daemon=True,
        )
        self._thread.start()
        logger.info("TCPFileServer started and listening on %s:%d", self.config.host, self._bound_port)

    def stop(self) -> None:
        """Stop accept loop and terminate all active client sockets."""
        if not self._running.is_set():
            return

        logger.info("Stopping TCPFileServer on %s:%d...", *self.address)
        self._running.clear()

        # Close server socket to interrupt any pending accept
        if self._server_socket:
            try:
                self._server_socket.close()
            except OSError:
                pass
            self._server_socket = None

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3.0)
            self._thread = None

        # Close all active client connections
        with self._connections_lock:
            for client_sock in list(self._active_connections):
                try:
                    client_sock.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
                try:
                    client_sock.close()
                except OSError:
                    pass
            self._active_connections.clear()

        logger.info("TCPFileServer stopped")

    def _accept_loop(self) -> None:
        """Background loop accepting incoming TCP client connections."""
        while self._running.is_set():
            try:
                if not self._server_socket:
                    break
                client_sock, client_addr = self._server_socket.accept()
            except socket.timeout:
                continue
            except OSError:
                # Socket was closed during stop()
                break

            with self._connections_lock:
                if len(self._active_connections) >= self.config.max_connections:
                    logger.warning(
                        "Rejecting connection from %s:%d: max connections limit (%d) reached",
                        client_addr[0],
                        client_addr[1],
                        self.config.max_connections,
                    )
                    try:
                        send_error(client_sock, ErrorCode.SERVER_ERROR, "Max connections reached")
                    except Exception:
                        pass
                    try:
                        client_sock.close()
                    except OSError:
                        pass
                    continue

                self._active_connections.append(client_sock)

            handler_thread = threading.Thread(
                target=self._handle_client,
                args=(client_sock, client_addr),
                name=f"TCPClientHandler-{client_addr[0]}:{client_addr[1]}",
                daemon=True,
            )
            handler_thread.start()

    def _handle_client(self, client_sock: socket.socket, client_addr: tuple[str, int]) -> None:
        """Handle communication with a connected peer."""
        transfer_id: str | None = None
        client_sock.settimeout(float(self.config.socket_timeout))
        client_desc = f"{client_addr[0]}:{client_addr[1]}"

        try:
            # 1. Receive FILE_REQUEST
            request_data = recv_file_request(client_sock)
            file_id = request_data.get("file_id", "").strip()
            req_filename = request_data.get("filename", "").strip()

            logger.info("Received FILE_REQUEST from %s for file_id=%s filename=%s", client_desc, file_id, req_filename)

            # 2. Validate file_id
            if not validate_file_id(file_id):
                send_error(client_sock, ErrorCode.INVALID_REQUEST, "Invalid file ID format")
                return

            # 3. Lookup file in file_index
            filepath: Path | None = None
            if hasattr(self.file_index, "get_file_path"):
                filepath = self.file_index.get_file_path(file_id)

            if filepath is None or not filepath.exists() or not filepath.is_file():
                logger.warning("File not found for file_id=%s", file_id)
                send_error(client_sock, ErrorCode.FILE_NOT_FOUND, f"File {file_id} not found")
                return

            # 4. Security validation against allowed shared directory
            shared_dir = Path(self.config.shared_dir).resolve()
            if not validate_file_path(filepath, shared_dir):
                logger.warning("Security violation: path traversal detected for file %s", filepath)
                send_error(client_sock, ErrorCode.INVALID_REQUEST, "File path security violation")
                return

            # 5. File size and checksum
            file_size = filepath.stat().st_size
            if file_size > self.config.max_file_size:
                send_error(
                    client_sock,
                    ErrorCode.INVALID_REQUEST,
                    f"File exceeds maximum allowed size ({self.config.max_file_size} bytes)",
                )
                return

            checksum = compute_file_sha256(filepath)
            actual_filename = filepath.name

            # 6. Send FILE_RESPONSE
            send_file_response(
                client_sock,
                status="ok",
                filename=actual_filename,
                file_size=file_size,
                checksum=checksum,
            )

            # 7. Create transfer record
            transfer = self.transfer_manager.create_transfer(
                file_id=file_id,
                filename=actual_filename,
                source_peer_id=self.config.peer_id,
                dest_peer_id=client_desc,
                direction=TransferDirection.UPLOAD,
                total_bytes=file_size,
            )
            transfer_id = transfer.transfer_id
            self.transfer_manager.update_status(transfer_id, TransferStatus.DOWNLOADING)

            # 8. Stream file chunks
            bytes_sent = 0
            chunk_size = self.config.chunk_size or DEFAULT_CHUNK_SIZE

            with open(filepath, "rb") as f:
                while bytes_sent < file_size:
                    # Check if cancelled locally
                    if self.transfer_manager.is_cancelled(transfer_id):
                        logger.info("Transfer %s cancelled locally during upload", transfer_id)
                        try:
                            send_cancel(client_sock)
                        except Exception:
                            pass
                        return

                    # Check if client sent CANCEL or disconnected
                    readable, _, _ = select.select([client_sock], [], [], 0)
                    if readable:
                        try:
                            msg_type, _ = recv_message(client_sock)
                            if msg_type == MessageType.CANCEL:
                                logger.info("Peer %s cancelled transfer %s", client_desc, transfer_id)
                                self.transfer_manager.cancel_transfer(transfer_id)
                                return
                        except (ConnectionError, socket.timeout):
                            logger.warning("Peer %s disconnected prematurely during transfer %s", client_desc, transfer_id)
                            self.transfer_manager.update_status(
                                transfer_id,
                                TransferStatus.FAILED,
                                "Client disconnected prematurely",
                            )
                            return

                    chunk = f.read(chunk_size)
                    if not chunk:
                        break

                    send_file_data(client_sock, chunk)
                    bytes_sent += len(chunk)
                    self.transfer_manager.update_progress(transfer_id, bytes_sent, file_size)

            # 9. Send TRANSFER_COMPLETE
            send_transfer_complete(client_sock, checksum)
            self.transfer_manager.update_status(transfer_id, TransferStatus.COMPLETED)
            logger.info("Upload completed for transfer %s (%d bytes)", transfer_id, bytes_sent)

        except ProtocolError as pe:
            logger.warning("Protocol error with client %s: %s", client_desc, pe)
            if transfer_id:
                self.transfer_manager.update_status(transfer_id, TransferStatus.FAILED, str(pe))
            try:
                send_error(client_sock, pe.code, pe.message)
            except Exception:
                pass

        except (ConnectionError, BrokenPipeError, ConnectionResetError) as ce:
            logger.warning("Client connection reset with %s: %s", client_desc, ce)
            if transfer_id:
                self.transfer_manager.update_status(
                    transfer_id, TransferStatus.FAILED, "Client disconnected"
                )

        except socket.timeout:
            logger.warning("Client socket timed out with %s", client_desc)
            if transfer_id:
                self.transfer_manager.update_status(
                    transfer_id, TransferStatus.FAILED, "Transfer timed out"
                )

        except Exception as e:
            logger.exception("Unexpected error serving client %s: %s", client_desc, e)
            if transfer_id:
                self.transfer_manager.update_status(transfer_id, TransferStatus.FAILED, str(e))
            try:
                send_error(client_sock, ErrorCode.SERVER_ERROR, f"Server error: {e}")
            except Exception:
                pass

        finally:
            with self._connections_lock:
                if client_sock in self._active_connections:
                    self._active_connections.remove(client_sock)
            try:
                client_sock.close()
            except OSError:
                pass
