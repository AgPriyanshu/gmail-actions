from typing import Optional, TypedDict


class EmailDict(TypedDict, total=False):
    """TypedDict for representing an email record from the database.

    Attributes:
        id: Database primary key
        message_id: Gmail's unique message ID
        sender: Email sender address
        subject: Email subject line
        date_received: Email sent date
        snippet: Short preview of email content
    """

    id: int
    message_id: str
    sender: Optional[str]
    subject: Optional[str]
    date_received: Optional[str]
    snippet: Optional[str]
