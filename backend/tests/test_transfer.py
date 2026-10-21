"""Tests for the TransferManager."""

import threading
import pytest
from app.core.transfer_manager import TransferManager
from app.schemas.transfer import TransferDirection, TransferStatus


def test_create_transfer():
    """Create a transfer record and verify all initialized fields."""
    manager = TransferManager(peer_id="peer-local")
    transfer = manager.create_transfer(
        file_id="abc123456789",
        filename="test_file.zip",
        source_peer_id="peer-source",
        dest_peer_id="peer-dest",
        direction=TransferDirection.DOWNLOAD,
        total_bytes=1000,
    )

    assert transfer.transfer_id is not None
    assert transfer.file_id == "abc123456789"
    assert transfer.filename == "test_file.zip"
    assert transfer.source_peer_id == "peer-source"
    assert transfer.dest_peer_id == "peer-dest"
    assert transfer.direction == TransferDirection.DOWNLOAD
    assert transfer.status == TransferStatus.PENDING
    assert transfer.bytes_transferred == 0
    assert transfer.total_bytes == 1000
    assert transfer.progress_percent == 0.0
    assert transfer.started_at is not None
    assert transfer.completed_at is None
    assert transfer.error_message is None


def test_update_status():
    """Update transfer status and verify state progression."""
    manager = TransferManager(peer_id="peer-local")
    transfer = manager.create_transfer(
        file_id="fid1",
        filename="video.mp4",
        source_peer_id="p1",
        dest_peer_id="p2",
        direction=TransferDirection.DOWNLOAD,
        total_bytes=5000,
    )

    updated = manager.update_status(transfer.transfer_id, TransferStatus.DOWNLOADING)
    assert updated is not None
    assert updated.status == TransferStatus.DOWNLOADING

    # Check status retrieved via get_transfer
    fetched = manager.get_transfer(transfer.transfer_id)
    assert fetched is not None
    assert fetched.status == TransferStatus.DOWNLOADING


def test_update_progress():
    """Update bytes transferred and verify progress_percent calculation."""
    manager = TransferManager(peer_id="peer-local")
    transfer = manager.create_transfer(
        file_id="fid2",
        filename="data.bin",
        source_peer_id="p1",
        dest_peer_id="p2",
        direction=TransferDirection.UPLOAD,
        total_bytes=1000,
    )

    updated = manager.update_progress(transfer.transfer_id, bytes_transferred=250)
    assert updated is not None
    assert updated.bytes_transferred == 250
    assert updated.progress_percent == 25.0

    updated_full = manager.update_progress(transfer.transfer_id, bytes_transferred=1000)
    assert updated_full is not None
    assert updated_full.bytes_transferred == 1000
    assert updated_full.progress_percent == 100.0


def test_cancel_transfer():
    """Cancelling an active transfer sets status to CANCELLED and is_cancelled to True."""
    manager = TransferManager(peer_id="peer-local")
    transfer = manager.create_transfer(
        file_id="fid3",
        filename="big.iso",
        source_peer_id="p1",
        dest_peer_id="p2",
        direction=TransferDirection.DOWNLOAD,
        total_bytes=20000,
    )

    assert manager.is_cancelled(transfer.transfer_id) is False

    cancelled = manager.cancel_transfer(transfer.transfer_id)
    assert cancelled is not None
    assert cancelled.status == TransferStatus.CANCELLED
    assert manager.is_cancelled(transfer.transfer_id) is True


def test_get_all_transfers():
    """Verify creating multiple transfers returns all of them."""
    manager = TransferManager(peer_id="peer-local")
    t1 = manager.create_transfer("f1", "doc1.txt", "p1", "p2", TransferDirection.DOWNLOAD, 100)
    t2 = manager.create_transfer("f2", "doc2.txt", "p1", "p2", TransferDirection.UPLOAD, 200)

    transfers = manager.get_all_transfers()
    assert len(transfers) == 2
    transfer_ids = {t.transfer_id for t in transfers}
    assert t1.transfer_id in transfer_ids
    assert t2.transfer_id in transfer_ids


def test_get_nonexistent_transfer():
    """get_transfer returns None for unknown IDs."""
    manager = TransferManager(peer_id="peer-local")
    assert manager.get_transfer("unknown-transfer-id") is None
    assert manager.update_status("unknown-transfer-id", TransferStatus.COMPLETED) is None
    assert manager.update_progress("unknown-transfer-id", 100) is None
    assert manager.cancel_transfer("unknown-transfer-id") is None


def test_concurrent_updates():
    """Verify thread-safety when multiple threads concurrently update progress on the same transfer."""
    manager = TransferManager(peer_id="peer-local")
    transfer = manager.create_transfer(
        file_id="concurrent-file",
        filename="concurrent.dat",
        source_peer_id="p1",
        dest_peer_id="p2",
        direction=TransferDirection.DOWNLOAD,
        total_bytes=100000,
    )

    errors = []

    def worker(worker_id: int):
        try:
            for i in range(100):
                manager.update_progress(
                    transfer.transfer_id,
                    bytes_transferred=(worker_id * 100) + i,
                )
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=worker, args=(t,)) for t in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, f"Errors occurred during concurrent updates: {errors}"
    final_transfer = manager.get_transfer(transfer.transfer_id)
    assert final_transfer is not None
    assert final_transfer.bytes_transferred >= 0
