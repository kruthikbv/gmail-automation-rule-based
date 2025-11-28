# tests/test_rule_engine.py
from unittest.mock import MagicMock
from process_rules import process_all
import json
from pathlib import Path


def test_full_rule_match_and_action(tmp_path):
    # --- Create temporary rules.json ---
    rules = {
        "rules": [
            {
                "id": "test_rule",
                "collection_predicate": "all",
                "conditions": [
                    {"field": "subject", "predicate": "contains", "value": "assignment"}
                ],
                "actions": ["mark_unread"]
            }
        ]
    }

    rules_file = tmp_path / "rules.json"
    rules_file.write_text(json.dumps(rules))

    # --- Mock DB ---
    fake_emails = [
        {"id": "MSG1", "subject": "HappyFox Assignment", "body": "", "date_received": ""}
    ]

    # Patch fetch_all_emails()
    import process_rules
    process_rules.fetch_all_emails = lambda: fake_emails

    # --- Mock Gmail service ---
    fake_service = MagicMock()
    fake_service.users().messages().get().execute.return_value = {"labelIds": []}

    process_rules.get_service = lambda: fake_service

    # --- Run engine ---
    process_rules.process_all(str(rules_file))

    # Expect modify called
    assert fake_service.users().messages().modify.called