"""
auth.py
Handles Google OAuth2 authentication and returns a Gmail API service object.

Before running:
1. Enable Gmail API in Google Cloud Console.
2. Create OAuth 2.0 Client ID (Desktop) credentials and download credentials.json into project folder.
3. pip install -r requirements.txt
4. First run will open a browser for authorization and create token.json.

This file uses google-auth and google-api-python-client libraries.
"""
from __future__ import print_function
import os
import pathlib
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# If modifying these SCOPES, delete the token.json file.
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

def get_service(credentials_path='credentials.json', token_path='token.json'):
    """
    Authenticate and return Gmail API service
    """
    creds = None
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(token_path, 'w') as token:
            token.write(creds.to_json())

    service = build('gmail', 'v1', credentials=creds)
    return service

if __name__ == "__main__":
    svc = get_service()
    print("Service created:", svc is not None)
