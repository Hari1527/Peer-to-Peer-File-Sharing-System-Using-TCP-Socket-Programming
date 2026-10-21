"""Central coordinator service for the Tracker node."""

import asyncio
from datetime import datetime, timedelta, timezone
import logging
import threading
from typing import Any

from ..api.websocket import tracker_event_manager
from ..config import TrackerConfig
from ..db.database import TrackerDatabase
from ..db.repositories import FileRepository, PeerRepository, TransferRepository
from ..schemas.file import (
    FileListResponse,
    FilePeersResponse,
    FileSearchResult,
    SharedFileInfo,
)
from ..schemas.peer import PeerInfo, PeerListResponse, PeerRegisterRequest, PeerHeartbeatRequest
from ..schemas.transfer import (
    TransferDirection,
    TransferInfo,
    TransferListResponse,
    TransferStatus,
)

logger = logging.getLogger("p2p.tracker_service")


class TrackerService:
    """Business logic coordinator for tracking peers, file metadata, and transfer states."""

    def __init__(self, db: TrackerDatabase, config: TrackerConfig) -> None:
        self.db = db
        self.config = config
        self.peer_repo = PeerRepository(db)
        self.file_repo = FileRepository(db)
        self.transfer_repo = TransferRepository(db)
        self._lock = threading.Lock()

    def _broadcast_event(self, event_type: str, data: dict[str, Any]) -> None:
        """Asynchronously dispatch real-time events to connected clients."""
        event = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(tracker_event_manager.broadcast(event))
        except RuntimeError:
            # Running outside an active event loop (e.g. sync tests or background thread)
            pass

    def register_peer(self, request: PeerRegisterRequest) -> PeerInfo:
        """Register a peer and index any initial files announced by it."""
        with self._lock:
            peer_record = self.peer_repo.register(
                peer_id=request.peer_id,
                host=request.host,
                tcp_port=request.tcp_port,
                api_port=request.api_port,
            )

            if request.shared_files:
                self.file_repo.add_files(request.peer_id, request.shared_files)

            peer_files = self.file_repo.get_by_peer(request.peer_id)
            peer_info = PeerInfo(
                peer_id=peer_record.peer_id,
                host=peer_record.host,
                tcp_port=peer_record.tcp_port,
                api_port=peer_record.api_port,
                status=peer_record.status,
                last_seen=peer_record.last_seen,
                file_count=len(peer_files),
            )

        self._broadcast_event("peer_registered", peer_info.model_dump())
        if request.shared_files:
            self._broadcast_event(
                "file_shared",
                {"peer_id": request.peer_id, "files": request.shared_files},
            )

        return peer_info

    def heartbeat(self, request: PeerHeartbeatRequest) -> PeerInfo:
        """Process peer heartbeat and optionally refresh its list of shared files."""
        with self._lock:
            existing = self.peer_repo.get_by_id(request.peer_id)
            if not existing:
                raise KeyError(f"Peer '{request.peer_id}' is not registered")

            self.peer_repo.heartbeat(request.peer_id)

            if request.shared_files is not None:
                self.file_repo.remove_by_peer(request.peer_id)
                if request.shared_files:
                    self.file_repo.add_files(request.peer_id, request.shared_files)

            updated = self.peer_repo.get_by_id(request.peer_id)
            peer_files = self.file_repo.get_by_peer(request.peer_id)
            peer_info = PeerInfo(
                peer_id=updated.peer_id,
                host=updated.host,
                tcp_port=updated.tcp_port,
                api_port=updated.api_port,
                status=updated.status,
                last_seen=updated.last_seen,
                file_count=len(peer_files),
            )

        self._broadcast_event("peer_heartbeat", peer_info.model_dump())
        return peer_info

    def get_peers(self, status: str | None = None) -> PeerListResponse:
        """Fetch all peers, filtered optionally by status (e.g. 'online', 'offline')."""
        records = self.peer_repo.get_all(status=status)
        peer_infos: list[PeerInfo] = []
        for r in records:
            file_count = len(self.file_repo.get_by_peer(r.peer_id))
            peer_infos.append(
                PeerInfo(
                    peer_id=r.peer_id,
                    host=r.host,
                    tcp_port=r.tcp_port,
                    api_port=r.api_port,
                    status=r.status,
                    last_seen=r.last_seen,
                    file_count=file_count,
                )
            )
        return PeerListResponse(peers=peer_infos, total=len(peer_infos))

    def remove_peer(self, peer_id: str) -> bool:
        """Unregister a peer and remove its shared files."""
        with self._lock:
            existing = self.peer_repo.get_by_id(peer_id)
            if not existing:
                return False

            self.file_repo.remove_by_peer(peer_id)
            deleted = self.peer_repo.delete(peer_id)

        self._broadcast_event("peer_offline", {"peer_id": peer_id, "reason": "unregistered"})
        return deleted

    def get_files(self, limit: int = 100, offset: int = 0) -> FileListResponse:
        """Fetch paginated shared files."""
        records = self.file_repo.get_all(limit=limit, offset=offset)
        total = self.file_repo.get_total_records_count()
        files = [
            SharedFileInfo(
                file_id=r.file_id,
                filename=r.filename,
                size=r.size,
                checksum=r.checksum,
                peer_id=r.peer_id,
                shared_at=r.shared_at,
            )
            for r in records
        ]
        return FileListResponse(files=files, total=total)

    def search_files(self, query: str) -> FileSearchResult:
        """Search files matching substring query."""
        records = self.file_repo.search(query=query)
        files = [
            SharedFileInfo(
                file_id=r.file_id,
                filename=r.filename,
                size=r.size,
                checksum=r.checksum,
                peer_id=r.peer_id,
                shared_at=r.shared_at,
            )
            for r in records
        ]
        return FileSearchResult(files=files, total=len(files), query=query)

    def get_file_peers(self, file_id: str) -> FilePeersResponse:
        """Locate online peers currently hosting a requested file."""
        file_meta = self.file_repo.get_file_metadata(file_id)
        if not file_meta:
            raise KeyError(f"File '{file_id}' not found")

        peer_records = self.file_repo.get_peers_for_file(file_id)
        peer_infos: list[PeerInfo] = []
        for p in peer_records:
            count = len(self.file_repo.get_by_peer(p.peer_id))
            peer_infos.append(
                PeerInfo(
                    peer_id=p.peer_id,
                    host=p.host,
                    tcp_port=p.tcp_port,
                    api_port=p.api_port,
                    status=p.status,
                    last_seen=p.last_seen,
                    file_count=count,
                )
            )

        return FilePeersResponse(
            file_id=file_meta.file_id,
            filename=file_meta.filename,
            size=file_meta.size,
            checksum=file_meta.checksum,
            peers=peer_infos,
        )

    def record_transfer(self, transfer_info: dict[str, Any]) -> None:
        """Record or update transfer progress and emit corresponding lifecycle events."""
        with self._lock:
            transfer_id = str(transfer_info.get("transfer_id", ""))
            if not transfer_id:
                raise ValueError("transfer_id is required")

            file_id = str(transfer_info.get("file_id", ""))
            filename = str(transfer_info.get("filename", ""))
            source_peer_id = str(transfer_info.get("source_peer_id", ""))
            dest_peer_id = str(transfer_info.get("dest_peer_id", ""))
            direction = str(transfer_info.get("direction", "DOWNLOAD")).upper()
            status_val = str(transfer_info.get("status", "PENDING")).upper()
            total_bytes = int(transfer_info.get("total_bytes", 0))
            bytes_transferred = int(transfer_info.get("bytes_transferred", 0))
            error_message = transfer_info.get("error_message")

            existing = self.transfer_repo.get_by_id(transfer_id)
            if not existing:
                self.transfer_repo.create(
                    transfer_id=transfer_id,
                    file_id=file_id,
                    filename=filename,
                    source_peer_id=source_peer_id,
                    dest_peer_id=dest_peer_id,
                    direction=direction,
                    status=status_val,
                    total_bytes=total_bytes,
                    bytes_transferred=bytes_transferred,
                )
            else:
                self.transfer_repo.update_progress(transfer_id, bytes_transferred)
                self.transfer_repo.update_status(transfer_id, status_val, error_message)

        # Broadcast real-time events depending on transfer state
        if status_val == "COMPLETED":
            self._broadcast_event("transfer_completed", transfer_info)
        elif status_val in ("FAILED", "CANCELLED"):
            self._broadcast_event("transfer_failed", transfer_info)
        elif status_val in ("DOWNLOADING", "VERIFYING"):
            self._broadcast_event("transfer_progress", transfer_info)
        else:
            self._broadcast_event("transfer_started", transfer_info)

    def get_transfers(self, limit: int = 50, offset: int = 0) -> TransferListResponse:
        """Fetch recent transfers with progress percentages."""
        records = self.transfer_repo.get_all(limit=limit, offset=offset)
        total = self.transfer_repo.get_total_count()

        transfers: list[TransferInfo] = []
        for r in records:
            pct = (
                round((r.bytes_transferred / r.total_bytes) * 100.0, 2)
                if r.total_bytes > 0
                else 0.0
            )
            transfers.append(
                TransferInfo(
                    transfer_id=r.transfer_id,
                    file_id=r.file_id,
                    filename=r.filename,
                    source_peer_id=r.source_peer_id,
                    dest_peer_id=r.dest_peer_id,
                    direction=TransferDirection(r.direction.upper()),
                    status=TransferStatus(r.status.upper()),
                    bytes_transferred=r.bytes_transferred,
                    total_bytes=r.total_bytes,
                    progress_percent=min(pct, 100.0),
                    started_at=r.started_at,
                    completed_at=r.completed_at,
                    error_message=r.error_message,
                    speed_bps=0.0,
                )
            )

        return TransferListResponse(transfers=transfers, total=total)

    def get_stats(self) -> dict[str, int]:
        """Aggregate high-level system metrics."""
        peers_online = self.peer_repo.get_online_count()
        total_files = self.file_repo.get_file_count()
        transfer_stats = self.transfer_repo.get_stats()

        return {
            "peers_online": peers_online,
            "total_files": total_files,
            "total_transfers": transfer_stats["total_transfers"],
            "bytes_transferred": transfer_stats["bytes_transferred"],
        }

    def expire_stale_peers(self) -> int:
        """Detect peers missing heartbeats, remove their files, and set them offline."""
        cutoff = (
            datetime.now(timezone.utc)
            - timedelta(seconds=self.config.peer_expiry_seconds)
        ).isoformat()

        with self._lock:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT peer_id FROM peers WHERE status = 'online' AND last_seen < ?",
                    (cutoff,),
                )
                expired_peer_ids = [row[0] for row in cursor.fetchall()]

            for pid in expired_peer_ids:
                self.file_repo.remove_by_peer(pid)
                self._broadcast_event(
                    "peer_offline",
                    {"peer_id": pid, "reason": "heartbeat_timeout"},
                )

            expired_count = self.peer_repo.expire_stale(self.config.peer_expiry_seconds)

        if expired_count > 0:
            logger.info("Expired %d stale peer(s)", expired_count)

        return expired_count
