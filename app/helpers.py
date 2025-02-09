import json
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from .constants import DEFAULT_RULES_PATH
from .db.queries import (
    update_email_folder,
    update_email_read_status,
)
from .schemas import ActionType, PredicateType, Rule, RuleAction, RuleCondition, Rules


def load_rules(rules_file: str = DEFAULT_RULES_PATH) -> List[Rule]:
    """Load processing rules from the JSON file."""
    if not os.path.exists(rules_file):
        print(f"No rules file found: {rules_file}")
        return []
    with open(rules_file) as f:
        rules_dict = json.load(f)
    return Rules.model_validate(rules_dict).rules


def parse_date_condition(email_date: datetime, condition: RuleCondition) -> bool:
    """Check if an email's received date satisfies the condition."""
    if email_date.tzinfo is None:
        email_date = email_date.astimezone()

    now = datetime.now().astimezone()
    compare_date = now - timedelta(days=int(condition.value))

    if condition.predicate == "is_less_than":
        return email_date < compare_date
    elif condition.predicate == "is_greater_than":
        return email_date > compare_date

    return False


def email_matches_rule(email: Dict[str, Any], rule: Rule) -> bool:
    """
    Determine if an email matches a rule.

    Rule format example:
      {
        "predicate": "and",
        "conditions": [
            {"field": "subject", "contains": "urgent"},
            {"field": "sender", "contains": "boss@example.com"}
        ],
        "actions": [ ... ]
      }
    """
    predicate: str = rule.predicate
    conditions: List[RuleCondition] = rule.conditions

    results: List[bool] = []
    for condition in conditions:
        field: str = condition.field
        value: Optional[str] = condition.value or condition.contains
        email_value = email.get(field, "")

        if field == "date_received" and value:
            results.append(parse_date_condition(email_value, condition))
        elif email_value and value and value.lower() in email_value.lower():
            results.append(True)
        else:
            results.append(False)

    return all(results) if predicate == PredicateType.ALL.value else any(results)


def perform_actions(email: dict, actions: List[RuleAction]) -> None:
    """Perform the specified actions on an email."""
    for action in actions:
        if action.action == ActionType.MOVE:
            if not action.folder:
                print("No folder specified for move action")
                continue
            print(f"Moving email {email['message_id']} to folder '{action.folder}'")
            update_email_folder(email["message_id"], action.folder)

        elif action.action == ActionType.MARK_READ:
            print(f"Marking email {email['message_id']} as read")
            update_email_read_status(email["message_id"], True)

        elif action.action == ActionType.MARK_UNREAD:
            print(f"Marking email {email['message_id']} as unread")
            update_email_read_status(email["message_id"], False)
