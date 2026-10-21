"""Database repositories for Peers, Shared Files, and Transfers."""

from datetime import datetime, timedelta, timezone
from typing import Any
from .database import TrackerDatabase
from .models import PeerRecord, SharedFileRecord, TransferRecord


class PeerRepository:
    """Repository managing peer registration and heartbeat persistence."""

    def __init__(self, db: TrackerDatabase) -> None:
        self.db = db

    def register(
        self, peer_id: str, host: str, tcp_port: int, api_port: int
    ) -> PeerRecord:
        """Register or update an active peer in the database."""
        now = datetime.now(timezone.utc).isoformat()
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO peers (peer_id, host, tcp_port, api_port, status, last_seen, created_at)
                VALUES (?, ?, ?, ?, 'online', ?, ?)
                ON CONFLICT(peer_id) DO UPDATE SET
                    host = excluded.host,
                    tcp_port = excluded.tcp_port,
                    api_port = excluded.api_port,
                    status = 'online',
                    last_seen = excluded.last_seen;
                """,
                (peer_id, host, tcp_port, api_port, now, now),
            )
            cursor.execute("SELECT * FROM peers WHERE peer_id = ?", (peer_id,))
            row = cursor.fetchone()
            return PeerRecord.from_row(row)

    def heartbeat(self, peer_id: str) -> bool:
        """Refresh a peer's last_seen timestamp and online status."""
        now = datetime.now(timezone.utc).isoformat()
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE peers SET last_seen = ?, status = 'online' WHERE peer_id = ?",
                (now, peer_id),
            )
            return cursor.rowcount > 0

    def get_all(self, status: str | None = None) -> list[PeerRecord]:
        """Fetch all peers, optionally filtered by status."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            if status:
                cursor.execute(
                    "SELECT * FROM peers WHERE status = ? ORDER BY last_seen DESC",
                    (status.lower(),),
                )
            else:
                cursor.execute("SELECT * FROM peers ORDER BY last_seen DESC")
            return [PeerRecord.from_row(r) for r in cursor.fetchall()]

    def get_by_id(self, peer_id: str) -> PeerRecord | None:
        """Fetch a peer by its unique identifier."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM peers WHERE peer_id = ?", (peer_id,))
            row = cursor.fetchone()
            return PeerRecord.from_row(row) if row else None

    def delete(self, peer_id: str) -> bool:
        """Remove a peer from the database."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM peers WHERE peer_id = ?", (peer_id,))
            return cursor.rowcount > 0

    def expire_stale(self, timeout_seconds: int) -> int:
        """Mark peers offline if they have not been seen within timeout_seconds."""
        cutoff = (
            datetime.now(timezone.utc) - timedelta(seconds=timeout_seconds)
        ).isoformat()
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE peers SET status = 'offline' WHERE status != 'offline' AND last_seen < ?",
                (cutoff,),
            )
            return cursor.rowcount

    def get_online_count(self) -> int:
        """Get the total count of currently online peers."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM peers WHERE status = 'online'")
            row = cursor.fetchone()
            return int(row[0]) if row else 0


