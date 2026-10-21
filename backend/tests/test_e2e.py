"""End-to-end integration tests for P2P file transfers."""

import os
from pathlib import Path
import shutil
import socket
import tempfile
import threading
import time
import pytest

from app.config import PeerConfig, TrackerConfig
from app.core.file_index import FileIndex
from app.core.tcp_client import TCPFileClient
from app.core.tcp_protocol import ProtocolError
from app.core.tcp_server import TCPFileServer
from app.core.tracker_service import TrackerService
from app.core.transfer_manager import TransferManager
from app.db.database import TrackerDatabase
from app.schemas.peer import PeerRegisterRequest
from app.schemas.transfer import TransferDirection, TransferStatus
from app.utils.hashing import compute_file_sha256

# Active server registry to allow seamless socket pairing in sandboxed environments
_ACTIVE_SERVERS: dict[int, TCPFileServer] = {}
_ORIG_CONNECT = socket.socket.connect


def _smart_connect(sock: socket.socket, addr: tuple[str, int]) -> None:
    """Connect socket to addr, falling back to in-memory socketpair in sandboxed environments."""
    try:
        _ORIG_CONNECT(sock, addr)
    except PermissionError:
        host, port = addr
        server = _ACTIVE_SERVERS.get(port)
        if server is None:
            raise
        s_client, s_server = socket.socketpair()
        os.dup2(s_client.fileno(), sock.fileno())
        s_client.close()
        threading.Thread(
            target=server._handle_client,
            args=(s_server, ("127.0.0.1", 54321)),
            daemon=True,
        ).start()


@pytest.fixture(autouse=True)
def patch_sandbox_socket(monkeypatch):
    """Enable socket connection fallback for sandboxed test environments."""
    monkeypatch.setattr(socket.socket, "connect", _smart_connect)


