"""FastAPI router for Peer control and management endpoints."""

from datetime import datetime, timezone
import logging
from pathlib import Path
import threading
from typing import Any

from fastapi import APIRouter, HTTPException, status

from app.config import PeerConfig
from app.core.file_index import FileIndex
from app.core.peer_registry import PeerRegistryClient
from app.core.tcp_client import TCPFileClient
from app.core.transfer_manager import TransferManager
from app.schemas.file import FileListResponse, ShareFilesRequest, ShareFilesResponse, SharedFileInfo
from app.schemas.transfer import (
    CancelTransferResponse,
    DownloadRequest,
    TransferDirection,
    TransferInfo,
    TransferListResponse,
    TransferStatus,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/peer", tags=["Peer Control"])

# Module-level dictionary holding runtime instances for the peer node
peer_state: dict[str, Any] = {
    "config": None,
    "file_index": None,
    "transfer_manager": None,
    "peer_registry_client": None,
    "tcp_client": None,
    "tcp_server": None,
}


def get_state() -> dict[str, Any]:
    """Retrieve and validate the peer node state dictionary."""
    if not peer_state.get("config"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Peer node is initializing or state unavailable",
        )
    return peer_state


@router.get("/status")
def get_peer_status() -> dict[str, Any]:
    """Retrieve runtime status of the local peer node."""
    state = get_state()
    config: PeerConfig = state["config"]
    file_index: FileIndex = state["file_index"]
    transfer_manager: TransferManager = state["transfer_manager"]

    files = file_index.get_all_files() if file_index else []
    all_transfers = transfer_manager.get_all_transfers() if transfer_manager else []

    active_statuses = {
        TransferStatus.PENDING,
        TransferStatus.CONNECTING,
        TransferStatus.DOWNLOADING,
        TransferStatus.VERIFYING,
    }
    active_transfers_count = sum(1 for t in all_transfers if t.status in active_statuses)

    return {
        "peer_id": config.peer_id,
        "host": config.host,
        "tcp_port": config.tcp_port,
        "api_port": config.api_port,
        "status": "online",
        "shared_dir": str(config.shared_dir),
        "download_dir": str(config.download_dir),
        "files_shared": len(files),
        "active_transfers": active_transfers_count,
    }


@router.get("/files", response_model=FileListResponse)
def list_shared_files() -> FileListResponse:
    """List all files currently indexed and shared by this peer."""
    state = get_state()
    config: PeerConfig = state["config"]
    file_index: FileIndex = state["file_index"]

    indexed = file_index.get_all_files() if file_index else []
    now_iso = datetime.now(timezone.utc).isoformat()

    file_items = [
        SharedFileInfo(
            file_id=item["file_id"],
            filename=item["filename"],
            size=item["size"],
            checksum=item["checksum"],
            peer_id=config.peer_id,
            shared_at=now_iso,
        )
        for item in indexed
    ]

    return FileListResponse(files=file_items, total=len(file_items))


@router.post("/share", response_model=ShareFilesResponse)
def share_files(req: ShareFilesRequest | None = None) -> ShareFilesResponse:
    """Rescan the shared directory and update registrations with the tracker."""
    state = get_state()
    config: PeerConfig = state["config"]
    file_index: FileIndex = state["file_index"]
    registry_client: PeerRegistryClient = state["peer_registry_client"]

    # Refresh local file index
    indexed = file_index.refresh() if file_index else []

    # Update tracker registration or heartbeat with updated file list
    if registry_client:
        try:
            registry_client.heartbeat(shared_files=indexed)
        except Exception as e:
            logger.warning("Failed to sync shared files with tracker: %s", e)

    now_iso = datetime.now(timezone.utc).isoformat()
    file_items = [
        SharedFileInfo(
            file_id=item["file_id"],
            filename=item["filename"],
            size=item["size"],
            checksum=item["checksum"],
            peer_id=config.peer_id,
            shared_at=now_iso,
        )
        for item in indexed
    ]

    return ShareFilesResponse(
        files=file_items,
        total=len(file_items),
        message=f"Successfully indexed {len(file_items)} shared files",
    )


@router.post("/download", response_model=TransferInfo)
def initiate_download(req: DownloadRequest) -> TransferInfo:
    """Initiate a peer-to-peer file download in a background thread."""
    state = get_state()
    config: PeerConfig = state["config"]
    transfer_manager: TransferManager = state["transfer_manager"]
    registry_client: PeerRegistryClient = state["peer_registry_client"]
    tcp_client: TCPFileClient = state["tcp_client"]

    logger.info("Received download request for file_id=%s from peer_id=%s", req.file_id, req.peer_id)

    # 1. Fetch peer metadata from tracker
    expected_size = 0
    expected_checksum = req.file_id
    target_host: str | None = None
    target_port: int | None = None

    if registry_client:
        try:
            peers_resp = registry_client.get_file_peers(req.file_id)
            if peers_resp:
                expected_size = int(peers_resp.get("size", 0))
                expected_checksum = peers_resp.get("checksum", req.file_id)
                peers = peers_resp.get("peers", [])
                for p in peers:
                    if p.get("peer_id") == req.peer_id:
                        target_host = p.get("host")
                        target_port = p.get("tcp_port")
                        break
                # If specific peer not found in peers list, fallback to any available peer
                if target_host is None and peers:
                    target_host = peers[0].get("host")
                    target_port = peers[0].get("tcp_port")
        except Exception as e:
            logger.warning("Could not fetch file peers from tracker: %s", e)

    if not target_host or not target_port:
        # Fallback to local default if tracker query did not return host/port
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Target peer {req.peer_id} hosting file {req.file_id} not reachable or not registered",
        )

    # 2. Create transfer record
    transfer = transfer_manager.create_transfer(
        file_id=req.file_id,
        filename=req.filename,
        source_peer_id=req.peer_id,
        dest_peer_id=config.peer_id,
        direction=TransferDirection.DOWNLOAD,
        total_bytes=expected_size,
    )

    # 3. Spawn background thread for downloading
    def _execute_download() -> None:
        try:
            downloaded_path = tcp_client.download_file(
                host=target_host,
                port=target_port,
                file_id=req.file_id,
                filename=req.filename,
                expected_checksum=expected_checksum,
                expected_size=expected_size,
                transfer_id=transfer.transfer_id,
                transfer_manager=transfer_manager,
            )
            logger.info("Successfully downloaded file to: %s", downloaded_path)

            # Report transfer completion to tracker
            if registry_client:
                updated_t = transfer_manager.get_transfer(transfer.transfer_id)
                if updated_t:
                    registry_client.report_transfer(updated_t.model_dump())

        except Exception as ex:
            logger.error("Download failed for transfer %s: %s", transfer.transfer_id, ex)
            if registry_client:
                updated_t = transfer_manager.get_transfer(transfer.transfer_id)
                if updated_t:
                    registry_client.report_transfer(updated_t.model_dump())

    thread = threading.Thread(
        target=_execute_download,
        name=f"DownloadWorker-{transfer.transfer_id[:8]}",
        daemon=True,
    )
    thread.start()

    return transfer


