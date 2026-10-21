"""Tracker FastAPI server entry point."""

import asyncio
from contextlib import asynccontextmanager
import logging
from typing import AsyncGenerator
import uvicorn
from fastapi import FastAPI, HTTPException, Request, WebSocket, status
from fastapi.middleware.cors import CORSMiddleware

from .api.tracker import router as tracker_router
from .api.websocket import websocket_endpoint
from .config import TrackerConfig
from .core.tracker_service import TrackerService
from .db.database import TrackerDatabase
from .utils.logging_config import setup_logging

logger = setup_logging(level="INFO", name="p2p.tracker")


async def peer_expiry_task(service: TrackerService, interval: int = 30) -> None:
    """Periodically check for stale peers and mark them offline."""
    logger.info("Started periodic peer expiry task (interval=%ds)", interval)
    while True:
        try:
            await asyncio.sleep(interval)
            await asyncio.to_thread(service.expire_stale_peers)
        except asyncio.CancelledError:
            logger.info("Peer expiry task cancelled")
            break
        except Exception as e:
            logger.error("Error running peer expiry task: %s", e)


def get_tracker_service(request: Request) -> TrackerService:
    """Dependency provider returning the TrackerService instance from app.state."""
    service: TrackerService | None = getattr(request.app.state, "tracker_service", None)
    if service is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="TrackerService not initialized",
        )
    return service


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application startup and shutdown lifecycle."""
    # Startup
    config = TrackerConfig()
    database = TrackerDatabase(db_path=config.db_path)
    database.initialize()

    tracker_service = TrackerService(db=database, config=config)
    app.state.tracker_service = tracker_service
    app.state.config = config
    app.state.db = database

    # Background task for removing expired peers
    expiry_worker = asyncio.create_task(peer_expiry_task(tracker_service, interval=30))
    app.state.expiry_task = expiry_worker
    logger.info("Tracker application startup complete. Listening on %s:%d", config.host, config.port)

    yield

    # Shutdown
    logger.info("Initiating tracker shutdown...")
    expiry_worker.cancel()
    try:
        await expiry_worker
    except asyncio.CancelledError:
        pass
    logger.info("Tracker shutdown complete")


def create_app() -> FastAPI:
    """Construct and configure the FastAPI Tracker application."""
    config = TrackerConfig()
    app = FastAPI(
        title="P2P Tracker Server",
        description="Central registry and coordination tracker for P2P file sharing",
        version="1.0.0",
        lifespan=lifespan,
    )

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include tracker API routes
    app.include_router(tracker_router)

    # WebSocket events endpoint
    @app.websocket("/ws/events")
    async def ws_events(websocket: WebSocket) -> None:
        await websocket_endpoint(websocket)

    return app


app = create_app()


if __name__ == "__main__":
    cfg = TrackerConfig()
    uvicorn.run("app.main:app", host=cfg.host, port=cfg.port, reload=False)
