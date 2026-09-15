import imaplib
import smtplib

import pytest

from epistolary.mailbox_manager import SMTPIMAPMailboxManager

RAW = b"From: a@b.com\r\nSubject: hi\r\nContent-Type: text/plain\r\n\r\nhello\r\n"


class FakeIMAP:
    def __init__(self, host, port, timeout=None):
        self.calls = []

    def login(self, user, password):
        self.calls.append(("login", user, password))

    def logout(self):
        pass

    def select(self, folder, readonly=False):
        self.calls.append(("select", folder, readonly))
        return ("OK", [b"3"]) if folder == "INBOX" else ("NO", [b"no such folder"])

    def uid(self, command, *args):
        self.calls.append((command, *args))
        if command == "SEARCH":
            return "OK", [b"9 4 12"]
        if command == "FETCH":
            return "OK", [(b"1 (UID 4 BODY[] {56}", RAW), b")"] if args[0] == "4" else [None]
        return "OK", [b""]


class FakeSMTP:
    instances = []

    def __init__(self, host, port, timeout=None):
        self.messages, self.tls = [], False
        FakeSMTP.instances.append(self)

    def starttls(self):
        self.tls = True

    def login(self, user, password):
        self.auth = (user, password)

    def send_message(self, msg):
        self.messages.append(msg)

    def quit(self):
        pass


class FakeSMTPSSL(FakeSMTP):
    starttls = None  # calling it would be a bug


@pytest.fixture
def servers(monkeypatch):
    imaps = []
    monkeypatch.setattr(imaplib, "IMAP4_SSL", lambda *a, **k: imaps.append(FakeIMAP(*a, **k)) or imaps[-1])
    monkeypatch.setattr(smtplib, "SMTP", FakeSMTP)
    monkeypatch.setattr(smtplib, "SMTP_SSL", FakeSMTPSSL)
    FakeSMTP.instances.clear()
    return imaps


def test_imap_reads_without_touching_flags(servers):
    box = SMTPIMAPMailboxManager("imap", 993, "me@x.com", "pw", "smtp", 587)
    assert box.unseen_uids("INBOX") == [4, 9, 12]
    (e,) = box.fetch("INBOX", [4, 5])  # 5 vanished in between
    assert (e.uid, e.text) == (4, "hello\n")
    assert ("select", "INBOX", True) in servers[1].calls and ("FETCH", "4", "(BODY.PEEK[])") in servers[1].calls
    box.mark_answered("INBOX", 4)
    assert servers[2].calls[-2:] == [("select", "INBOX", False), ("STORE", "4", "+FLAGS", r"(\Answered)")]
    with pytest.raises(RuntimeError, match="no such folder"):
        box.unseen_uids("Nope")


def test_smtp_reply_headers_and_transports(servers):
    box = SMTPIMAPMailboxManager("imap", 993, "me@x.com", "pw", "smtp", 587)
    box.send('"Bob" <bob@x.com>', "Re: hi", "line one\nline two", "<orig@x>")
    (conn,) = FakeSMTP.instances
    (msg,) = conn.messages
    assert conn.tls and conn.auth == ("me@x.com", "pw")
    assert (msg["To"], msg["In-Reply-To"], msg["References"]) == ("Bob <bob@x.com>", "<orig@x>", "<orig@x>")
    assert msg.get_content() == "line one\nline two\n" and msg["Message-ID"].endswith("@x.com>")
    SMTPIMAPMailboxManager("imap", 993, "me@x.com", "pw", "smtp", 465, "smtp-user", "pw2").check()
    assert isinstance(FakeSMTP.instances[-1], FakeSMTPSSL) and FakeSMTP.instances[-1].auth == ("smtp-user", "pw2")
