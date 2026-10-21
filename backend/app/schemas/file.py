"""Pydantic schemas for file indexing, sharing, and lookup."""

from pydantic import BaseModel, Field, field_validator
from .peer import PeerInfo


class SharedFileInfo(BaseModel):
    """Information about a file shared on the P2P network."""

    file_id: str
    filename: str
    size: int
    checksum: str
    peer_id: str
    shared_at: str


class FileListResponse(BaseModel):
    """List of shared files available in the network."""

    files: list[SharedFileInfo]
    total: int


class FileSearchResult(BaseModel):
    """Search results for file queries."""

    files: list[SharedFileInfo]
    total: int
    query: str


class FilePeersResponse(BaseModel):
    """Peers holding a specific file."""

    file_id: str
    filename: str
    size: int
    checksum: str
    peers: list[PeerInfo]


class ShareFilesRequest(BaseModel):
    """Request to share files from a specific directory."""

    directory: str | None = None

    @field_validator("directory")
    @classmethod
    def validate_directory(cls, v: str | None) -> str | None:
        if v is not None:
            if ".." in v or v.startswith("/"):
                raise ValueError("Directory path cannot contain '..' or start with '/'")
        return v


class ShareFilesResponse(BaseModel):
    """Response after sharing files."""

    files: list[SharedFileInfo]
    total: int
    message: str
