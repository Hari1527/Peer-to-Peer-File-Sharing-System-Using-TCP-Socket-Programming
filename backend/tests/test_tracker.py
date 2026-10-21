"""Tests for TrackerService business logic."""

import time
import pytest
from app.config import TrackerConfig
from app.core.tracker_service import TrackerService
from app.schemas.peer import PeerHeartbeatRequest, PeerRegisterRequest


def test_register_peer(tracker_service: TrackerService):
    """Register a peer and verify it appears in get_peers."""
    req = PeerRegisterRequest(
        peer_id="test-peer-reg",
        host="127.0.0.1",
        tcp_port=9001,
        api_port=8001,
    )
    peer_info = tracker_service.register_peer(req)
    assert peer_info.peer_id == "test-peer-reg"
    assert peer_info.host == "127.0.0.1"
    assert peer_info.tcp_port == 9001
    assert peer_info.status == "online"

    peers_resp = tracker_service.get_peers()
    assert any(p.peer_id == "test-peer-reg" for p in peers_resp.peers)


def test_register_peer_with_files(tracker_service: TrackerService):
    """Register peer with shared files and verify files are indexed."""
    shared_files = [
        {
            "file_id": "sha256_hash_1",
            "filename": "report.pdf",
            "size": 1024,
            "checksum": "sha256_hash_1",
        },
        {
            "file_id": "sha256_hash_2",
            "filename": "data.csv",
            "size": 2048,
            "checksum": "sha256_hash_2",
        },
    ]
    req = PeerRegisterRequest(
        peer_id="peer-with-files",
        host="127.0.0.1",
        tcp_port=9002,
        api_port=8002,
        shared_files=shared_files,
    )
    peer_info = tracker_service.register_peer(req)
    assert peer_info.file_count == 2

    files_resp = tracker_service.get_files()
    indexed_names = {f.filename for f in files_resp.files}
    assert "report.pdf" in indexed_names
    assert "data.csv" in indexed_names


def test_duplicate_registration(tracker_service: TrackerService):
    """Re-registering an existing peer updates its network details."""
    req1 = PeerRegisterRequest(
        peer_id="dup-peer",
        host="127.0.0.1",
        tcp_port=9001,
        api_port=8001,
    )
    tracker_service.register_peer(req1)

    req2 = PeerRegisterRequest(
        peer_id="dup-peer",
        host="192.168.1.50",
        tcp_port=9999,
        api_port=8888,
    )
    updated = tracker_service.register_peer(req2)
    assert updated.host == "192.168.1.50"
    assert updated.tcp_port == 9999
    assert updated.api_port == 8888

    peers = tracker_service.get_peers().peers
    matching = [p for p in peers if p.peer_id == "dup-peer"]
    assert len(matching) == 1
    assert matching[0].tcp_port == 9999


def test_heartbeat(tracker_service: TrackerService):
    """Heartbeat updates the last_seen timestamp."""
    req = PeerRegisterRequest(
        peer_id="hb-peer",
        host="127.0.0.1",
        tcp_port=9001,
        api_port=8001,
    )
    initial = tracker_service.register_peer(req)
    time.sleep(0.01)

    hb_req = PeerHeartbeatRequest(peer_id="hb-peer")
    updated = tracker_service.heartbeat(hb_req)
    assert updated.peer_id == "hb-peer"
    assert updated.status == "online"


def test_heartbeat_nonexistent(tracker_service: TrackerService):
    """Heartbeat for an unknown peer raises KeyError."""
    hb_req = PeerHeartbeatRequest(peer_id="unknown-peer-404")
    with pytest.raises(KeyError):
        tracker_service.heartbeat(hb_req)


def test_get_peers_online(tracker_service: TrackerService):
    """Status filter only returns peers matching the status."""
    req = PeerRegisterRequest(
        peer_id="peer-online-check",
        host="127.0.0.1",
        tcp_port=9001,
        api_port=8001,
    )
    tracker_service.register_peer(req)

    online_peers = tracker_service.get_peers(status="online")
    assert any(p.peer_id == "peer-online-check" for p in online_peers.peers)

    offline_peers = tracker_service.get_peers(status="offline")
    assert not any(p.peer_id == "peer-online-check" for p in offline_peers.peers)


