"""Tests for the security module."""

from pathlib import Path
import pytest
from app.core.security import (
    validate_filename,
    sanitize_filename,
    validate_file_path,
    validate_file_id,
    check_path_traversal,
)


def test_validate_filename_valid():
    """Normal safe filenames pass validation."""
    assert validate_filename("document.pdf") is True
    assert validate_filename("archive_2026.tar.gz") is True
    assert validate_filename("my photo-1.jpeg") is True
    assert validate_filename("test.txt") is True


def test_validate_filename_path_traversal():
    """Filenames with directory traversal patterns are rejected."""
    assert validate_filename("../etc/passwd") is False
    assert validate_filename("..\\windows\\system32") is False
    assert validate_filename("dir/../secret.txt") is False
    assert validate_filename("subfolder/file.txt") is False


def test_validate_filename_absolute_path():
    """Filenames that represent absolute paths are rejected."""
    assert validate_filename("/etc/passwd") is False
    assert validate_filename("/home/user/test.txt") is False
    assert validate_filename("\\Windows\\System32") is False


def test_validate_filename_null_bytes():
    """Filenames containing null bytes are rejected."""
    assert validate_filename("file\x00.txt") is False
    assert validate_filename("\x00malicious.sh") is False


def test_validate_filename_empty():
    """Empty or whitespace-only filenames are rejected."""
    assert validate_filename("") is False
    assert validate_filename("   ") is False
    assert validate_filename("\t\n") is False


def test_sanitize_filename():
    """Dangerous characters and traversal elements are stripped."""
    assert sanitize_filename("safe_file.txt") == "safe_file.txt"
    # Strips path traversal
    sanitized = sanitize_filename("../../../etc/passwd")
    assert ".." not in sanitized
    assert "/" not in sanitized
    # Strips special characters
    assert sanitize_filename("bad<name>:|?*$.txt") == "badname.txt"
    # Strips leading and trailing dots/spaces/dashes
    assert sanitize_filename("..hidden..") == "hidden"
    # Empty result falls back to unnamed_file
    assert sanitize_filename("") == "unnamed_file"
    assert sanitize_filename("../..") == "unnamed_file"


def test_validate_file_path_inside(tmp_path: Path):
    """File path residing strictly within allowed directory passes."""
    allowed_dir = tmp_path / "shared"
    allowed_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = allowed_dir / "valid_file.txt"
    file_path.write_text("content")

    assert validate_file_path(file_path, allowed_dir) is True
    assert validate_file_path(allowed_dir / "subdir" / "nested.txt", allowed_dir) is True


def test_validate_file_path_outside(tmp_path: Path):
    """File path resolving outside allowed directory is rejected."""
    allowed_dir = tmp_path / "shared"
    allowed_dir.mkdir(parents=True, exist_ok=True)
    outside_dir = tmp_path / "private"
    outside_dir.mkdir(parents=True, exist_ok=True)

    outside_file = outside_dir / "secret.txt"
    outside_file.write_text("confidential")

    assert validate_file_path(outside_file, allowed_dir) is False
    assert validate_file_path(allowed_dir / ".." / "private" / "secret.txt", allowed_dir) is False


def test_validate_file_id_valid():
    """64-character hexadecimal SHA-256 strings pass validation."""
    valid_hash = "a1b2c3d4e5f60718293a4b5c6d7e8f901234567890abcdef1234567890abcdef"
    assert validate_file_id(valid_hash) is True
    assert validate_file_id("0" * 64) is True
    assert validate_file_id("abcdef0123456789" * 4) is True


def test_validate_file_id_invalid():
    """Non-hex or wrong-length identifiers are rejected."""
    assert validate_file_id("short_string") is False
    assert validate_file_id("a" * 63) is False
    assert validate_file_id("a" * 65) is False
    assert validate_file_id("g" * 64) is False  # Non-hex char
    assert validate_file_id("") is False
    assert validate_file_id("a1b2c3d4e5f60718293a4b5c6d7e8f901234567890abcdef1234567890abcde!") is False


def test_check_path_traversal():
    """Various traversal patterns are correctly detected."""
    # Traversal patterns should return True (traversal detected)
    assert check_path_traversal("../etc/passwd") is True
    assert check_path_traversal("..\\Windows") is True
    assert check_path_traversal("/absolute/path") is True
    assert check_path_traversal("\\absolute\\path") is True
    assert check_path_traversal("file\x00traversal") is True
    assert check_path_traversal("normal/../parent") is True

    # Safe relative names should return False (no traversal detected)
    assert check_path_traversal("safe_file.txt") is False
    assert check_path_traversal("folder/subfolder/file.dat") is False
