"""Tests for hashing utilities."""

import hashlib
import os
from pathlib import Path
import pytest
from app.utils.hashing import compute_file_sha256, verify_checksum


def test_compute_file_sha256(tmp_path: Path):
    """Compute hash of a file with known content and verify against hashlib."""
    content = b"The quick brown fox jumps over the lazy dog"
    test_file = tmp_path / "fox.txt"
    test_file.write_bytes(content)

    expected_hash = hashlib.sha256(content).hexdigest()
    actual_hash = compute_file_sha256(test_file)

    assert actual_hash == expected_hash
    assert actual_hash == "d7a8fbb307d7809469ca9abcb0082e4f8d5651e46d3cdb762d02d0bf37c9e592"


def test_compute_sha256_empty_file(tmp_path: Path):
    """Empty file hash matches the well-known SHA-256 for 0 bytes."""
    empty_file = tmp_path / "empty.txt"
    empty_file.write_bytes(b"")

    expected_empty_hash = hashlib.sha256(b"").hexdigest()
    # e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
    actual_hash = compute_file_sha256(empty_file)

    assert actual_hash == expected_empty_hash
    assert actual_hash == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"


def test_verify_checksum_match(tmp_path: Path):
    """verify_checksum returns True when hash matches expected."""
    content = b"Hello, P2P World!"
    sample_file = tmp_path / "hello.txt"
    sample_file.write_bytes(content)

    expected_hash = hashlib.sha256(content).hexdigest()
    assert verify_checksum(sample_file, expected_hash) is True
    # Test uppercase handling
    assert verify_checksum(sample_file, expected_hash.upper()) is True
    # Test whitespace trimming
    assert verify_checksum(sample_file, f"  {expected_hash} \n") is True


def test_verify_checksum_mismatch(tmp_path: Path):
    """verify_checksum returns False when checksum is incorrect or file is missing."""
    content = b"File content A"
    sample_file = tmp_path / "file_a.txt"
    sample_file.write_bytes(content)

    wrong_hash = "0000000000000000000000000000000000000000000000000000000000000000"
    assert verify_checksum(sample_file, wrong_hash) is False

    # Non-existent file
    assert verify_checksum(tmp_path / "nonexistent.txt", wrong_hash) is False


def test_compute_sha256_binary(tmp_path: Path):
    """Binary file with random bytes yields consistent and matching hash."""
    random_bytes = os.urandom(128 * 1024)  # 128 KB
    bin_file = tmp_path / "random.bin"
    bin_file.write_bytes(random_bytes)

    expected_hash = hashlib.sha256(random_bytes).hexdigest()
    hash_1 = compute_file_sha256(bin_file)
    hash_2 = compute_file_sha256(bin_file)

    assert hash_1 == expected_hash
    assert hash_2 == expected_hash