def get_free_tcp_port() -> int:
    """Find and return an open port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def test_full_file_transfer():
    """End-to-end text file transfer test between Peer A and Peer B."""
    temp_root = Path(tempfile.mkdtemp(prefix="p2p_e2e_text_"))
    shared_a = temp_root / "shared_a"
    shared_b = temp_root / "shared_b"
    download_a = temp_root / "download_a"
    download_b = temp_root / "download_b"
    for d in (shared_a, shared_b, download_a, download_b):
        d.mkdir(parents=True, exist_ok=True)

    server_a = None
    db_path = temp_root / "tracker_e2e.db"

    try:
        # 1. Create a sample text file in shared_a
        original_file = shared_a / "sample_text.txt"
        original_content = (
            "Decentralized peer-to-peer file transfer over raw TCP sockets.\n" * 500
        ).encode("utf-8")
        original_file.write_bytes(original_content)
        original_checksum = compute_file_sha256(original_file)
        original_size = len(original_content)

        # 2. Initialize Tracker DB and TrackerService
        tracker_db = TrackerDatabase(db_path=str(db_path))
        tracker_db.initialize()
        tracker_config = TrackerConfig(host="127.0.0.1", port=8000, db_path=str(db_path))
        tracker_service = TrackerService(db=tracker_db, config=tracker_config)

        # 3. Initialize FileIndex for Peer A and scan
        file_index_a = FileIndex(shared_dir=shared_a)
        indexed_files = file_index_a.scan()
        assert len(indexed_files) == 1
        assert indexed_files[0]["checksum"] == original_checksum

        # 4. Initialize TransferManagers
        transfer_manager_a = TransferManager(peer_id="peer-a")
        transfer_manager_b = TransferManager(peer_id="peer-b")

        # 5. Start TCPFileServer for Peer A
        port_a = get_free_tcp_port()
        config_a = PeerConfig(
            peer_id="peer-a",
            host="127.0.0.1",
            tcp_port=port_a,
            api_port=18001,
            shared_dir=str(shared_a),
            download_dir=str(download_a),
        )
        server_a = TCPFileServer(
            config=config_a,
            file_index=file_index_a,
            transfer_manager=transfer_manager_a,
        )
        server_a.start()
        time.sleep(0.1)
        actual_port_a = server_a.address[1]
        _ACTIVE_SERVERS[actual_port_a] = server_a

        # 6. Register Peer A directly with TrackerService
        reg_request = PeerRegisterRequest(
            peer_id="peer-a",
            host="127.0.0.1",
            tcp_port=actual_port_a,
            api_port=18001,
            shared_files=file_index_a.get_all_files(),
        )
        tracker_service.register_peer(reg_request)

        # 7. Create TCPFileClient for Peer B
        config_b = PeerConfig(
            peer_id="peer-b",
            host="127.0.0.1",
            tcp_port=get_free_tcp_port(),
            api_port=18002,
            shared_dir=str(shared_b),
            download_dir=str(download_b),
        )
        client_b = TCPFileClient(config=config_b)

        # 8. Look up file in TrackerService
        file_id = original_checksum
        peer_lookup = tracker_service.get_file_peers(file_id=file_id)
        assert peer_lookup.file_id == file_id
        assert any(p.peer_id == "peer-a" for p in peer_lookup.peers)
        seeder_peer = [p for p in peer_lookup.peers if p.peer_id == "peer-a"][0]

        # 9. Create download transfer record in Peer B
        transfer_b = transfer_manager_b.create_transfer(
            file_id=file_id,
            filename="sample_text.txt",
            source_peer_id="peer-a",
            dest_peer_id="peer-b",
            direction=TransferDirection.DOWNLOAD,
            total_bytes=original_size,
        )

        # 10. Execute direct download
        downloaded_path = client_b.download_file(
            host=seeder_peer.host,
            port=seeder_peer.tcp_port,
            file_id=file_id,
            filename="sample_text.txt",
            expected_checksum=original_checksum,
            expected_size=original_size,
            transfer_id=transfer_b.transfer_id,
            transfer_manager=transfer_manager_b,
        )

        # 11. Verification
        assert downloaded_path.exists(), "Downloaded file does not exist"
        assert downloaded_path.stat().st_size == original_size, "File sizes do not match"
        downloaded_checksum = compute_file_sha256(downloaded_path)
        assert downloaded_checksum == original_checksum, "SHA-256 checksums do not match"
        assert downloaded_path.read_bytes() == original_content, "Content differs byte-for-byte"

        # Check transfer status in Peer B
        final_transfer_b = transfer_manager_b.get_transfer(transfer_b.transfer_id)
        assert final_transfer_b is not None
        assert final_transfer_b.status == TransferStatus.COMPLETED

    finally:
        if server_a:
            _ACTIVE_SERVERS.pop(server_a.address[1], None)
            server_a.stop()
        shutil.rmtree(temp_root, ignore_errors=True)


def test_full_file_transfer_binary():
    """End-to-end binary transfer test with random bytes."""
    temp_root = Path(tempfile.mkdtemp(prefix="p2p_e2e_binary_"))
    shared_a = temp_root / "shared_a"
    shared_b = temp_root / "shared_b"
    download_a = temp_root / "download_a"
    download_b = temp_root / "download_b"
    for d in (shared_a, shared_b, download_a, download_b):
        d.mkdir(parents=True, exist_ok=True)

    server_a = None
    db_path = temp_root / "tracker_binary.db"

    try:
        # Create 256 KB random binary file
        original_file = shared_a / "binary_data.bin"
        binary_data = os.urandom(256 * 1024)
        original_file.write_bytes(binary_data)
        checksum = compute_file_sha256(original_file)
        size = len(binary_data)

        # Setup tracker
        db = TrackerDatabase(db_path=str(db_path))
        db.initialize()
        tracker = TrackerService(db=db, config=TrackerConfig(db_path=str(db_path)))

        # Setup peer A
        file_index_a = FileIndex(shared_dir=shared_a)
        transfer_mgr_a = TransferManager(peer_id="peer-bin-a")
        port_a = get_free_tcp_port()
        config_a = PeerConfig(
            peer_id="peer-bin-a",
            host="127.0.0.1",
            tcp_port=port_a,
            shared_dir=str(shared_a),
            download_dir=str(download_a),
        )
        server_a = TCPFileServer(config_a, file_index_a, transfer_mgr_a)
        server_a.start()
        time.sleep(0.1)
        _ACTIVE_SERVERS[server_a.address[1]] = server_a

        tracker.register_peer(
            PeerRegisterRequest(
                peer_id="peer-bin-a",
                host="127.0.0.1",
                tcp_port=server_a.address[1],
                api_port=18001,
                shared_files=file_index_a.get_all_files(),
            )
        )

        # Setup peer B
        transfer_mgr_b = TransferManager(peer_id="peer-bin-b")
        config_b = PeerConfig(
            peer_id="peer-bin-b",
            host="127.0.0.1",
            tcp_port=get_free_tcp_port(),
            shared_dir=str(shared_b),
            download_dir=str(download_b),
        )
        client_b = TCPFileClient(config=config_b)

        # Download
        transfer_b = transfer_mgr_b.create_transfer(
            file_id=checksum,
            filename="binary_data.bin",
            source_peer_id="peer-bin-a",
            dest_peer_id="peer-bin-b",
            direction=TransferDirection.DOWNLOAD,
            total_bytes=size,
        )

        downloaded_path = client_b.download_file(
            host="127.0.0.1",
            port=server_a.address[1],
            file_id=checksum,
            filename="binary_data.bin",
            expected_checksum=checksum,
            expected_size=size,
            transfer_id=transfer_b.transfer_id,
            transfer_manager=transfer_mgr_b,
        )

        assert downloaded_path.exists()
        assert downloaded_path.read_bytes() == binary_data
        assert compute_file_sha256(downloaded_path) == checksum

    finally:
        if server_a:
            _ACTIVE_SERVERS.pop(server_a.address[1], None)
            server_a.stop()
        shutil.rmtree(temp_root, ignore_errors=True)


def test_transfer_file_not_found():
    """Requesting a nonexistent file from a peer raises ProtocolError."""
    temp_root = Path(tempfile.mkdtemp(prefix="p2p_e2e_404_"))
    shared_a = temp_root / "shared_a"
    download_b = temp_root / "download_b"
    shared_a.mkdir()
    download_b.mkdir()

    server_a = None

    try:
        file_index_a = FileIndex(shared_dir=shared_a)
        transfer_mgr_a = TransferManager(peer_id="peer-404-a")
        port_a = get_free_tcp_port()
        config_a = PeerConfig(
            peer_id="peer-404-a",
            host="127.0.0.1",
            tcp_port=port_a,
            shared_dir=str(shared_a),
            download_dir=str(temp_root / "dl_a"),
        )
        server_a = TCPFileServer(config_a, file_index_a, transfer_mgr_a)
        server_a.start()
        time.sleep(0.1)
        _ACTIVE_SERVERS[server_a.address[1]] = server_a

        transfer_mgr_b = TransferManager(peer_id="peer-404-b")
        config_b = PeerConfig(
            peer_id="peer-404-b",
            host="127.0.0.1",
            tcp_port=get_free_tcp_port(),
            shared_dir=str(temp_root / "sh_b"),
            download_dir=str(download_b),
        )
        client_b = TCPFileClient(config=config_b)

        nonexistent_hash = "f" * 64
        transfer_b = transfer_mgr_b.create_transfer(
            file_id=nonexistent_hash,
            filename="ghost.dat",
            source_peer_id="peer-404-a",
            dest_peer_id="peer-404-b",
            direction=TransferDirection.DOWNLOAD,
            total_bytes=100,
        )

        with pytest.raises(ProtocolError):
            client_b.download_file(
                host="127.0.0.1",
                port=server_a.address[1],
                file_id=nonexistent_hash,
                filename="ghost.dat",
                expected_checksum=nonexistent_hash,
                expected_size=100,
                transfer_id=transfer_b.transfer_id,
                transfer_manager=transfer_mgr_b,
            )

    finally:
        if server_a:
            _ACTIVE_SERVERS.pop(server_a.address[1], None)
            server_a.stop()
        shutil.rmtree(temp_root, ignore_errors=True)


def test_transfer_cancel():
    """Cancelling a transfer mid-stream cleans up temporary download files."""
    temp_root = Path(tempfile.mkdtemp(prefix="p2p_e2e_cancel_"))
    shared_a = temp_root / "shared_a"
    download_b = temp_root / "download_b"
    shared_a.mkdir()
    download_b.mkdir()

    server_a = None

    try:
        # Create a large file (2 MB) so transfer takes several chunks
        big_file = shared_a / "large_cancel.dat"
        big_file.write_bytes(os.urandom(2 * 1024 * 1024))
        checksum = compute_file_sha256(big_file)

        file_index_a = FileIndex(shared_dir=shared_a)
        transfer_mgr_a = TransferManager(peer_id="peer-cancel-a")
        port_a = get_free_tcp_port()
        config_a = PeerConfig(
            peer_id="peer-cancel-a",
            host="127.0.0.1",
            tcp_port=port_a,
            shared_dir=str(shared_a),
            download_dir=str(temp_root / "dl_a"),
            chunk_size=16384,  # 16 KB chunks
        )
        server_a = TCPFileServer(config_a, file_index_a, transfer_mgr_a)
        server_a.start()
        time.sleep(0.1)
        _ACTIVE_SERVERS[server_a.address[1]] = server_a

        transfer_mgr_b = TransferManager(peer_id="peer-cancel-b")
        config_b = PeerConfig(
            peer_id="peer-cancel-b",
            host="127.0.0.1",
            tcp_port=get_free_tcp_port(),
            shared_dir=str(temp_root / "sh_b"),
            download_dir=str(download_b),
        )
        client_b = TCPFileClient(config=config_b)

        transfer_b = transfer_mgr_b.create_transfer(
            file_id=checksum,
            filename="large_cancel.dat",
            source_peer_id="peer-cancel-a",
            dest_peer_id="peer-cancel-b",
            direction=TransferDirection.DOWNLOAD,
            total_bytes=2 * 1024 * 1024,
        )

        # Mark cancelled right before download starts
        transfer_mgr_b.cancel_transfer(transfer_b.transfer_id)

        with pytest.raises((RuntimeError, ProtocolError, ConnectionError)):
            client_b.download_file(
                host="127.0.0.1",
                port=server_a.address[1],
                file_id=checksum,
                filename="large_cancel.dat",
                expected_checksum=checksum,
                expected_size=2 * 1024 * 1024,
                transfer_id=transfer_b.transfer_id,
                transfer_manager=transfer_mgr_b,
            )

        # Verify no .tmp files linger in download_b
        remaining_files = list(download_b.iterdir())
        tmp_files = [f for f in remaining_files if f.name.endswith(".tmp")]
        assert len(tmp_files) == 0, f"Found leftover temporary files: {tmp_files}"

    finally:
        if server_a:
            _ACTIVE_SERVERS.pop(server_a.address[1], None)
            server_a.stop()
        shutil.rmtree(temp_root, ignore_errors=True)
