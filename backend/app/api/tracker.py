"""FastAPI route handlers for Tracker endpoints."""

from datetime import datetime, timezone
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from ..core.tracker_service import TrackerService
from ..schemas.file import (
    FileListResponse,
    FilePeersResponse,
    FileSearchResult,
)
from ..schemas.peer import (
    PeerHeartbeatRequest,
    PeerInfo,
    PeerListResponse,
    PeerRegisterRequest,
)
from ..schemas.transfer import TransferListResponse

router = APIRouter(prefix="/api", tags=["tracker"])


def get_tracker_service(request: Request) -> TrackerService:
    """Dependency provider for retrieving the TrackerService from app.state."""
    service: TrackerService | None = getattr(request.app.state, "tracker_service", None)
    if service is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="TrackerService not initialized",
        )
    return service


@router.get("/health")
def get_health() -> dict[str, str]:
    """Tracker health and liveness check."""
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0",
    }


@router.get("/peers", response_model=PeerListResponse)
def get_peers(
    status: str | None = Query(default=None),
    service: TrackerService = Depends(get_tracker_service),
) -> PeerListResponse:
    """Retrieve list of registered peers, optionally filtered by status."""
    return service.get_peers(status=status)


@router.post("/peers/register", response_model=PeerInfo)
def register_peer(
    request: PeerRegisterRequest,
    service: TrackerService = Depends(get_tracker_service),
) -> PeerInfo:
    """Register a new peer and announce its shared files."""
    try:
        return service.register_peer(request)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/peers/heartbeat", response_model=PeerInfo)
def heartbeat(
    request: PeerHeartbeatRequest,
    service: TrackerService = Depends(get_tracker_service),
) -> PeerInfo:
    """Refresh peer heartbeat and keep peer active."""
    try:
        return service.heartbeat(request)
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e).strip("'\""),
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/peers/{peer_id}")
def remove_peer(
    peer_id: str,
    service: TrackerService = Depends(get_tracker_service),
) -> dict[str, str]:
    """Unregister and remove peer from tracker."""
    removed = service.remove_peer(peer_id)
    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Peer '{peer_id}' not found",
        )
    return {"message": "Peer removed", "peer_id": peer_id}


@router.get("/files", response_model=FileListResponse)
def get_files(
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    service: TrackerService = Depends(get_tracker_service),
) -> FileListResponse:
    """Retrieve paginated shared files."""
    return service.get_files(limit=limit, offset=offset)


@router.get("/files/search", response_model=FileSearchResult)
def search_files(
    q: str = Query(..., min_length=1),
    service: TrackerService = Depends(get_tracker_service),
) -> FileSearchResult:
    """Search for shared files by filename substring."""
    return service.search_files(query=q)


@router.get("/files/{file_id}/peers", response_model=FilePeersResponse)
def get_file_peers(
    file_id: str,
    service: TrackerService = Depends(get_tracker_service),
) -> FilePeersResponse:
    """Find online peers sharing the requested file."""
    try:
        return service.get_file_peers(file_id=file_id)
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e).strip("'\""),
        )


@router.get("/transfers", response_model=TransferListResponse)
def get_transfers(
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    service: TrackerService = Depends(get_tracker_service),
) -> TransferListResponse:
    """List recent file transfers."""
    return service.get_transfers(limit=limit, offset=offset)


@router.get("/stats")
def get_stats(
    service: TrackerService = Depends(get_tracker_service),
) -> dict[str, int]:
    """Get tracker statistics (peers online, total files, transfers, bytes)."""
    return service.get_stats()


@router.post("/transfers/report")
def report_transfer(
    transfer_info: dict[str, Any],
    service: TrackerService = Depends(get_tracker_service),
) -> dict[str, str]:
    """Report file transfer status or progress from peers."""
    try:
        service.record_transfer(transfer_info)
        return {"status": "recorded"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
