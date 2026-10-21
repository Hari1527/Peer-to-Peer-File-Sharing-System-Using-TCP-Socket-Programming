"""Security utility module for the P2P file sharing system.

Provides validation and sanitization functions to prevent path traversal,
invalid identifiers, and unauthorized filesystem access.
"""

from pathlib import Path
import os
import re

# Compiled regex for 64-character hexadecimal SHA-256 strings
_HEX_64_PATTERN = re.compile(r"^[0-9a-fA-F]{64}$")

# Pattern for safe characters: alphanumeric, dash, underscore, dot, space
_SAFE_FILENAME_CHARS = re.compile(r"[^a-zA-Z0-9._ -]")


def validate_filename(filename: str) -> bool:
    """Validate that a filename is safe and does not contain traversal sequences.

    Rejects filenames that:
    - Are empty or whitespace-only
    - Contain '..' (directory traversal)
    - Start with '/' or '\\' (absolute path indicator)
    - Contain null bytes ('\\x00')

    Args:
        filename: The filename string to validate.

    Returns:
        bool: True if filename is valid and safe, False otherwise.
    """
    if not isinstance(filename, str):
        return False
    
    trimmed = filename.strip()
    if not trimmed:
        return False

    if "\x00" in filename:
        return False

    if ".." in filename:
        return False

    if filename.startswith("/") or filename.startswith("\\"):
        return False

    # Also reject any embedded directory separator
    if "/" in filename or "\\" in filename:
        return False

    return True


def sanitize_filename(filename: str) -> str:
    """Sanitize a filename by stripping dangerous characters.

    Keeps only alphanumeric characters, dashes, underscores, dots, and spaces.
    Ensures the resulting filename does not start with dots or contain path traversals.

    Args:
        filename: The original filename string.

    Returns:
        str: A sanitized, safe filename string.
    """
    if not isinstance(filename, str):
        return "unnamed_file"

    # Remove dangerous characters
    cleaned = _SAFE_FILENAME_CHARS.sub("", filename)

    # Remove any traversal patterns
    while ".." in cleaned:
        cleaned = cleaned.replace("..", "")

    # Strip leading/trailing dots, dashes, and spaces
    cleaned = cleaned.strip(". -")

    if not cleaned:
        return "unnamed_file"

    return cleaned


def validate_file_path(filepath: Path, allowed_dir: Path) -> bool:
    """Validate that a file path resides strictly within the allowed directory.

    Resolves both paths to their absolute canonical forms and verifies
    that filepath is contained within or equal to allowed_dir.

    Args:
        filepath: The path to check.
        allowed_dir: The root directory that filepath must be inside.

    Returns:
        bool: True if filepath is within allowed_dir, False otherwise.
    """
    try:
        resolved_file = Path(filepath).resolve()
        resolved_dir = Path(allowed_dir).resolve()
        return resolved_file == resolved_dir or resolved_file.is_relative_to(resolved_dir)
    except (ValueError, RuntimeError, OSError):
        return False


def validate_file_id(file_id: str) -> bool:
    """Validate that a file ID is a valid 64-character hex string (SHA-256).

    Args:
        file_id: The identifier string to validate.

    Returns:
        bool: True if file_id is a 64-character hex string, False otherwise.
    """
    if not isinstance(file_id, str):
        return False
    return bool(_HEX_64_PATTERN.fullmatch(file_id))


def check_path_traversal(path_str: str) -> bool:
    """Check if a path string contains directory traversal attempts.

    Detects '..', absolute paths (starting with '/' or '\\'), and null bytes.

    Args:
        path_str: The path string to test.

    Returns:
        bool: True if path traversal is detected, False if safe.
    """
    if not isinstance(path_str, str):
        return True

    if "\x00" in path_str:
        return True

    if ".." in path_str:
        return True

    if path_str.startswith("/") or path_str.startswith("\\"):
        return True

    normalized = os.path.normpath(path_str)
    if (
        normalized.startswith("/")
        or normalized.startswith("\\")
        or normalized.startswith("..")
        or "/.." in normalized
        or "\\.." in normalized
    ):
        return True

    return False
