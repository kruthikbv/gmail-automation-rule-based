# tests/test_predicates.py
import pytest
from datetime import datetime, timedelta, timezone
from process_rules import parse_email_date, eval_string, eval_date


def test_contains():
    assert eval_string("Hello World", "contains", "world") is True


def test_not_contains():
    assert eval_string("Hello", "not_contains", "xyz") is True


def test_equals():
    assert eval_string("Test", "equals", "test") is True


def test_not_equals():
    assert eval_string("ABC", "not_equals", "xyz") is True


def test_older_than_days():
    # email 10 days old
    email_dt = datetime.now(timezone.utc) - timedelta(days=10)
    assert eval_date(email_dt, "older_than_days", 5) is True   # older than 5 days


def test_newer_than_days():
    # email 1 day old
    email_dt = datetime.now(timezone.utc) - timedelta(days=1)
    assert eval_date(email_dt, "newer_than_days", 3) is False
    assert eval_date(email_dt, "newer_than_days", 0) is True

