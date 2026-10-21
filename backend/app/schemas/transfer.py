"""Pydantic schemas and enums for file transfer monitoring."""

from enum import Enum
from pydantic import BaseModel, Field


class TransferStatus(str, Enum):
    """Lifecycle statuses for file transfers."""

    PENDING = "PENDING"
    CONNECTING = "CONNECTING"
    DOWNLOADING = "DOWNLOADING"
    VERIFYING = "VERIFYING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

    @classmethod
    def _missing_(cls, value: object):
        if isinstance(value, str):
            for member in cls:
                if member.value.lower() == value.lower():
                    return member
        return None


class TransferDirection(str, Enum):
    """Direction of the file transfer."""

    UPLOAD = "UPLOAD"
    DOWNLOAD = "DOWNLOAD"

    @classmethod
    def _missing_(cls, value: object):
        if isinstance(value, str):
            for member in cls:
                if member.value.lower() == value.lower():
                    return member
        return None


class DownloadRequest(BaseModel):
    """Payload to initiate a file download."""

    file_id: str
    peer_id: str
    filename: str


class TransferInfo(BaseModel):
    """Progress and metadata for a single transfer."""

    transfer_id: str
    file_id: str
    filename: str
    source_peer_id: str
    dest_peer_id: str
    direction: TransferDirection
    status: TransferStatus
    bytes_transferred: int = 0
    total_bytes: int = 0
    progress_percent: float = 0.0
    started_at: str
    completed_at: str | None = None
    error_message: str | None = None
    speed_bps: float = 0.0


class TransferListResponse(BaseModel):
    """Response containing a list of transfers."""

    transfers: list[TransferInfo]
    total: int


class CancelTransferResponse(BaseModel):
    """Response returned upon cancelling a transfer."""

    transfer_id: str
    status: TransferStatus
    message: str
