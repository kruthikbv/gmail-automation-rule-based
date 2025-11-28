"""
db.py
SQLite wrapper for storing fetched emails.

Schema: emails table
Columns:
- id (TEXT PRIMARY KEY) : Gmail message id
- from_email (TEXT)
- to_email (TEXT)
- subject (TEXT)
- body (TEXT)
- date_received (TEXT)
- label_ids (TEXT) -- comma separated label ids
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "emails.db"

def init_db():
    """Create the emails table if it doesn't exist."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS emails (
            id TEXT PRIMARY KEY,
            from_email TEXT,
            to_email TEXT,
            subject TEXT,
            body TEXT,
            date_received TEXT,
            label_ids TEXT
        )
    """)
    conn.commit()
    conn.close()

def insert_email(msg):
    """
    Insert or update email record.
    msg is a dict with fields:
    id, from_email, to_email, subject, body, date_received, label_ids
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        INSERT OR REPLACE INTO emails
        (id, from_email, to_email, subject, body, date_received, label_ids)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        msg['id'],
        msg.get('from_email'),
        msg.get('to_email'),
        msg.get('subject'),
        msg.get('body'),
        msg.get('date_received'),
        msg.get('label_ids')
    ))
    conn.commit()
    conn.close()

def fetch_all_emails():
    """Return all email rows as a list of dictionaries."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        SELECT id, from_email, to_email, subject, body, date_received, label_ids
        FROM emails
    """)
    rows = cur.fetchall()
    conn.close()

    columns = [
        'id', 'from_email', 'to_email',
        'subject', 'body', 'date_received', 'label_ids'
    ]

    return [dict(zip(columns, r)) for r in rows]

if __name__ == "__main__":
    init_db()
    print("DB initialized at", DB_PATH)
