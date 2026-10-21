"""Tests for Tracker HTTP REST API."""

import pytest
import httpx
from fastapi import FastAPI


@pytest.mark.asyncio
async def test_health_endpoint(async_client: httpx.AsyncClient):
    """GET /api/health returns 200 OK with health status."""
    response = await async_client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "timestamp" in data
    assert "version" in data


@pytest.mark.asyncio
async def test_register_peer_api(async_client: httpx.AsyncClient):
    """POST /api/peers/register registers a new peer successfully."""
    payload = {
        "peer_id": "api-test-peer-1",
        "host": "127.0.0.1",
        "tcp_port": 9001,
        "api_port": 8001,
        "shared_files": [
            {
                "file_id": "hash-api-file-1",
                "filename": "guide.txt",
                "size": 512,
                "checksum": "hash-api-file-1",
            }
        ],
    }
    response = await async_client.post("/api/peers/register", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["peer_id"] == "api-test-peer-1"
    assert data["host"] == "127.0.0.1"
    assert data["tcp_port"] == 9001
    assert data["status"] == "online"
    assert data["file_count"] == 1


@pytest.mark.asyncio
async def test_get_peers_api(async_client: httpx.AsyncClient):
    """GET /api/peers lists active peers."""
    # Register peer first
    payload = {
        "peer_id": "list-peer-1",
        "host": "127.0.0.1",
        "tcp_port": 9002,
        "api_port": 8002,
        "shared_files": [],
    }
    await async_client.post("/api/peers/register", json=payload)

    response = await async_client.get("/api/peers")
    assert response.status_code == 200
    data = response.json()
    assert "peers" in data
    assert "total" in data
    assert any(p["peer_id"] == "list-peer-1" for p in data["peers"])


@pytest.mark.asyncio
async def test_heartbeat_api(async_client: httpx.AsyncClient):
    """POST /api/peers/heartbeat refreshes peer status."""
    # Register
    reg_payload = {
        "peer_id": "hb-api-peer",
        "host": "127.0.0.1",
        "tcp_port": 9003,
        "api_port": 8003,
        "shared_files": [],
    }
    await async_client.post("/api/peers/register", json=reg_payload)

    # Heartbeat
    hb_payload = {"peer_id": "hb-api-peer"}
    response = await async_client.post("/api/peers/heartbeat", json=hb_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["peer_id"] == "hb-api-peer"
    assert data["status"] == "online"


@pytest.mark.asyncio
async def test_delete_peer_api(async_client: httpx.AsyncClient):
    """DELETE /api/peers/{peer_id} unregisters a peer."""
    # Register
    reg_payload = {
        "peer_id": "delete-me-peer",
        "host": "127.0.0.1",
        "tcp_port": 9004,
        "api_port": 8004,
        "shared_files": [],
    }
    await async_client.post("/api/peers/register", json=reg_payload)

    # Delete
    response = await async_client.delete("/api/peers/delete-me-peer")
    assert response.status_code == 200

    # Ensure removed
    peers_resp = await async_client.get("/api/peers")
    peers_data = peers_resp.json()
    assert not any(p["peer_id"] == "delete-me-peer" for p in peers_data["peers"])


@pytest.mark.asyncio
async def test_get_files_api(async_client: httpx.AsyncClient):
    """GET /api/files returns indexed files."""
    reg_payload = {
        "peer_id": "files-provider-peer",
        "host": "127.0.0.1",
        "tcp_port": 9005,
        "api_port": 8005,
        "shared_files": [
            {
                "file_id": "api-fid-file-listing",
                "filename": "inventory.json",
                "size": 1024,
                "checksum": "api-fid-file-listing",
            }
        ],
    }
    await async_client.post("/api/peers/register", json=reg_payload)

    response = await async_client.get("/api/files")
    assert response.status_code == 200
    data = response.json()
    assert "files" in data
    assert any(f["filename"] == "inventory.json" for f in data["files"])


@pytest.mark.asyncio
async def test_search_files_api(async_client: httpx.AsyncClient):
    """GET /api/files/search searches files by query substring."""
    reg_payload = {
        "peer_id": "search-provider-peer",
        "host": "127.0.0.1",
        "tcp_port": 9006,
        "api_port": 8006,
        "shared_files": [
            {
                "file_id": "search-match-fid",
                "filename": "quarterly_presentation_test.pptx",
                "size": 4096,
                "checksum": "search-match-fid",
            }
        ],
    }
    await async_client.post("/api/peers/register", json=reg_payload)

    response = await async_client.get("/api/files/search?q=presentation_test")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert any(f["filename"] == "quarterly_presentation_test.pptx" for f in data["files"])


@pytest.mark.asyncio
async def test_get_stats_api(async_client: httpx.AsyncClient):
    """GET /api/stats returns system statistics."""
    response = await async_client.get("/api/stats")
    assert response.status_code == 200
    data = response.json()
    assert "peers_online" in data
    assert "total_files" in data
    assert "total_transfers" in data
    assert "bytes_transferred" in data


@pytest.mark.asyncio
async def test_register_invalid_port(async_client: httpx.AsyncClient):
    """POST /api/peers/register with port > 65535 returns 422 Unprocessable Entity."""
    payload = {
        "peer_id": "invalid-port-peer",
        "host": "127.0.0.1",
        "tcp_port": 70000,  # Invalid port > 65535
        "api_port": 8001,
        "shared_files": [],
    }
    response = await async_client.post("/api/peers/register", json=payload)
    assert response.status_code == 422
