"""
fetch_emails.py
Fetch emails from Gmail using the Gmail API and store them in SQLite database.
Requires auth.get_service() to return authenticated Gmail service.
"""
from auth import get_service
from db import init_db, insert_email
import base64
import email
from datetime import datetime

def get_message(service, msg_id):
    message = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
    payload = message.get('payload', {})
    headers = payload.get('headers', [])
    parts = payload.get('parts', [])
    # Extract headers
    header_map = {h['name']: h['value'] for h in headers}
    from_email = header_map.get('From', '')
    to_email = header_map.get('To', '')
    subject = header_map.get('Subject', '')
    date_received = header_map.get('Date', '')
    # Extract body (try payload.body, then parts)
    body = ''
    if payload.get('body') and payload['body'].get('data'):
        data = payload['body']['data']
        body = base64.urlsafe_b64decode(data.encode('ASCII')).decode('utf-8', errors='replace')
    else:
        # walk parts
        def get_text_from_parts(parts):
            texts = []
            for p in parts:
                if p.get('mimeType') == 'text/plain' and p.get('body', {}).get('data'):
                    data = p['body']['data']
                    texts.append(base64.urlsafe_b64decode(data.encode('ASCII')).decode('utf-8', errors='replace'))
                elif p.get('mimeType') == 'text/html' and p.get('body', {}).get('data'):
                    data = p['body']['data']
                    texts.append(base64.urlsafe_b64decode(data.encode('ASCII')).decode('utf-8', errors='replace'))
                elif p.get('parts'):
                    texts.extend(get_text_from_parts(p.get('parts')))
            return texts
        texts = get_text_from_parts(parts)
        body = "\n".join(texts)
    label_ids = ",".join(message.get('labelIds', []))
    return {
        'id': message['id'],
        'from_email': from_email,
        'to_email': to_email,
        'subject': subject,
        'body': body,
        'date_received': date_received,
        'label_ids': label_ids
    }

def list_message_ids(service, query=None, max_results=50):
    q = query if query else ''
    response = service.users().messages().list(userId='me', q=q, maxResults=max_results).execute()
    msgs = response.get('messages', [])
    ids = [m['id'] for m in msgs]
    return ids

def fetch_and_store(service, query=None, max_results=5):
    init_db()
    ids = list_message_ids(service, query=query, max_results=max_results)
    print(f"Found {len(ids)} messages (limited to {max_results})")
    for i, mid in enumerate(ids, start=1):
        try:
            msg = get_message(service, mid)
            insert_email(msg)
            print(f"[{i}] Stored message id={msg['id']} subject={msg['subject'][:150]}")
        except Exception as e:
            print("Error fetching message", mid, e)

if __name__ == '__main__':
    svc = get_service()
    # optional: change query to filter emails, e.g. 'is:unread'
    fetch_and_store(svc, query="in:inbox", max_results=5)
