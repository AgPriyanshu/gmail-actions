import sqlite3
from typing import Optional

from ..constants import DATABASE_NAME


class Database:
    """Database connection manager."""

    def __init__(self, db_name: str = DATABASE_NAME):
        self.db_name = db_name
        self.conn: Optional[sqlite3.Connection] = None

    def connect(self) -> sqlite3.Connection:
        """Create a database connection."""
        if not self.conn:
            self.conn = sqlite3.connect(self.db_name)
        return self.conn

    def close(self) -> None:
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def __enter__(self) -> sqlite3.Connection:
        """Context manager entry."""
        return self.connect()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()


def init_db(db_name: str = DATABASE_NAME) -> sqlite3.Connection:
    """Initialize the database and create required tables.

    Returns:
        sqlite3.Connection: The database connection
    """
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id TEXT UNIQUE,
            sender TEXT,
            subject TEXT,
            date TEXT,
            snippet TEXT,
            folder TEXT DEFAULT 'INBOX',
            is_read BOOLEAN DEFAULT 0
        )
    """
    )
    conn.commit()
    return conn
