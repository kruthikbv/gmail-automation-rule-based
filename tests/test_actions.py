# tests/test_actions.py
from unittest.mock import MagicMock
from process_rules import apply_action


def make_fake_msg(label_ids):
    return {"labelIds": label_ids}


def test_mark_unread():
    service = MagicMock()
    service.users().messages().get().execute.return_value = make_fake_msg([])
    label_map = {}

    apply_action(service, "123", "mark_unread", label_map)

    service.users().messages().modify.assert_called()


def test_mark_read():
    service = MagicMock()
    service.users().messages().get().execute.return_value = make_fake_msg(["UNREAD"])
    label_map = {}

    apply_action(service, "123", "mark_read", label_map)
    service.users().messages().modify.assert_called()


def test_move_message():
    service = MagicMock()
    service.users().messages().get().execute.return_value = make_fake_msg(["INBOX"])
    service.users().labels().create().execute.return_value = {"id": "LBL1"}

    label_map = {}

    apply_action(service, "123", "move_message:TEST_LABEL", label_map)

    service.users().messages().modify.assert_called()


def test_move_message_keep_inbox():
    service = MagicMock()
    service.users().messages().get().execute.return_value = make_fake_msg(["INBOX"])
    service.users().labels().create().execute.return_value = {"id": "LBL2"}

    label_map = {}

    apply_action(service, "123", "move_message_keep_inbox:TEST_LABEL", label_map)
    service.users().messages().modify.assert_called()