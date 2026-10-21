"""Pydantic schemas for Peer registration and status."""

from typing import Any
from pydantic import BaseModel, Field


class PeerRegisterRequest(BaseModel):
    """Payload for registering a peer with the tracker."""

    peer_id: str
    host: str
    tcp_port: int = Field(..., gt=0, lt=65536)
    api_port: int = Field(..., gt=0, lt=65536)
    shared_files: list[dict[str, Any]] = Field(default_factory=list)


class PeerHeartbeatRequest(BaseModel):
    """Payload for sending peer heartbeat to the tracker."""

    peer_id: str
    shared_files: list[dict[str, Any]] | None = None


class PeerInfo(BaseModel):
    """Detailed information about an active or registered peer."""

    peer_id: str
    host: str
    tcp_port: int
    api_port: int
    status: str = "online"
    last_seen: str
    file_count: int = 0


class PeerListResponse(BaseModel):
    """Response containing a list of registered peers."""

    peers: list[PeerInfo]
    total: int