class FileRepository:
    """Repository managing indexed shared files across peers."""

    def __init__(self, db: TrackerDatabase) -> None:
        self.db = db

    def add_files(
        self, peer_id: str, files: list[dict[str, Any]]
    ) -> list[SharedFileRecord]:
        """Batch insert or update shared files announced by a peer."""
        now = datetime.now(timezone.utc).isoformat()
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            for f in files:
                cursor.execute(
                    """
                    INSERT INTO shared_files (file_id, filename, size, checksum, peer_id, shared_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(file_id, peer_id) DO UPDATE SET
                        filename = excluded.filename,
                        size = excluded.size,
                        checksum = excluded.checksum,
                        shared_at = excluded.shared_at;
                    """,
                    (
                        f["file_id"],
                        f["filename"],
                        int(f["size"]),
                        f["checksum"],
                        peer_id,
                        now,
                    ),
                )
            cursor.execute(
                "SELECT * FROM shared_files WHERE peer_id = ? ORDER BY filename ASC",
                (peer_id,),
            )
            return [SharedFileRecord.from_row(r) for r in cursor.fetchall()]

    def get_all(self, limit: int = 100, offset: int = 0) -> list[SharedFileRecord]:
        """Fetch all shared files with pagination."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM shared_files ORDER BY shared_at DESC LIMIT ? OFFSET ?",
                (limit, offset),
            )
            return [SharedFileRecord.from_row(r) for r in cursor.fetchall()]

    def search(self, query: str) -> list[SharedFileRecord]:
        """Search shared files by partial filename match."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM shared_files WHERE filename LIKE ? ORDER BY filename ASC",
                (f"%{query}%",),
            )
            return [SharedFileRecord.from_row(r) for r in cursor.fetchall()]

    def get_peers_for_file(self, file_id: str) -> list[PeerRecord]:
        """Fetch all online peers sharing a specific file (by ID or checksum)."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT p.* FROM peers p
                JOIN shared_files sf ON p.peer_id = sf.peer_id
                WHERE (sf.file_id = ? OR sf.checksum = ?) AND p.status = 'online'
                ORDER BY p.last_seen DESC
                """,
                (file_id, file_id),
            )
            return [PeerRecord.from_row(r) for r in cursor.fetchall()]

    def get_file_metadata(self, file_id: str) -> SharedFileRecord | None:
        """Fetch file metadata by file_id or checksum."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM shared_files WHERE file_id = ? OR checksum = ? LIMIT 1",
                (file_id, file_id),
            )
            row = cursor.fetchone()
            return SharedFileRecord.from_row(row) if row else None

    def get_by_peer(self, peer_id: str) -> list[SharedFileRecord]:
        """Fetch all files shared by a given peer."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM shared_files WHERE peer_id = ? ORDER BY filename ASC",
                (peer_id,),
            )
            return [SharedFileRecord.from_row(r) for r in cursor.fetchall()]

    def remove_by_peer(self, peer_id: str) -> int:
        """Delete all shared files associated with a peer."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM shared_files WHERE peer_id = ?",
                (peer_id,),
            )
            return cursor.rowcount

    def get_file_count(self) -> int:
        """Get the count of unique files shared on the network."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(DISTINCT file_id) FROM shared_files")
            row = cursor.fetchone()
            return int(row[0]) if row else 0

    def get_total_records_count(self) -> int:
        """Get total count of shared file entries across all peers."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM shared_files")
            row = cursor.fetchone()
            return int(row[0]) if row else 0


class TransferRepository:
    """Repository managing transfer history and transfer metrics."""

    def __init__(self, db: TrackerDatabase) -> None:
        self.db = db

    def create(
        self,
        transfer_id: str,
        file_id: str,
        filename: str,
        source_peer_id: str,
        dest_peer_id: str,
        direction: str,
        status: str = "pending",
        total_bytes: int = 0,
        bytes_transferred: int = 0,
    ) -> TransferRecord:
        """Insert or update a transfer session record."""
        now = datetime.now(timezone.utc).isoformat()
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO transfers (
                    transfer_id, file_id, filename, source_peer_id, dest_peer_id,
                    direction, status, bytes_transferred, total_bytes, started_at, completed_at, error_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL)
                """,
                (
                    transfer_id,
                    file_id,
                    filename,
                    source_peer_id,
                    dest_peer_id,
                    direction,
                    status,
                    bytes_transferred,
                    total_bytes,
                    now,
                ),
            )
            cursor.execute("SELECT * FROM transfers WHERE transfer_id = ?", (transfer_id,))
            return TransferRecord.from_row(cursor.fetchone())

    def update_status(
        self,
        transfer_id: str,
        status: str,
        error_message: str | None = None,
    ) -> bool:
        """Update transfer status and set completed_at for terminal states."""
        now = datetime.now(timezone.utc).isoformat()
        is_terminal = str(status).lower() in ("completed", "failed", "cancelled")
        completed_at = now if is_terminal else None

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE transfers
                SET status = ?,
                    error_message = COALESCE(?, error_message),
                    completed_at = CASE WHEN ? IS NOT NULL THEN ? ELSE completed_at END
                WHERE transfer_id = ?
                """,
                (str(status), error_message, completed_at, completed_at, transfer_id),
            )
            return cursor.rowcount > 0

    def update_progress(self, transfer_id: str, bytes_transferred: int) -> bool:
        """Update bytes transferred for an ongoing transfer."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE transfers SET bytes_transferred = ? WHERE transfer_id = ?",
                (bytes_transferred, transfer_id),
            )
            return cursor.rowcount > 0

    def get_all(self, limit: int = 50, offset: int = 0) -> list[TransferRecord]:
        """Retrieve paginated transfer records ordered by started_at DESC."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM transfers ORDER BY started_at DESC LIMIT ? OFFSET ?",
                (limit, offset),
            )
            return [TransferRecord.from_row(r) for r in cursor.fetchall()]

    def get_total_count(self) -> int:
        """Get total count of transfers."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM transfers")
            row = cursor.fetchone()
            return int(row[0]) if row else 0

    def get_by_id(self, transfer_id: str) -> TransferRecord | None:
        """Fetch transfer record by its unique transfer ID."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM transfers WHERE transfer_id = ?", (transfer_id,))
            row = cursor.fetchone()
            return TransferRecord.from_row(row) if row else None

    def get_recent(self, limit: int = 20) -> list[TransferRecord]:
        """Fetch the most recent transfers ordered by started_at DESC."""
        return self.get_all(limit=limit, offset=0)

    def get_stats(self) -> dict[str, int]:
        """Calculate overall transfer statistics."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT
                    COUNT(*) AS total_transfers,
                    SUM(CASE WHEN LOWER(status) = 'completed' THEN 1 ELSE 0 END) AS completed_transfers,
                    SUM(CASE WHEN LOWER(status) = 'failed' THEN 1 ELSE 0 END) AS failed_transfers,
                    COALESCE(SUM(bytes_transferred), 0) AS total_bytes
                FROM transfers
                """
            )
            row = cursor.fetchone()
            return {
                "total_transfers": int(row["total_transfers"] or 0),
                "completed_transfers": int(row["completed_transfers"] or 0),
                "failed_transfers": int(row["failed_transfers"] or 0),
                "bytes_transferred": int(row["total_bytes"] or 0),
            }
