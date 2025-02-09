import os
import pickle
from typing import Any, Dict, List, Optional

from google.auth.transport.requests import Request  # type: ignore
from google_auth_oauthlib.flow import InstalledAppFlow  # type: ignore
from googleapiclient.discovery import build  # type: ignore

from .constants import CREDENTIALS_PATH, GMAIL_SCOPES, TOKEN_PATH


class GmailManager:
    """Manages Gmail API operations and authentication.

    This class handles OAuth2 authentication with Gmail and provides methods
    to fetch and process emails from the user's inbox.

    Class Attributes:
        _service: Authenticated Gmail API service instance
    """

    _service: Optional[Any] = None

    @classmethod
    def _authenticate(cls) -> Any:
        """Authenticate with Gmail and return a Gmail API service instance.

        Handles the OAuth2 flow:
        1. Checks for existing token
        2. Refreshes expired token
        3. Creates new token if none exists
        4. Saves token for future use

        Returns:
            An authenticated Gmail API service instance

        Note:
            Requires credentials.json file from Google Cloud Console
        """
        credentials = None
        if os.path.exists(TOKEN_PATH):
            with open(TOKEN_PATH, "rb") as token:
                credentials = pickle.load(token)

        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    CREDENTIALS_PATH, GMAIL_SCOPES
                )
                credentials = flow.run_local_server(port=0)

            with open(TOKEN_PATH, "wb") as token:
                pickle.dump(credentials, token)

        return build("gmail", "v1", credentials=credentials)

    @classmethod
    def get_service(cls) -> Any:
        """Get or create the Gmail API service instance.

        Returns:
            An authenticated Gmail API service instance
        """
        if cls._service is None:
            cls._service = cls._authenticate()
        return cls._service

    @classmethod
    def fetch_emails(
        cls, user_email: str = "me", max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """Fetch emails from Gmail inbox.

        Retrieves emails from the user's inbox and processes them into a
        standardized format with headers and content.

        Args:
            user_email: Gmail user email address or 'me' for authenticated user
            max_results: Maximum number of emails to fetch

        Returns:
            List of dictionaries containing email details:
            {
                'message_id': str,
                'sender': str,
                'subject': str,
                'date': str,
                'snippet': str,
            }
        """
        service = cls.get_service()
        results = (
            service.users()
            .messages()
            .list(userId=user_email, labelIds=["INBOX"], maxResults=max_results)
            .execute()
        )

        messages = results.get("messages", [])
        if not messages:
            return []

        email_messages = []
        for message in messages:
            msg = cls._get_email_details(message["id"], user_email)
            if msg:
                email_messages.append(msg)

        return email_messages

    @classmethod
    def _get_email_details(
        cls, message_id: str, user_email: str = "me"
    ) -> Optional[Dict[str, Any]]:
        """Get detailed information for a specific email.

        Fetches and processes the full email content, including headers
        and message body.

        Args:
            message_id: Gmail message ID
            user_email: Gmail user email address

        Returns:
            Dictionary containing email details or None if retrieval fails:
            {
                'message_id': str,
                'sender': str,
                'subject': str,
                'date': str,
                'snippet': str,
            }

        """
        try:
            service = cls.get_service()
            msg = (
                service.users()
                .messages()
                .get(userId=user_email, id=message_id, format="full")
                .execute()
            )

            headers = msg["payload"].get("headers", [])
            email_data = {
                "message_id": message_id,
                "sender": None,
                "subject": None,
                "date": None,
                "snippet": msg.get("snippet"),
            }

            for header in headers:
                header_name = header["name"].lower()
                if header_name == "subject":
                    email_data["subject"] = header["value"]
                elif header_name == "from":
                    email_data["sender"] = header["value"]
                elif header_name == "date":
                    email_data["date"] = header["value"]

            return email_data
        except Exception as e:
            print(f"Error fetching email {message_id}: {e}")
            return None
