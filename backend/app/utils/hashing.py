"""Hashing utilities for file integrity verification."""

import hashlib
from pathlib import Path


def create_sha256_hasher() -> hashlib._Hash:
    """Create and return a new SHA-256 hasher object."""
    return hashlib.sha256()


def compute_file_sha256(filepath: str | Path) -> str:
    """Read a file in 65536-byte chunks and compute its SHA-256 hex digest.

    Args:
        filepath: Path to the target file.

    Returns:
        Hexadecimal SHA-256 string.
    """
    path = Path(filepath)
    hasher = create_sha256_hasher()
    with path.open("rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def verify_checksum(filepath: str | Path, expected: str) -> bool:
    """Verify whether a file's SHA-256 digest matches the expected hash.

    Args:
        filepath: Path to the target file.
        expected: Expected hex digest string.

    Returns:
        True if matching, False otherwise.
    """
    try:
        actual = compute_file_sha256(filepath)
        return actual.lower() == expected.lower().strip()
    except (FileNotFoundError, OSError):
        return False
