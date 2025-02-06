from ..epiconfig import EpistolaryConfig
import pathlib
import os
import base64
import google.auth
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from typing import Union

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly", "https://www.googleapis.com/auth/gmail.send"]

class GmailMailboxManager:
    def __init__(
        self,
        username: str,
        credentials: Credentials,
    ):
        self.username = username
        self.credentials = credentials
        self.service = build('gmail', 'v1', credentials=credentials)

    @classmethod
    def from_file(cls, path: str | pathlib.Path = "~/.config/epistolary.json") -> "GmailMailboxManager":
        config = EpistolaryConfig.from_file(path)
        creds = cls.get_credentials(config)
        return cls(
            username=config.email,
            credentials=creds,
        )

    @staticmethod
    def get_credentials(config) -> Credentials:
        creds = None
        token_path = os.path.expanduser(config.token_path)
        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    os.path.expanduser(config.credentials_path), SCOPES
                )
                creds = flow.run_local_server(port=0)
            with open(token_path, "w") as token:
                token.write(creds.to_json())
        return creds

    def get_emails(self, query: str = '', max_results: int = 10):
        results = self.service.users().messages().list(userId='me', q=query, maxResults=max_results).execute()
        messages = results.get('messages', [])
        emails = []
        for message in messages:
            msg = self.service.users().messages().get(userId='me', id=message['id']).execute()
            emails.append(msg)
        return emails

    def send_message(self, to: str, subject: str, body: str):
        message = self.create_message(to, subject, body)
        sent_message = self.service.users().messages().send(userId='me', body=message).execute()
        return sent_message

    def create_message(self, to: str, subject: str, body: str):
        message = {
            'raw': base64.urlsafe_b64encode(f"To: {to}\nSubject: {subject}\n\n{body}".encode('utf-8')).decode('utf-8')
        }
        return message
