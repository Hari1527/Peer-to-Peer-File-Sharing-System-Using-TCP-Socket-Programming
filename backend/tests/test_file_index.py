"""Tests for local file indexing and hashing."""

from pathlib import Path
import pytest
from app.core.file_index import FileIndex
from app.utils.hashing import compute_file_sha256


def test_scan_directory(tmp_path: Path):
    """Scan directory with files and verify all are found and indexed."""
    shared_dir = tmp_path / "shared"
    shared_dir.mkdir()

    file1 = shared_dir / "file1.txt"
    file1.write_text("Hello from file 1")
    file2 = shared_dir / "file2.bin"
    file2.write_bytes(b"\x00\x01\x02\x03\x04")

    indexer = FileIndex(shared_dir=shared_dir)
    indexed = indexer.scan()

    assert len(indexed) == 2
    filenames = {f["filename"] for f in indexed}
    assert "file1.txt" in filenames
    assert "file2.bin" in filenames

    # Verify checksums match compute_file_sha256
    for item in indexed:
        expected_hash = compute_file_sha256(shared_dir / item["filename"])
        assert item["checksum"] == expected_hash
        assert item["file_id"] == expected_hash


def test_scan_empty_directory(tmp_path: Path):
    """Scan empty directory returns empty list."""
    empty_dir = tmp_path / "empty_shared"
    empty_dir.mkdir()

    indexer = FileIndex(shared_dir=empty_dir)
    assert indexer.scan() == []
    assert indexer.get_all_files() == []


def test_get_file_path(tmp_path: Path):
    """Look up a scanned file by its file_id (checksum)."""
    shared_dir = tmp_path / "shared"
    shared_dir.mkdir()
    sample = shared_dir / "target.txt"
    sample.write_text("Unique target content")

    indexer = FileIndex(shared_dir=shared_dir)
    file_id = compute_file_sha256(sample)

    path = indexer.get_file_path(file_id)
    assert path is not None
    assert path.resolve() == sample.resolve()


def test_get_file_path_not_found(tmp_path: Path):
    """Look up nonexistent file returns None."""
    shared_dir = tmp_path / "shared"
    shared_dir.mkdir()

    indexer = FileIndex(shared_dir=shared_dir)
    assert indexer.get_file_path("nonexistent_file_id") is None


def test_has_file(tmp_path: Path):
    """Verify has_file returns True for scanned files and False for others."""
    shared_dir = tmp_path / "shared"
    shared_dir.mkdir()
    sample = shared_dir / "exists.txt"
    sample.write_text("I exist")

    indexer = FileIndex(shared_dir=shared_dir)
    file_id = compute_file_sha256(sample)

    assert indexer.has_file(file_id) is True
    assert indexer.has_file("nonexistent_id") is False


def test_refresh(tmp_path: Path):
    """Adding a new file and calling refresh updates the index."""
    shared_dir = tmp_path / "shared"
    shared_dir.mkdir()
    file1 = shared_dir / "first.txt"
    file1.write_text("First file")

    indexer = FileIndex(shared_dir=shared_dir)
    initial_files = indexer.scan()
    assert len(initial_files) == 1

    # Add second file
    file2 = shared_dir / "second.txt"
    file2.write_text("Second file")

    refreshed = indexer.refresh()
    assert len(refreshed) == 2
    filenames = {f["filename"] for f in refreshed}
    assert "first.txt" in filenames
    assert "second.txt" in filenames


def test_skips_hidden_files(tmp_path: Path):
    """Files starting with a dot are skipped."""
    shared_dir = tmp_path / "shared"
    shared_dir.mkdir()
    hidden_file = shared_dir / ".hidden_secret.txt"
    hidden_file.write_text("Secret")
    regular_file = shared_dir / "visible.txt"
    regular_file.write_text("Visible")

    indexer = FileIndex(shared_dir=shared_dir)
    indexed = indexer.scan()

    assert len(indexed) == 1
    assert indexed[0]["filename"] == "visible.txt"


def test_skips_large_files(tmp_path: Path):
    """Files exceeding max_file_size are skipped."""
    shared_dir = tmp_path / "shared"
    shared_dir.mkdir()
    normal_file = shared_dir / "small.txt"
    normal_file.write_text("Small enough")

    large_file = shared_dir / "too_big.dat"
    large_file.write_bytes(b"A" * 1024)

    # Set max_file_size to 500 bytes
    indexer = FileIndex(shared_dir=shared_dir, max_file_size=500)
    indexed = indexer.scan()

    assert len(indexed) == 1
    assert indexed[0]["filename"] == "small.txt"
