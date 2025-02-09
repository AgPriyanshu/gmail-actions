"""Mock data for testing."""

from typing import Any, Dict

from ..schemas import ActionType

# Test email data
SAMPLE_EMAIL: Dict[str, Any] = {
    "id": 1,
    "message_id": "test123",
    "sender": "boss@example.com",
    "subject": "URGENT: Meeting Now",
    "date": "2024-01-01",
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
                {
                    "action": ActionType.MOVE,
                    "folder": "Important/Urgent",
                },
            ],
        }
    ]
}
