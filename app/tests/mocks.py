"""Mock data for testing."""

from datetime import datetime
from typing import Any, Dict

from ..schemas import ActionType

# Test email data
SAMPLE_EMAIL: Dict[str, Any] = {
    "id": 1,
    "message_id": "test123",
    "sender": "boss@example.com",
    "subject": "URGENT: Meeting Now",
    "date_received": datetime.now(),
    "snippet": "Please join the meeting",
    "folder": "Inbox",
    "is_read": False,
}

# Test rules data
SAMPLE_RULES_JSON = {
    "rules": [
        {
            "predicate": "all",
            "conditions": [
                {"field": "subject", "contains": "URGENT"},
                {"field": "sender", "contains": "boss@example.com"},
            ],
            "actions": [
                {"action": ActionType.MARK_READ},
                {"action": ActionType.MOVE, "folder": "Important/Urgent"},
            ],
        },
        {
            "predicate": "all",
            "conditions": [
                {"field": "date_received", "predicate": "is_less_than", "value": "7"}
            ],
            "actions": [
                {"action": ActionType.MOVE, "folder": "Old Emails"},
            ],
        },
        {
            "predicate": "any",
            "conditions": [
                {
                    "field": "date_received",
                    "predicate": "is_greater_than",
                    "value": "1",
                },
                {"field": "subject", "contains": "Important"},
            ],
            "actions": [
                {"action": ActionType.MARK_READ},
                {"action": ActionType.MOVE, "folder": "Immediate Attention"},
            ],
        },
        {
            "predicate": "all",
            "conditions": [{"field": "sender", "contains": "notifications@github.com"}],
            "actions": [
                {"action": ActionType.MOVE, "folder": "GitHub"},
            ],
        },
    ]
}
