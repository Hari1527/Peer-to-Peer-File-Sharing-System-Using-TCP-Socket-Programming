"""Database row models as dataclasses."""

from dataclasses import asdict, dataclass
import sqlite3
from typing import Any


@dataclass
class PeerRecord:
    """Represents a peer database row."""

    peer_id: str
    host: str
    tcp_port: int
    api_port: int
    status: str
    last_seen: str
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        """Convert record to dictionary."""
        return asdict(self)

    @classmethod
    def from_row(cls, row: sqlite3.Row | dict[str, Any]) -> "PeerRecord":
        """Construct record from a SQLite row or dictionary."""
        return cls(
            peer_id=row["peer_id"],
            host=row["host"],
            tcp_port=int(row["tcp_port"]),
            api_port=int(row["api_port"]),
            status=row["status"],
            last_seen=row["last_seen"],
            created_at=row["created_at"],
        )


@dataclass
class SharedFileRecord:
    """Represents a shared file database row."""

    id: int | None
    file_id: str
    filename: str
    size: int
    checksum: str
    peer_id: str
    shared_at: str

    def to_dict(self) -> dict[str, Any]:
        """Convert record to dictionary."""
        return asdict(self)

    @classmethod
    def from_row(cls, row: sqlite3.Row | dict[str, Any]) -> "SharedFileRecord":
        """Construct record from a SQLite row or dictionary."""
        return cls(
            id=row["id"] if "id" in row and row["id"] is not None else None,
            file_id=row["file_id"],
            filename=row["filename"],
            size=int(row["size"]),
            checksum=row["checksum"],
            peer_id=row["peer_id"],
            shared_at=row["shared_at"],
        )


@dataclass
class TransferRecord:
    """Represents a transfer history database row."""

    transfer_id: str
    file_id: str
    filename: str
    source_peer_id: str
    dest_peer_id: str
    direction: str
    status: str = "pending"
    bytes_transferred: int = 0
    total_bytes: int = 0
    started_at: str = ""
    completed_at: str | None = None
    error_message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert record to dictionary."""
        return asdict(self)

    @classmethod
    def from_row(cls, row: sqlite3.Row | dict[str, Any]) -> "TransferRecord":
        """Construct record from a SQLite row or dictionary."""
        return cls(
            transfer_id=row["transfer_id"],
            file_id=row["file_id"],
            filename=row["filename"],
            source_peer_id=row["source_peer_id"],
            dest_peer_id=row["dest_peer_id"],
            direction=row["direction"],
            status=row["status"],
            bytes_transferred=int(row["bytes_transferred"] or 0),
            total_bytes=int(row["total_bytes"] or 0),
            started_at=row["started_at"],
            completed_at=row["completed_at"],
            error_message=row["error_message"],
        )
