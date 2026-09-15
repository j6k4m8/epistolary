"""IMAP and SMTP over the standard library."""

import imaplib
import smtplib
from contextlib import contextmanager, suppress
from email.message import EmailMessage
from email.utils import formatdate, make_msgid

from .mailbox_manager import Email

TIMEOUT = 30  # seconds, per connection


class SMTPIMAPMailboxManager:
    def __init__(
        self,
        imap_host: str,
        imap_port: int,
        username: str,
        password: str,
        smtp_host: str,
        smtp_port: int = 587,
        smtp_username: str | None = None,
        smtp_password: str | None = None,
    ):
        self.imap = (imap_host, imap_port, username, password)
        self.smtp = (smtp_host, smtp_port, smtp_username or username, smtp_password or password)
        self.address = username

    @contextmanager
    def _imap(self):
        host, port, user, password = self.imap
        conn = imaplib.IMAP4_SSL(host, port, timeout=TIMEOUT)
        try:
            conn.login(user, password)
            yield conn
        finally:
            with suppress(Exception):
                conn.logout()

    @contextmanager
    def _smtp(self):
        host, port, user, password = self.smtp
        if port == 465:
            conn = smtplib.SMTP_SSL(host, port, timeout=TIMEOUT)
        else:
            conn = smtplib.SMTP(host, port, timeout=TIMEOUT)
        try:
            if port != 465:
                conn.starttls()
            conn.login(user, password)
            yield conn
        finally:
            with suppress(Exception):
                conn.quit()

    def check(self) -> None:
        with self._imap(), self._smtp():
            pass

    def unseen_uids(self, folder: str) -> list[int]:
        with self._imap() as conn:
            _select(conn, folder, readonly=True)
            _, data = conn.uid("SEARCH", "UNSEEN")
        return sorted(int(uid) for uid in data[0].split())

    def fetch(self, folder: str, uids: list[int]) -> list[Email]:
        emails = []
        with self._imap() as conn:
            _select(conn, folder, readonly=True)
            for uid in uids:
                _, data = conn.uid("FETCH", str(uid), "(BODY.PEEK[])")
                raw = next((part[1] for part in data if isinstance(part, tuple)), None)
                if raw:  # None if the message vanished between search and fetch
                    emails.append(Email.from_bytes(uid, raw))
        return emails

    def mark_answered(self, folder: str, uid: int) -> None:
        with self._imap() as conn:
            _select(conn, folder)
            conn.uid("STORE", str(uid), "+FLAGS", r"(\Answered)")

    def send(self, to: str, subject: str, body: str, in_reply_to: str | None = None) -> None:
        msg = EmailMessage()
        msg["From"] = self.address
        msg["To"] = to
        msg["Subject"] = subject
        msg["Date"] = formatdate(localtime=True)
        msg["Message-ID"] = make_msgid(domain=self.address.rpartition("@")[2] or None)
        if in_reply_to:
            msg["In-Reply-To"] = msg["References"] = in_reply_to
        msg.set_content(body)
        with self._smtp() as conn:
            conn.send_message(msg)


def _select(conn: imaplib.IMAP4, folder: str, readonly: bool = False) -> None:
    status, detail = conn.select(folder, readonly=readonly)
    if status != "OK":
        raise RuntimeError(f"cannot open folder {folder!r}: {detail[0].decode()}")
