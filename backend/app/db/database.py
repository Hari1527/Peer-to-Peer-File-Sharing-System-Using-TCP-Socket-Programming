"""SQLite database management for the tracker service."""

import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path


class TrackerDatabase:
    """Manages SQLite database connections, schema setup, and transactions."""

    def __init__(self, db_path: str = "tracker.db") -> None:
        self.db_path = db_path
        # Ensure parent directory exists if specified in db_path
        parent = Path(db_path).parent
        if parent and not parent.exists():
            parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Provide a transactional SQLite connection context manager.

        Configures foreign keys, row factory, and handles commit/rollback.
        """
        conn = sqlite3.connect(self.db_path, check_same_thread=False, timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def initialize(self) -> None:
        """Create tables and indexes if they do not exist."""
        with self.get_connection() as conn:
            conn.execute("PRAGMA journal_mode = WAL;")

            conn.execute("""
                CREATE TABLE IF NOT EXISTS peers (
                    peer_id TEXT PRIMARY KEY,
                    host TEXT NOT NULL,
                    tcp_port INTEGER NOT NULL,
                    api_port INTEGER NOT NULL,
                    status TEXT DEFAULT 'online',
                    last_seen TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS shared_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_id TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    size INTEGER NOT NULL,
                    checksum TEXT NOT NULL,
                    peer_id TEXT NOT NULL REFERENCES peers(peer_id) ON DELETE CASCADE,
                    shared_at TEXT NOT NULL,
                    UNIQUE(file_id, peer_id)
                );
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS transfers (
                    transfer_id TEXT PRIMARY KEY,
                    file_id TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    source_peer_id TEXT NOT NULL,
                    dest_peer_id TEXT NOT NULL,
                    direction TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    bytes_transferred INTEGER DEFAULT 0,
                    total_bytes INTEGER DEFAULT 0,
                    started_at TEXT NOT NULL,
                    completed_at TEXT,
                    error_message TEXT
                );
            """)

            conn.execute("CREATE INDEX IF NOT EXISTS idx_shared_files_peer ON shared_files(peer_id);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_shared_files_name ON shared_files(filename);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_transfers_status ON transfers(status);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_transfers_source ON transfers(source_peer_id);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_transfers_dest ON transfers(dest_peer_id);")
