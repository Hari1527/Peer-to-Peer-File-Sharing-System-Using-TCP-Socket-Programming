"""Pytest fixtures for P2P file sharing test suite."""

import os
from pathlib import Path
import shutil
import tempfile
from typing import AsyncGenerator, Generator
import pytest
import pytest_asyncio
import httpx
from httpx import ASGITransport
from fastapi import FastAPI

from app.config import PeerConfig, TrackerConfig
from app.core.tracker_service import TrackerService
from app.db.database import TrackerDatabase
from app.main import create_app


@pytest.fixture
def tmp_shared_dir() -> Generator[Path, None, None]:
    """Create a temporary shared directory populated with sample files."""
    temp_dir = Path(tempfile.mkdtemp(prefix="p2p_shared_"))
    
    # Text file
    text_file = temp_dir / "hello.txt"
    text_file.write_text("Hello P2P network! This is a test file.", encoding="utf-8")

    # Binary file (10 KB)
    bin_file = temp_dir / "image.bin"
    bin_file.write_bytes(os.urandom(10 * 1024))

    # Large file (1 MB)
    large_file = temp_dir / "large.dat"
    large_file.write_bytes(os.urandom(1024 * 1024))

    try:
        yield temp_dir
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def tmp_download_dir() -> Generator[Path, None, None]:
    """Create an empty temporary download directory."""
    temp_dir = Path(tempfile.mkdtemp(prefix="p2p_download_"))
    try:
        yield temp_dir
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_text_file(tmp_shared_dir: Path) -> Path:
    """Return the path to sample 'hello.txt' in tmp_shared_dir."""
    target = tmp_shared_dir / "hello.txt"
    if not target.exists():
        target.write_text("Hello P2P network! This is a test file.", encoding="utf-8")
    return target


@pytest.fixture
def sample_binary_file(tmp_shared_dir: Path) -> Path:
    """Return the path to sample 'image.bin' (10KB) in tmp_shared_dir."""
    target = tmp_shared_dir / "image.bin"
    if not target.exists():
        target.write_bytes(os.urandom(10 * 1024))
    return target


@pytest.fixture
def sample_large_file(tmp_shared_dir: Path) -> Path:
    """Return the path to sample 'large.dat' (1MB) in tmp_shared_dir."""
    target = tmp_shared_dir / "large.dat"
    if not target.exists():
        target.write_bytes(os.urandom(1024 * 1024))
    return target


@pytest.fixture
def tracker_db() -> Generator[TrackerDatabase, None, None]:
    """Create an isolated TrackerDatabase instance in a temp file and initialize it."""
    temp_fd, temp_db_path = tempfile.mkstemp(prefix="tracker_test_", suffix=".db")
    os.close(temp_fd)
    
    db = TrackerDatabase(db_path=temp_db_path)
    db.initialize()
    try:
        yield db
    finally:
        if os.path.exists(temp_db_path):
            try:
                os.remove(temp_db_path)
            except OSError:
                pass


@pytest.fixture
def tracker_config(tracker_db: TrackerDatabase) -> TrackerConfig:
    """Create a TrackerConfig configured for tests."""
    return TrackerConfig(
        host="127.0.0.1",
        port=8000,
        db_path=tracker_db.db_path,
        peer_expiry_seconds=60,
        heartbeat_timeout=10,
    )


@pytest.fixture
def peer_config_1(tmp_shared_dir: Path, tmp_download_dir: Path) -> PeerConfig:
    """Create PeerConfig for peer 1."""
    return PeerConfig(
        peer_id="test-peer-1",
        host="127.0.0.1",
        tcp_port=19001,
        api_port=18001,
        tracker_url="http://127.0.0.1:8000",
        shared_dir=str(tmp_shared_dir),
        download_dir=str(tmp_download_dir),
    )


@pytest.fixture
def peer_config_2(tmp_download_dir: Path) -> Generator[PeerConfig, None, None]:
    """Create PeerConfig for peer 2 with dedicated shared and download directories."""
    peer2_shared = Path(tempfile.mkdtemp(prefix="p2p_peer2_shared_"))
    try:
        yield PeerConfig(
            peer_id="test-peer-2",
            host="127.0.0.1",
            tcp_port=19002,
            api_port=18002,
            tracker_url="http://127.0.0.1:8000",
            shared_dir=str(peer2_shared),
            download_dir=str(tmp_download_dir),
        )
    finally:
        shutil.rmtree(peer2_shared, ignore_errors=True)


@pytest.fixture
def tracker_service(tracker_db: TrackerDatabase, tracker_config: TrackerConfig) -> TrackerService:
    """Create TrackerService wired to temp database and config."""
    return TrackerService(db=tracker_db, config=tracker_config)


@pytest.fixture
def tracker_app(
    tracker_db: TrackerDatabase,
    tracker_config: TrackerConfig,
    tracker_service: TrackerService,
) -> FastAPI:
    """Create the tracker FastAPI app configured with test services."""
    app = create_app()
    app.state.tracker_service = tracker_service
    app.state.config = tracker_config
    app.state.db = tracker_db
    return app


@pytest_asyncio.fixture
async def async_client(tracker_app: FastAPI) -> AsyncGenerator[httpx.AsyncClient, None]:
    """Async HTTP client targeting the tracker FastAPI test application."""
    transport = ASGITransport(app=tracker_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
