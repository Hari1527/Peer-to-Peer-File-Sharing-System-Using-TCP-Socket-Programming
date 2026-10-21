"""Local file indexing and SHA-256 metadata extraction."""

import logging
from pathlib import Path
import threading
from typing import Any

from ..utils.hashing import compute_file_sha256

logger = logging.getLogger("p2p.file_index")


class FileIndex:
    """Maintains an index of files available in the shared directory."""

    def __init__(self, shared_dir: str | Path, max_file_size: int = 1_073_741_824) -> None:
        self.shared_dir = Path(shared_dir).resolve()
        self.max_file_size = max_file_size
        self._lock = threading.Lock()
        self._files: dict[str, dict[str, Any]] = {}

        # Ensure directory exists
        if not self.shared_dir.exists():
            self.shared_dir.mkdir(parents=True, exist_ok=True)

        self.scan()

    def scan(self) -> list[dict[str, Any]]:
        """Scan the shared directory, calculate SHA-256 checksums, and update index.

        Returns:
            List of file metadata dictionaries:
            [{"file_id": str, "filename": str, "size": int, "checksum": str}]
        """
        with self._lock:
            new_files: dict[str, dict[str, Any]] = {}
            result: list[dict[str, Any]] = []

            if not self.shared_dir.exists():
                self.shared_dir.mkdir(parents=True, exist_ok=True)

            for item in self.shared_dir.iterdir():
                # Skip hidden files
                if item.name.startswith("."):
                    continue

                # Only regular files
                if not item.is_file():
                    continue

                try:
                    stat = item.stat()
                    if stat.st_size > self.max_file_size:
                        logger.warning(
                            "Skipping file %s (size %d exceeds max %d)",
                            item.name,
                            stat.st_size,
                            self.max_file_size,
                        )
                        continue

                    checksum = compute_file_sha256(item)
                    file_id = checksum

                    file_data = {
                        "file_id": file_id,
                        "filename": item.name,
                        "size": stat.st_size,
                        "checksum": checksum,
                        "path": item,
                    }
                    new_files[file_id] = file_data
                    result.append(
                        {
                            "file_id": file_id,
                            "filename": item.name,
                            "size": stat.st_size,
                            "checksum": checksum,
                        }
                    )
                except Exception as e:
                    logger.error("Error processing file %s: %s", item.name, e)

            self._files = new_files
            return result

    def refresh(self) -> list[dict[str, Any]]:
        """Re-scan the shared directory and return updated file list."""
        return self.scan()

    def get_file_path(self, file_id: str) -> Path | None:
        """Retrieve local filesystem Path for a given file_id or checksum."""
        with self._lock:
            # Direct match
            if file_id in self._files:
                return self._files[file_id]["path"]
            # Case-insensitive match
            for fid, data in self._files.items():
                if fid.lower() == file_id.lower() or data["checksum"].lower() == file_id.lower():
                    return data["path"]
            return None

    def get_file_by_name(self, filename: str) -> dict[str, Any] | None:
        """Look up file metadata by filename."""
        with self._lock:
            for data in self._files.values():
                if data["filename"] == filename:
                    return {
                        "file_id": data["file_id"],
                        "filename": data["filename"],
                        "size": data["size"],
                        "checksum": data["checksum"],
                    }
            return None

    def has_file(self, file_id: str) -> bool:
        """Check if file exists in the index."""
        with self._lock:
            if file_id in self._files:
                return True
            for fid, data in self._files.items():
                if fid.lower() == file_id.lower() or data["checksum"].lower() == file_id.lower():
                    return True
            return False

    def get_all_files(self) -> list[dict[str, Any]]:
        """Return all indexed files without internal path references."""
        with self._lock:
            return [
                {
                    "file_id": data["file_id"],
                    "filename": data["filename"],
                    "size": data["size"],
                    "checksum": data["checksum"],
                }
                for data in self._files.values()
            ]
