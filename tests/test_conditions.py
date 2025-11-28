# tests/test_conditions.py
from process_rules import evaluate_condition


def test_condition_subject_contains():
    email = {"subject": "HappyFox Assignment", "body": ""}
    cond = {
        "field": "subject",
        "predicate": "contains",
        "value": "assignment"
    }
    assert evaluate_condition(email, cond) is True


def test_all_conditions_match():
    email = {
        "from_email": "kruthikbv4@gmail.com",
        "subject": "HappyFox Assignment",
        "body": "please finish this",
        "date_received": "Wed, 20 Nov 2024 10:00:00 +0530"
    }

    conditions = [
        {"field": "from_email", "predicate": "contains", "value": "gmail.com"},
        {"field": "subject", "predicate": "contains", "value": "assignment"},
        {"field": "message", "predicate": "contains", "value": "finish"}
    ]

    results = [evaluate_condition(email, c) for c in conditions]
    assert all(results) is True


def test_any_conditions_match():
    email = {
        "subject": "Scheduled Interview Tomorrow",
        "body": "Please join Google Meet"
    }

    conditions = [
        {"field": "subject", "predicate": "contains", "value": "interview"},
        {"field": "message", "predicate": "contains", "value": "zoom"}
    ]

    results = [evaluate_condition(email, c) for c in conditions]
    assert any(results) is True
