"""Constants used throughout the application."""

from typing import List

# Database configuration
DATABASE_NAME: str = "emails.db"

# Gmail API configuration
GMAIL_SCOPES: List[str] = ["https://www.googleapis.com/auth/gmail.readonly"]

# File paths
CREDENTIALS_PATH: str = "config/credentials.json"
TOKEN_PATH: str = "token.pickle"
DEFAULT_RULES_PATH: str = "rules.json"

# Gmail API defaults
DEFAULT_USER: str = "me"
DEFAULT_MAX_RESULTS: int = 10
