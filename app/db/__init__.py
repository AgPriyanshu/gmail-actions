from .database import Database, init_db
from .queries import get_all_emails, insert_email

__all__ = ["Database", "init_db", "insert_email", "get_all_emails"]
