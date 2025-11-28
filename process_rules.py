"""
process_rules.py

Supports:
- rules.json with "rules": [ ... ]
- Fields: from_email, subject, message, received_datetime
- String predicates: contains, not_contains, equals, not_equals
- Date predicates: older_than_days, newer_than_days, less_than_months, greater_than_months
- collection_predicate: "all" / "any"
- Actions:
      mark_read
      mark_unread
      move_message:<LabelName>
      move_message_keep_inbox:<LabelName>

Label names are automatically resolved to Gmail label IDs.
Missing labels are created on demand.
"""

import json
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

from auth import get_service
from db import fetch_all_emails


RULES_PATH = "rules.json"


# --------------------- DATE PARSER ---------------------
def parse_email_date(date_str):
    """Parse Gmail/DB date safely as timezone-aware datetime."""
    if not date_str:
        return None

    # Attempt RFC822 / Gmail header parsing
    try:
        dt = parsedate_to_datetime(date_str)
        if dt and dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        pass

    # ISO format fallback
    try:
        dt = datetime.fromisoformat(date_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        pass

    return None


# --------------------- LABEL HANDLING ---------------------
def build_label_map(service):
    """Returns dict mapping label_name → label_id."""
    result = {}
    resp = service.users().labels().list(userId="me").execute()
    for l in resp.get("labels", []):
        result[l["name"]] = l["id"]
    return result


def get_or_create_label(service, name, label_map):
    """Get label id; create label if missing."""
    if name in label_map:
        return label_map[name]

    body = {
        "name": name,
        "labelListVisibility": "labelShow",
        "messageListVisibility": "show",
    }
    created = service.users().labels().create(userId="me", body=body).execute()
    label_id = created["id"]
    label_map[name] = label_id
    print(f"Created label: {name} -> {label_id}")
    return label_id


# --------------------- PREDICATE EVALUATION ---------------------
def eval_string(field_text, pred, value):
    """String predicate evaluator."""
    t = (field_text or "").lower()
    v = (value or "").lower()

    if pred == "contains":
        return v in t
    if pred == "not_contains":
        return v not in t
    if pred == "equals":
        return t == v
    if pred == "not_equals":
        return t != v

    return False


def eval_date(email_dt, pred, value_int):
    """Evaluate date-based predicates using email age (now - email_dt)."""
    if not email_dt:
        return False

    # make 'now' timezone-aware using email_dt tzinfo (or UTC fallback)
    now = datetime.now(tz=email_dt.tzinfo or timezone.utc)
    days = int(value_int)
    
    if pred=="older_than_days":
        return email_dt<(now -  timedelta(days=days))
    
    if pred=="newer_than_days":
        return email_dt<(now -  timedelta(days=days))

    return False

def evaluate_condition(email_row, cond):
    field = cond["field"]
    pred = cond["predicate"]
    value = cond["value"]

    # Map fields
    if field == "from_email":
        return eval_string(email_row.get("from_email", ""), pred, value)

    if field == "subject":
        return eval_string(email_row.get("subject", ""), pred, value)

    if field == "message":
        return eval_string(email_row.get("body", ""), pred, value)

    if field == "received_datetime":
        dt = parse_email_date(email_row.get("date_received"))
        return eval_date(dt, pred, int(value))

    # Unknown field:
    return False


# --------------------- ACTION EXECUTION ---------------------
def apply_action(service, msg_id, action, label_map):
    """Apply a single action: mark/read/unread or move message."""
    msg = service.users().messages().get(userId="me", id=msg_id).execute()
    existing = msg.get("labelIds", [])

    add = []
    remove = []

    # --- Mark as unread ---
    if action == "mark_unread":
        if "UNREAD" not in existing:
            add.append("UNREAD")

    # --- Mark as read ---
    elif action == "mark_read":
        if "UNREAD" in existing:
            remove.append("UNREAD")

    # --- Move message (remove inbox) ---
    elif action.startswith("move_message:"):
        label = action.split(":", 1)[1].strip()
        label_id = get_or_create_label(service, label, label_map)
        add.append(label_id)
        if "INBOX" in existing:
            remove.append("INBOX")

    # --- Move message but keep inbox ---
    elif action.startswith("move_message_keep_inbox:"):
        label = action.split(":", 1)[1].strip()
        label_id = get_or_create_label(service, label, label_map)
        add.append(label_id)

    else:
        print(f"Unknown action: {action}")
        return

    # If nothing to change → skip
    if not add and not remove:
        print(f"No changes needed for action={action} msg={msg_id}")
        return

    service.users().messages().modify(
        userId="me",
        id=msg_id,
        body={"addLabelIds": add, "removeLabelIds": remove}
    ).execute()

    print(f"Applied {action} → add={add} remove={remove}")


# --------------------- MAIN ENGINE ---------------------
def process_all(rules_path=RULES_PATH):
    data = json.load(open(rules_path))
    rules = data.get("rules", [])

    emails = fetch_all_emails()
    service = get_service()

    label_map = build_label_map(service)

    print(f"Loaded {len(rules)} rules; Processing {len(emails)} emails...\n")

    for email in emails:
        for rule in rules:
            conditions = rule.get("conditions", [])
            mode = rule.get("collection_predicate", "all").lower()

            results = [evaluate_condition(email, c) for c in conditions]

            matched = False
            if mode == "all":
                matched = all(results)
            elif mode == "any":
                matched = any(results)

            if matched:
                print(f"Rule matched: {rule['id']} → email {email['id']}")
                for action in rule.get("actions", []):
                    apply_action(service, email["id"], action, label_map)


if __name__ == "__main__":
    process_all()
