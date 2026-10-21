"""Transfer manager module for tracking active and historical file transfers."""

import asyncio
from datetime import datetime, timezone
import logging
import threading
import time
from typing import Any
import uuid

from app.schemas.transfer import TransferDirection, TransferInfo, TransferStatus

logger = logging.getLogger(__name__)


class TransferManager:
    """Thread-safe manager for tracking peer file uploads and downloads."""

    def __init__(self, peer_id: str) -> None:
        """Initialize the transfer manager.

        Args:
            peer_id: The identifier of the local peer.
        """
        self.peer_id = peer_id
        self._transfers: dict[str, TransferInfo] = {}
        self._lock = threading.Lock()
        self._cancelled: set[str] = set()
        self._last_progress_broadcast: dict[str, float] = {}
        self._loop: asyncio.AbstractEventLoop | None = None

    def set_event_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        """Set the asyncio event loop for thread-safe event broadcasts.

        Args:
            loop: Active asyncio event loop.
        """
        self._loop = loop

    def _broadcast(self, event: dict[str, Any]) -> None:
        """Fire-and-forget broadcast of transfer events to WebSocket clients."""
        try:
            from app.api.websocket import peer_event_manager
        except ImportError:
            return

        if peer_event_manager is None:
            return

        try:
            # 1. If explicit event loop was provided and is running:
            if self._loop is not None and self._loop.is_running():
                asyncio.run_coroutine_threadsafe(peer_event_manager.broadcast(event), self._loop)
                return

            # 2. Check if the current thread has a running loop:
            try:
                curr_loop = asyncio.get_running_loop()
                if curr_loop.is_running():
                    curr_loop.create_task(peer_event_manager.broadcast(event))
                    return
            except RuntimeError:
                pass

        except Exception as e:
            logger.debug("Failed to dispatch WebSocket event: %s", e)

    def _calculate_speed(self, transfer: TransferInfo) -> float:
        """Calculate transfer speed in bytes per second.

        Args:
            transfer: TransferInfo record.

        Returns:
            float: Speed in bytes per second.
        """
        try:
            started = datetime.fromisoformat(transfer.started_at)
            now = datetime.now(timezone.utc)
            if started.tzinfo is None:
                started = started.replace(tzinfo=timezone.utc)
            elapsed = (now - started).total_seconds()
            if elapsed > 0.05 and transfer.bytes_transferred > 0:
                return round(transfer.bytes_transferred / elapsed, 2)
        except Exception:
            pass
        return 0.0

    def create_transfer(
        self,
        file_id: str,
        filename: str,
        source_peer_id: str,
        dest_peer_id: str,
        direction: TransferDirection | str,
        total_bytes: int = 0,
    ) -> TransferInfo:
        """Create a new file transfer record.

        Args:
            file_id: SHA-256 identifier of the file.
            filename: Name of the file being transferred.
            source_peer_id: Peer ID of the sender/uploader.
            dest_peer_id: Peer ID of the receiver/downloader.
            direction: TransferDirection.UPLOAD or TransferDirection.DOWNLOAD.
            total_bytes: Expected total size of file in bytes.

        Returns:
            TransferInfo: Newly created transfer object.
        """
        transfer_id = str(uuid.uuid4())
        now_iso = datetime.now(timezone.utc).isoformat()

        if isinstance(direction, str):
            direction = TransferDirection(direction)

        transfer = TransferInfo(
            transfer_id=transfer_id,
            file_id=file_id,
            filename=filename,
            source_peer_id=source_peer_id,
            dest_peer_id=dest_peer_id,
            direction=direction,
            status=TransferStatus.PENDING,
            bytes_transferred=0,
            total_bytes=total_bytes,
            progress_percent=0.0,
            started_at=now_iso,
            completed_at=None,
            error_message=None,
            speed_bps=0.0,
        )

        with self._lock:
            self._transfers[transfer_id] = transfer
            result = transfer.model_copy()

        logger.info(
            "Created transfer %s: file=%s direction=%s size=%d",
            transfer_id,
            filename,
            direction.value,
            total_bytes,
        )

        self._broadcast({
            "event_type": "transfer_created",
            "data": result.model_dump(),
        })

        return result

    def update_status(
        self,
        transfer_id: str,
        status: TransferStatus | str,
        error_message: str | None = None,
    ) -> TransferInfo | None:
        """Update the status of an existing transfer.

        Args:
            transfer_id: UUID of the transfer.
            status: New TransferStatus enum value or string.
            error_message: Optional error message string.

        Returns:
            TransferInfo | None: Updated transfer info, or None if not found.
        """
        if isinstance(status, str):
            status = TransferStatus(status)

        with self._lock:
            transfer = self._transfers.get(transfer_id)
            if not transfer:
                logger.warning("Attempted to update status of unknown transfer: %s", transfer_id)
                return None

            transfer.status = status
            if error_message is not None:
                transfer.error_message = error_message

            if status in (TransferStatus.COMPLETED, TransferStatus.FAILED, TransferStatus.CANCELLED):
                transfer.completed_at = datetime.now(timezone.utc).isoformat()
                if status == TransferStatus.CANCELLED:
                    self._cancelled.add(transfer_id)
                if status == TransferStatus.COMPLETED and transfer.total_bytes > 0:
                    transfer.bytes_transferred = transfer.total_bytes
                    transfer.progress_percent = 100.0

            result = transfer.model_copy()

        logger.info("Transfer %s status updated to %s", transfer_id, status.value)

        self._broadcast({
            "event_type": "transfer_status",
            "data": result.model_dump(),
        })

        return result

    def update_progress(
        self,
        transfer_id: str,
        bytes_transferred: int,
        total_bytes: int = 0,
    ) -> TransferInfo | None:
        """Update progress metrics for an ongoing transfer.

        Args:
            transfer_id: UUID of the transfer.
            bytes_transferred: Number of bytes transferred so far.
            total_bytes: Total file size in bytes (if known).

        Returns:
            TransferInfo | None: Updated transfer info, or None if not found.
        """
        with self._lock:
            transfer = self._transfers.get(transfer_id)
            if not transfer:
                return None

            transfer.bytes_transferred = bytes_transferred
            if total_bytes > 0:
                transfer.total_bytes = total_bytes

            if transfer.total_bytes > 0:
                transfer.progress_percent = round(
                    min(100.0, (bytes_transferred / transfer.total_bytes) * 100), 2
                )
            else:
                transfer.progress_percent = 0.0

            transfer.speed_bps = self._calculate_speed(transfer)
            result = transfer.model_copy()

        # Throttle progress event broadcasts (max 10 updates per second per transfer)
        now = time.time()
        last_broadcast = self._last_progress_broadcast.get(transfer_id, 0.0)
        if (now - last_broadcast > 0.1) or (result.progress_percent >= 100.0):
            self._last_progress_broadcast[transfer_id] = now
            self._broadcast({
                "event_type": "transfer_progress",
                "data": result.model_dump(),
            })

        return result

    def get_transfer(self, transfer_id: str) -> TransferInfo | None:
        """Retrieve transfer info by transfer_id.

        Args:
            transfer_id: UUID of the transfer.

        Returns:
            TransferInfo | None: Copy of the transfer info or None.
        """
        with self._lock:
            transfer = self._transfers.get(transfer_id)
            return transfer.model_copy() if transfer else None

    def get_all_transfers(self) -> list[TransferInfo]:
        """Retrieve all transfer records.

        Returns:
            list[TransferInfo]: List of all transfers sorted by started_at descending.
        """
        with self._lock:
            transfers = [t.model_copy() for t in self._transfers.values()]
        transfers.sort(key=lambda t: t.started_at, reverse=True)
        return transfers

    def cancel_transfer(self, transfer_id: str) -> TransferInfo | None:
        """Cancel an ongoing transfer.

        Args:
            transfer_id: UUID of the transfer to cancel.

        Returns:
            TransferInfo | None: Updated transfer info, or None if not found.
        """
        with self._lock:
            if transfer_id not in self._transfers:
                return None
            self._cancelled.add(transfer_id)

        return self.update_status(
            transfer_id,
            TransferStatus.CANCELLED,
            error_message="Transfer cancelled by user",
        )

    def is_cancelled(self, transfer_id: str) -> bool:
        """Check if a transfer has been marked as cancelled.

        Args:
            transfer_id: UUID of the transfer.

        Returns:
            bool: True if transfer was cancelled, False otherwise.
        """
        with self._lock:
            return transfer_id in self._cancelled