def test_remove_peer(tracker_service: TrackerService):
    """Deleting a peer removes it and its indexed files."""
    shared_files = [
        {"file_id": "rem-fid-1", "filename": "temp.txt", "size": 10, "checksum": "rem-fid-1"}
    ]
    req = PeerRegisterRequest(
        peer_id="peer-to-delete",
        host="127.0.0.1",
        tcp_port=9001,
        api_port=8001,
        shared_files=shared_files,
    )
    tracker_service.register_peer(req)

    deleted = tracker_service.remove_peer("peer-to-delete")
    assert deleted is True

    # Peer should no longer be in get_peers
    peers = tracker_service.get_peers().peers
    assert not any(p.peer_id == "peer-to-delete" for p in peers)

    # Files should no longer be indexed
    files = tracker_service.get_files().files
    assert not any(f.file_id == "rem-fid-1" for f in files)


def test_search_files(tracker_service: TrackerService):
    """Search by filename substring finds matching files."""
    files = [
        {"file_id": "hash-search-1", "filename": "financial_report_2026.xlsx", "size": 500, "checksum": "hash-search-1"},
        {"file_id": "hash-search-2", "filename": "vacation_photo.jpeg", "size": 2500, "checksum": "hash-search-2"},
    ]
    req = PeerRegisterRequest(
        peer_id="search-seeder",
        host="127.0.0.1",
        tcp_port=9001,
        api_port=8001,
        shared_files=files,
    )
    tracker_service.register_peer(req)

    results = tracker_service.search_files(query="report")
    assert results.total >= 1
    filenames = [f.filename for f in results.files]
    assert "financial_report_2026.xlsx" in filenames
    assert "vacation_photo.jpeg" not in filenames


def test_search_files_no_results(tracker_service: TrackerService):
    """Searching for a nonexistent file returns empty list."""
    results = tracker_service.search_files(query="completely_nonexistent_token_xyz")
    assert results.total == 0
    assert results.files == []


def test_get_file_peers(tracker_service: TrackerService):
    """Locate peers that share a specific file."""
    files = [
        {"file_id": "seeder-file-id-123", "filename": "seeder.dat", "size": 800, "checksum": "seeder-file-id-123"}
    ]
    req = PeerRegisterRequest(
        peer_id="seed-peer-node",
        host="127.0.0.1",
        tcp_port=9050,
        api_port=8050,
        shared_files=files,
    )
    tracker_service.register_peer(req)

    peer_response = tracker_service.get_file_peers(file_id="seeder-file-id-123")
    assert peer_response.file_id == "seeder-file-id-123"
    assert peer_response.filename == "seeder.dat"
    assert any(p.peer_id == "seed-peer-node" for p in peer_response.peers)


def test_expire_stale_peers(tracker_db):
    """Peers exceeding heartbeat timeout are expired and set offline."""
    short_config = TrackerConfig(peer_expiry_seconds=1)
    short_service = TrackerService(db=tracker_db, config=short_config)

    req = PeerRegisterRequest(
        peer_id="soon-stale-peer",
        host="127.0.0.1",
        tcp_port=9001,
        api_port=8001,
    )
    short_service.register_peer(req)

    # Wait for expiration duration
    time.sleep(1.2)
    expired_count = short_service.expire_stale_peers()
    assert expired_count >= 1

    online_peers = short_service.get_peers(status="online").peers
    assert not any(p.peer_id == "soon-stale-peer" for p in online_peers)

    offline_peers = short_service.get_peers(status="offline").peers
    assert any(p.peer_id == "soon-stale-peer" for p in offline_peers)


def test_get_stats(tracker_service: TrackerService):
    """Verify stats reflect registered peers, indexed files, and transfers."""
    initial_stats = tracker_service.get_stats()
    assert "peers_online" in initial_stats
    assert "total_files" in initial_stats
    assert "total_transfers" in initial_stats
    assert "bytes_transferred" in initial_stats

    req = PeerRegisterRequest(
        peer_id="stat-peer",
        host="127.0.0.1",
        tcp_port=9001,
        api_port=8001,
        shared_files=[{"file_id": "fstat", "filename": "stat.txt", "size": 100, "checksum": "fstat"}],
    )
    tracker_service.register_peer(req)

    new_stats = tracker_service.get_stats()
    assert new_stats["peers_online"] >= initial_stats["peers_online"] + 1
    assert new_stats["total_files"] >= initial_stats["total_files"] + 1
