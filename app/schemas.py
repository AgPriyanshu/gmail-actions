from enum import StrEnum
from typing import List, Optional

from pydantic import BaseModel


class EmailModel(BaseModel):
    """Pydantic Model for email validation and serialization."""

    id: Optional[int]
    message_id: str
    sender: Optional[str]
    subject: Optional[str]
    date_received: Optional[str]
    snippet: Optional[str]
    raw: str
    folder: str = "INBOX"  # Default folder
    is_read: bool = False  # Default read status


class RuleCondition(BaseModel):
    """Pydantic Model for a single rule condition."""

    field: str
    contains: Optional[str] = None
    value: Optional[str] = None
    predicate: Optional[str] = None


class ActionType(StrEnum):
    """Enum for supported email actions.

    Supported actions:
        MOVE: Move the email to a specified folder
        MARK_READ: Mark the email as read
        MARK_UNREAD: Mark the email as unread
    """

    MOVE = "move"
    MARK_READ = "mark_as_read"
    MARK_UNREAD = "mark_as_unread"


class RuleAction(BaseModel):
    """Pydantic Model for a single rule action.

    Attributes:
        action: Type of action to perform (from ActionType enum)
        folder: Optional folder/label name for move action
    """

    action: ActionType
    folder: Optional[str] = None


class PredicateType(StrEnum):
    """Enum for predicate types.

    Supported predicates:
        ALL: All conditions must be met
        ANY: Any condition must be met
    """

    ALL = "all"
    ANY = "any"


class Rule(BaseModel):
    """Pydantic Model for a complete rule with conditions and actions."""

    predicate: PredicateType
    conditions: List[RuleCondition]
    actions: List[RuleAction]


class Rules(BaseModel):
    """Pydantic Model for multiple rules."""

    rules: List[Rule]
