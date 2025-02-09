import json
from pathlib import Path
from unittest.mock import patch

import pytest

from ..db.database import Database, init_db
from ..email_processor import (
    Rule,
    RuleAction,
    display_emails,
    email_matches_rule,
    load_rules,
    perform_actions,
)
from ..schemas import ActionType, PredicateType
from .mocks import SAMPLE_EMAIL, SAMPLE_RULES_JSON


class TestEmailProcessor:
    # Fixtures
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        """Setup test database for each test."""
        self.test_database_path = str(tmp_path / "test.db")
        self.database_connection = init_db(self.test_database_path)
        yield
        self.database_connection.close()

    @pytest.fixture
    def sample_emails(self):
        """Insert sample emails into test database."""
        cursor = self.database_connection.cursor()
        emails = [
            (
                "msg1",
                "sender1@test.com",
                "Test Subject 1",
                "2024-03-15",
                "Snippet 1",
                "INBOX",
                0,
            ),
            (
                "msg2",
                "sender2@test.com",
                "Test Subject 2",
                "2024-03-16",
                "Snippet 2",
                "Archive",
                1,
            ),
            (
                "msg3",
                "sender3@test.com",
                "Test Subject 3",
                "2024-03-17",
                "Snippet 3",
                "INBOX",
                0,
            ),
        ]
        cursor.executemany(
            """
            INSERT INTO emails
            (message_id, sender, subject, date, snippet, folder, is_read)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            emails,
        )
        self.database_connection.commit()
        return emails

    @pytest.fixture
    def sample_rules(self, tmp_path: Path) -> str:
        """Create a temporary rules.json file for testing.

        Args:
            tmp_path: Pytest fixture providing temporary directory path

        Returns:
            str: Path to the temporary rules file
        """
        rules_file = tmp_path / "test_rules.json"
        with open(rules_file, "w") as f:
            json.dump(SAMPLE_RULES_JSON, f)
        return str(rules_file)

    # Tests
    def test_init_db(self):
        """Test database initialization."""
        cursor = self.database_connection.cursor()
        cursor.execute(
            """
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='emails'
        """
        )
        assert cursor.fetchone() is not None

    def test_load_rules(self, sample_rules):
        """Test loading rules from JSON file."""
        loaded_rules = load_rules(sample_rules)
        assert len(loaded_rules) == 1
        assert loaded_rules[0].predicate == PredicateType.ALL.value
        assert len(loaded_rules[0].conditions) == 2
        assert len(loaded_rules[0].actions) == 2

    def test_email_matches_rule(self):
        """Test rule matching logic."""
        test_rule_dict = SAMPLE_RULES_JSON["rules"][0]
        test_rule = Rule.model_validate(test_rule_dict)

        assert email_matches_rule(SAMPLE_EMAIL, test_rule) is True

        non_matching_email = SAMPLE_EMAIL.copy()
        non_matching_email["subject"] = "Regular meeting"
        assert email_matches_rule(non_matching_email, test_rule) is False

    @patch("app.email_processor.update_email_folder")
    @patch("app.email_processor.update_email_read_status")
    def test_perform_actions(self, mock_update_read, mock_update_folder, capsys):
        """Test action performance with mocked database calls."""
        test_actions = [
            RuleAction(action=ActionType.MARK_READ),
            RuleAction(action=ActionType.MOVE, folder="Important/Urgent"),
        ]

        perform_actions(SAMPLE_EMAIL, test_actions)
        captured_output = capsys.readouterr()

        # Verify output messages
        assert "Marking email test123 as read" in captured_output.out
        assert (
            "Moving email test123 to folder 'Important/Urgent'" in captured_output.out
        )

        # Verify mock calls
        mock_update_read.assert_called_once_with(SAMPLE_EMAIL["message_id"], True)
        mock_update_folder.assert_called_once_with(
            SAMPLE_EMAIL["message_id"], "Important/Urgent"
        )

    @patch("app.email_processor.update_email_folder")
    def test_move_action_without_folder(self, mock_update_folder, capsys):
        """Test move action without specified folder."""
        test_actions = [RuleAction(action=ActionType.MOVE)]

        perform_actions(SAMPLE_EMAIL, test_actions)
        captured_output = capsys.readouterr()

        assert "No folder specified for move action" in captured_output.out
        mock_update_folder.assert_not_called()

    def test_email_matches_rule_with_or_predicate(self):
        """Test 'or' predicate in rule matching."""
        or_rule_dict = {
            "predicate": "any",
            "conditions": [
                {"field": "subject", "contains": "urgent"},
                {"field": "subject", "contains": "important"},
            ],
            "actions": [],
        }
        or_rule = Rule.model_validate(or_rule_dict)

        assert email_matches_rule(SAMPLE_EMAIL, or_rule) is True

        important_email = SAMPLE_EMAIL.copy()
        important_email["subject"] = "IMPORTANT: Another meeting"
        assert email_matches_rule(important_email, or_rule) is True

        regular_email = important_email.copy()
        regular_email["subject"] = "Regular meeting"
        assert email_matches_rule(regular_email, or_rule) is False

    @patch("app.email_processor.update_email_read_status")
    def test_mark_read_action(self, mock_update_read):
        """Test marking email as read with mocked database call."""
        test_actions = [RuleAction(action=ActionType.MARK_READ)]
        perform_actions(SAMPLE_EMAIL, test_actions)

        mock_update_read.assert_called_once_with(SAMPLE_EMAIL["message_id"], True)

    @patch("app.email_processor.update_email_folder")
    def test_update_folder_action(self, mock_update_folder):
        """Test updating email folder with mocked database call."""
        test_actions = [RuleAction(action=ActionType.MOVE, folder="Archive")]
        perform_actions(SAMPLE_EMAIL, test_actions)

        mock_update_folder.assert_called_once_with(
            SAMPLE_EMAIL["message_id"], "Archive"
        )

    def test_display_emails_with_data(self, capsys, sample_emails):
        """Test displaying emails when data exists."""
        with patch.object(Database, "__enter__", return_value=self.database_connection):
            display_emails(limit=2)
            captured = capsys.readouterr()

            # Check if headers are present
            assert "ID" in captured.out
            assert "From" in captured.out
            assert "Subject" in captured.out
            assert "Date" in captured.out
            assert "Folder" in captured.out
            assert "Read" in captured.out

            # Check if email data is present
            assert "sender1@test.com" in captured.out
            assert "Test Subject 1" in captured.out
            assert "INBOX" in captured.out
            assert "✗" in captured.out  # Unread email

            # Check if limit works
            assert "sender3@test.com" not in captured.out
            assert "Showing 2 of 3 emails" in captured.out

    def test_display_emails_empty_db(self, capsys):
        """Test displaying emails with empty database."""
        cursor = self.database_connection.cursor()
        cursor.execute("DELETE FROM emails")
        self.database_connection.commit()
        with patch.object(Database, "__enter__", return_value=self.database_connection):
            display_emails()
            captured = capsys.readouterr()
            assert "No emails found in database." in captured.out

    def test_display_emails_long_fields(self, capsys):
        """Test displaying emails with long sender/subject fields."""
        cursor = self.database_connection.cursor()
        long_email = (
            "msg4",
            "very.long.email.address.that.should.be.truncated@really.long.domain.com",
            "This is a very long subject line that should be truncated in the display",
            "2024-03-18",
            "Snippet 4",
            "INBOX",
            0,
        )
        cursor.execute(
            """
            INSERT INTO emails
            (message_id, sender, subject, date, snippet, folder, is_read)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            long_email,
        )
        self.database_connection.commit()
        with patch.object(Database, "__enter__", return_value=self.database_connection):
            display_emails()
        captured = capsys.readouterr()

        # Check if long fields are truncated
        assert "..." in captured.out
        assert len(max(captured.out.split("\n"), key=len)) < 200  # Check line length
