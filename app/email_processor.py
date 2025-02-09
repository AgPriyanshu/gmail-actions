import argparse
import json
import os
from typing import Any, Dict, List, Optional

from tabulate import tabulate

from .constants import DEFAULT_RULES_PATH, DEFAULT_USER
from .db.database import init_db
from .db.queries import (
    get_all_emails,
    insert_email,
    update_email_folder,
    update_email_read_status,
)
from .gmail_manager import GmailManager
from .schemas import ActionType, PredicateType, Rule, RuleAction, RuleCondition, Rules


def fetch_and_store_emails(user_email: str = DEFAULT_USER) -> None:
    """Fetch emails from Gmail and store them in the SQLite database."""
    print("\n📥 Fetching emails from Gmail...\n")

    # Use GmailManager to fetch emails
    email_messages = GmailManager.fetch_emails(user_email=user_email)

    if not email_messages:
        print("ℹ️  No new messages found.")
        return

    init_db()
    for email in email_messages:
        msg_id = email["message_id"]
        sender = email["sender"]
        subject = email["subject"]
        date = email["date"]
        snippet = email["snippet"]
        folder = email.get("folder", "INBOX")
        is_read = email.get("is_read", False)

        if insert_email(msg_id, sender, subject, date, snippet, folder, is_read):
            print("✅ Stored new email:")
            print(f"   From: {sender}")
            print(f"   Subject: {subject}")
            print(f"   Date: {date}")
            print(f"   Folder: {folder}")
            print(f"   Read: {'Yes' if is_read else 'No'}")
            print("   ----------------------")
        else:
            print("ℹ️  Email already exists:")
            print(f"   Subject: {subject}")
            print("   ----------------------")


def load_rules(rules_file: str = DEFAULT_RULES_PATH) -> List[Rule]:
    """Load processing rules from the JSON file."""
    if not os.path.exists(rules_file):
        print(f"No rules file found: {rules_file}")
        return []
    with open(rules_file) as f:
        rules_dict = json.load(f)
    return Rules.model_validate(rules_dict).rules


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
    for cond in conditions:
        field: str = cond.field
        # Check for a substring match on the specified field.
        value: Optional[str] = cond.value or cond.contains
        email_value: str = email.get(field, "")
        if email_value and value and value.lower() in email_value.lower():
            results.append(True)
        else:
            results.append(False)

    if predicate == PredicateType.ALL.value:
        return all(results)
    elif predicate == PredicateType.ANY.value:
        return any(results)
    return all(results)


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


def process_emails() -> None:
    """Load emails from the database, apply rules, and take the defined actions."""
    emails = get_all_emails()
    rules: List[Rule] = load_rules()

    if not rules:
        print("ℹ️  No rules to process.")
        return

    print("\n📧 Processing emails...\n")

    # Print all rules first
    print("📋 Current Rules:")
    for i, rule in enumerate(rules, 1):
        print(f"\nRule {i}:")
        print(f"   Predicate: {rule.predicate.upper()}")
        print("   Conditions:")
        for condition in rule.conditions:
            print(f"   - {condition.field} contains '{condition.contains}'")
        print("   Actions:")
        for action in rule.actions:
            if action.action == ActionType.MARK_READ:
                print("   - Mark as read")
            elif action.action == ActionType.MARK_UNREAD:
                print("   - Move to unread")
            elif action.action == ActionType.MOVE:
                print(f"   - Move to folder: {action.folder}")
    print("\n" + "=" * 50 + "\n")

    rules_matched = False
    for email in emails:
        subject = email.get("subject", "No Subject")
        sender = email.get("sender", "No Sender")
        print(f"📨 Checking email: '{subject}' from {sender}")

        for i, rule in enumerate(rules, 1):
            if email_matches_rule(email, rule):
                rules_matched = True
                print(f"\n✅ Rule {i} matched:")
                print(f"   Subject: {subject}")
                print("   Rule conditions:")
                for condition in rule.conditions:
                    print(f"   - {condition.field} contains '{condition.contains}'")
                print("\n   Performing actions:")
                perform_actions(email, rule.actions)
                print("   ----------------------")

    if not rules_matched:
        print("\nℹ️  No rules matched with any email")


def display_emails(limit: int = 10) -> None:
    """Display emails in a formatted table.

    Args:
        limit: Maximum number of emails to display
    """
    emails = get_all_emails()
    if not emails:
        print("No emails found in database.")
        return

    # Prepare data for tabulation
    headers = ["ID", "From", "Subject", "Date", "Folder", "Read"]
    table_data = [
        [
            email["id"],
            email["sender"][:30] + "..."
            if email["sender"] and len(email["sender"]) > 30
            else email["sender"],
            email["subject"][:40] + "..."
            if email["subject"] and len(email["subject"]) > 40
            else email["subject"],
            email["date"],
            email["folder"],
            "✓" if email["is_read"] else "✗",
        ]
        for email in emails[:limit]
    ]

    print("\n📧 Recent Emails:\n")
    print(tabulate(table_data, headers=headers, tablefmt="grid"))
    print(f"\nShowing {min(len(emails), limit)} of {len(emails)} emails")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gmail Email Processor")
    parser.add_argument(
        "--mode",
        choices=["fetch", "process", "display"],
        required=True,
        help=(
            'Mode to run: "fetch" to retrieve emails, '
            '"process" to process emails, "display" to show emails'
        ),
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Number of emails to display (default: 10)",
    )
    args = parser.parse_args()

    if args.mode == "fetch":
        user_email: str = input("Enter your email address for Gmail OAuth: ").strip()
        if not user_email:
            print("No email entered; using default 'me'")
            user_email = "me"
        fetch_and_store_emails(user_email)
    elif args.mode == "process":
        process_emails()
    elif args.mode == "display":
        display_emails(args.limit)
