"""Main entrypoint for running a P2P File Sharing Peer Node.

Initializes the FastAPI application, background TCP file transfer server,
local file indexer, peer registry client, and WebSocket event channels.
"""

import argparse
import asyncio
from contextlib import asynccontextmanager
import logging
from pathlib import Path
from typing import AsyncGenerator
import uuid
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.peer import peer_state, router as peer_router
from app.api.websocket import peer_websocket_endpoint
from app.config import PeerConfig
from app.core.file_index import FileIndex
from app.core.peer_registry import PeerRegistryClient
from app.core.tcp_client import TCPFileClient
from app.core.tcp_server import TCPFileServer
from app.core.transfer_manager import TransferManager
from app.utils.logging_config import setup_logging

logger = logging.getLogger("p2p.peer")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """FastAPI lifespan managing the initialization and shutdown of peer services."""
    config: PeerConfig = getattr(app.state, "config", None) or PeerConfig()

    logger.info(
        "Starting Peer Node [id=%s] on TCP port %d, API port %d...",
        config.peer_id,
        config.tcp_port,
        config.api_port,
    )

    # 1. Ensure required directories exist
    shared_path = Path(config.shared_dir).resolve()
    download_path = Path(config.download_dir).resolve()
    shared_path.mkdir(parents=True, exist_ok=True)
    download_path.mkdir(parents=True, exist_ok=True)

    # 2. Initialize file index and scan shared directory
    file_index = FileIndex(shared_dir=shared_path, max_file_size=config.max_file_size)

    # 3. Initialize transfer manager and bind to active event loop for WebSockets
    transfer_manager = TransferManager(peer_id=config.peer_id)
    try:
        transfer_manager.set_event_loop(asyncio.get_running_loop())
    except RuntimeError:
        pass

    # 4. Initialize peer registry client
    peer_registry_client = PeerRegistryClient(
        tracker_url=config.tracker_url,
        peer_id=config.peer_id,
        host=config.host,
        tcp_port=config.tcp_port,
        api_port=config.api_port,
    )

    # 5. Initialize and start TCP server for inbound file transfers
    tcp_server = TCPFileServer(
        config=config,
        file_index=file_index,
        transfer_manager=transfer_manager,
    )
    tcp_server.start()

    # 6. Initialize TCP client for outbound file downloads
    tcp_client = TCPFileClient(config=config)

    # 7. Store instances in the shared peer_state dictionary for API routes
    peer_state.update({
        "config": config,
        "file_index": file_index,
        "transfer_manager": transfer_manager,
        "peer_registry_client": peer_registry_client,
        "tcp_client": tcp_client,
        "tcp_server": tcp_server,
    })

    # 8. Register peer with tracker and start recurring heartbeat
    try:
        shared_files = file_index.get_all_files()
        reg_response = peer_registry_client.register(shared_files=shared_files)
        if not reg_response:
            logger.warning(
                "Tracker at %s is currently unreachable. Peer will continue running and retry via heartbeat.",
                config.tracker_url,
            )
        peer_registry_client.start_heartbeat(interval=25.0)
    except Exception as e:
        logger.warning("Initial tracker registration encountered an error: %s. Peer will continue running.", e)

    logger.info("Peer node initialization complete. Ready to serve requests.")

    yield

    # ================= SHUTDOWN =================
    logger.info("Shutting down Peer Node [%s]...", config.peer_id)

    try:
        peer_registry_client.stop_heartbeat()
    except Exception as e:
        logger.debug("Error while stopping heartbeat: %s", e)

    try:
        peer_registry_client.unregister()
    except Exception as e:
        logger.debug("Error unregistering from tracker: %s", e)

    try:
        tcp_server.stop()
    except Exception as e:
        logger.debug("Error stopping TCP server: %s", e)

    logger.info("Peer Node [%s] shutdown cleanly.", config.peer_id)


def create_peer_app(config: PeerConfig | None = None) -> FastAPI:
    """Factory function to build and configure the Peer FastAPI application.

    Args:
        config: Optional PeerConfig instance.

    Returns:
        FastAPI: Configured application instance.
    """
    app = FastAPI(
        title="P2P File Sharing Peer Node",
        description="Peer control REST API and real-time event dispatcher",
        version="1.0.0",
        lifespan=lifespan,
    )

    if config is not None:
        app.state.config = config

    # Enable CORS
    origins = config.cors_origins if config else ["*"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount peer API routes
    app.include_router(peer_router)

    # Mount WebSocket endpoint
    app.add_api_websocket_route("/ws/events", peer_websocket_endpoint)

    return app


def create_app(
    peer_id: str | None = None,
    tcp_port: int = 9001,
    api_port: int = 8001,
    tracker_url: str = "http://localhost:8000",
    shared_dir: str = "./shared",
    download_dir: str = "./downloads",
    config: PeerConfig | None = None,
    **kwargs,
) -> FastAPI:
    """Create peer FastAPI application accepting keyword parameters."""
    if config is None:
        config = PeerConfig(
            peer_id=peer_id or uuid.uuid4().hex,
            tcp_port=tcp_port,
            api_port=api_port,
            tracker_url=tracker_url,
            shared_dir=shared_dir,
            download_dir=download_dir,
            **kwargs,
        )
    return create_peer_app(config)


# Default application instance for ASGI servers
app = create_peer_app()



def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments for the peer node."""
    parser = argparse.ArgumentParser(
        description="P2P File Sharing Peer Node Service",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--peer-id",
        type=str,
        default=None,
        help="Unique identifier for this peer (defaults to auto-generated UUID)",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Network interface to bind peer services to",
    )
    parser.add_argument(
        "--tcp-port",
        type=int,
        default=9001,
        help="TCP socket port for peer-to-peer file transfers",
    )
    parser.add_argument(
        "--api-port",
        type=int,
        default=8001,
        help="HTTP API port for peer control endpoints",
    )
    parser.add_argument(
        "--tracker-url",
        type=str,
        default="http://localhost:8000",
        help="URL of the central Tracker service",
    )
    parser.add_argument(
        "--shared-dir",
        type=str,
        default="./shared",
        help="Directory containing files to share with the network",
    )
    parser.add_argument(
        "--download-dir",
        type=str,
        default="./downloads",
        help="Directory where downloaded files are saved",
    )
    return parser.parse_args()


if __name__ == "__main__":
    setup_logging(name="p2p.peer")
    cli_args = parse_arguments()

    peer_config = PeerConfig(
        peer_id=cli_args.peer_id or uuid.uuid4().hex,
        host=cli_args.host,
        tcp_port=cli_args.tcp_port,
        api_port=cli_args.api_port,
        tracker_url=cli_args.tracker_url,
        shared_dir=cli_args.shared_dir,
        download_dir=cli_args.download_dir,
    )

    peer_app = create_peer_app(peer_config)
    uvicorn.run(peer_app, host=peer_config.host, port=peer_config.api_port)