@router.get("/transfers", response_model=TransferListResponse)
def list_transfers() -> TransferListResponse:
    """Retrieve all current and historical transfers for this peer."""
    state = get_state()
    transfer_manager: TransferManager = state["transfer_manager"]
    transfers = transfer_manager.get_all_transfers() if transfer_manager else []
    return TransferListResponse(transfers=transfers, total=len(transfers))


@router.get("/transfers/{transfer_id}", response_model=TransferInfo)
def get_transfer_status(transfer_id: str) -> TransferInfo:
    """Retrieve detailed progress of a specific transfer."""
    state = get_state()
    transfer_manager: TransferManager = state["transfer_manager"]
    transfer = transfer_manager.get_transfer(transfer_id) if transfer_manager else None
    if not transfer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transfer with ID '{transfer_id}' not found",
        )
    return transfer


@router.post("/transfers/{transfer_id}/cancel", response_model=CancelTransferResponse)
def cancel_transfer(transfer_id: str) -> CancelTransferResponse:
    """Cancel an active file transfer."""
    state = get_state()
    transfer_manager: TransferManager = state["transfer_manager"]
    transfer = transfer_manager.cancel_transfer(transfer_id) if transfer_manager else None
    if not transfer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transfer with ID '{transfer_id}' not found",
        )
    return CancelTransferResponse(
        transfer_id=transfer.transfer_id,
        status=transfer.status,
        message="Transfer cancelled successfully",
    )


@router.post("/refresh", response_model=ShareFilesResponse)
def refresh_shared_files() -> ShareFilesResponse:
    """Rescan local shared folder and republish active inventory to tracker."""
    state = get_state()
    config: PeerConfig = state["config"]
    file_index: FileIndex = state["file_index"]
    registry_client: PeerRegistryClient = state["peer_registry_client"]

    indexed = file_index.refresh() if file_index else []

    if registry_client:
        try:
            registry_client.heartbeat(shared_files=indexed)
        except Exception as e:
            logger.warning("Heartbeat failed during refresh: %s", e)

    now_iso = datetime.now(timezone.utc).isoformat()
    file_items = [
        SharedFileInfo(
            file_id=item["file_id"],
            filename=item["filename"],
            size=item["size"],
            checksum=item["checksum"],
            peer_id=config.peer_id,
            shared_at=now_iso,
        )
        for item in indexed
    ]

    return ShareFilesResponse(
        files=file_items,
        total=len(file_items),
        message="Local index refreshed and published to tracker",
    )


@router.delete("/files/{file_id}")
def remove_shared_file(file_id: str) -> dict[str, str]:
    """Remove a file from the shared directory and update tracker index."""
    state = get_state()
    file_index: FileIndex = state["file_index"]
    registry_client: PeerRegistryClient = state["peer_registry_client"]

    if not file_index or not file_index.has_file(file_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File with ID '{file_id}' not found in shared inventory",
        )

    file_path = file_index.get_file_path(file_id)
    if file_path and file_path.exists():
        try:
            file_path.unlink()
            logger.info("Deleted shared file from disk: %s", file_path)
        except OSError as e:
            logger.error("Failed to delete file from disk: %s", e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Could not delete file from disk: {e}",
            )

    # Refresh file index
    indexed = file_index.refresh()

    # Update tracker
    if registry_client:
        try:
            registry_client.heartbeat(shared_files=indexed)
        except Exception as e:
            logger.warning("Failed to notify tracker of removed file: %s", e)

    return {"message": "File removed from sharing", "file_id": file_id}
