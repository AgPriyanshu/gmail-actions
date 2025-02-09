import sqlite3
from typing import Any, Dict, List, Optional

from .database import Database


def insert_email(
    message_id: str,
    sender: Optional[str],
    subject: Optional[str],
    date: Optional[str],
    snippet: Optional[str],
    folder: str = "INBOX",
    is_read: bool = False,
) -> bool:
    """Insert a new email into the database."""
    with Database() as conn:
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO emails
                (message_id, sender, subject, date, snippet, folder, is_read)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    message_id,
                    sender,
                    subject,
                    date,
                    snippet,
                    folder,
                    1 if is_read else 0,
                ),
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False


def get_all_emails() -> List[Dict[str, Any]]:
    """Retrieve all emails from the database."""
    with Database() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, message_id, sender, subject, date, snippet, folder, is_read
            FROM emails
            """
        )
        rows = cursor.fetchall()
        return [
            {
                "id": row[0],
                "message_id": row[1],
                "sender": row[2],
                "subject": row[3],
                "date": row[4],
                "snippet": row[5],
                "folder": row[6],
                "is_read": bool(row[7]),
            }
            for row in rows
        ]


def update_email_folder(message_id: str, folder: str) -> bool:
    """
    Update the folder of an email in the database.

    Args:
        message_id: The unique message ID of the email
        folder: The new folder name

    Returns:
        bool: True if update was successful, False otherwise
    """
    with Database() as conn:
        try:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE emails SET folder = ? WHERE message_id = ?",
                (folder, message_id),
            )
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Error updating email folder: {e}")
            return False


def update_email_read_status(message_id: str, is_read: bool) -> bool:
    """
    Update the read status of an email in the database.

    Args:
        message_id: The unique message ID of the email
        is_read: True to mark as read, False to mark as unread

    Returns:
        bool: True if update was successful, False otherwise
    """
    with Database() as conn:
        try:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE emails SET is_read = ? WHERE message_id = ?",
                (1 if is_read else 0, message_id),
            )
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Error updating email read status: {e}")
            return False
