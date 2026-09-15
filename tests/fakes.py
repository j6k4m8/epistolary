"""In-memory backends for the three protocols."""

import fitz

from epistolary.mailbox_manager import Email

ANN = '"Ann" <ann@x.com>'


def email(uid: int, subject: str = "Hello", text: str = "hi", bulk: bool = False) -> Email:
    return Email(uid, f"<{uid}@x>", ANN, ANN, subject, text, "", bulk)


def write_on(doc: fitz.Document, page: int = -1) -> None:
    doc[page].insert_text((72, 200), "handwriting here", fontsize=24)


class FakeMailbox:
    def __init__(self, *emails: Email):
        self.emails = {e.uid: e for e in emails}
        self.sent, self.answered = [], []

    def unseen_uids(self, folder):
        return sorted(self.emails)

    def fetch(self, folder, uids):
        return [self.emails[u] for u in uids]

    def mark_answered(self, folder, uid):
        self.answered.append(uid)

    def send(self, to, subject, body, in_reply_to=None):
        self.sent.append((to, subject, body, in_reply_to))

    def check(self):
        pass


class FakeDocuments:
    def __init__(self):
        self.inbox, self.outbox, self.archived = {}, {}, []
        self.fail_archive = False

    def list_inbox(self):
        return sorted(self.inbox)

    def list_outbox(self):
        return sorted(self.outbox)

    def get(self, name, outbox=False):
        return (self.outbox if outbox else self.inbox)[name]

    def put(self, name, doc):
        self.inbox[name] = doc

    def archive(self, name, outbox=False):
        if self.fail_archive:
            raise OSError("tablet offline")
        (self.outbox if outbox else self.inbox).pop(name)
        self.archived.append(name)

    def move_to_outbox(self, name):
        self.outbox[name] = self.inbox.pop(name)


class FakeExtractor:
    def extract(self, page):
        return "transcribed"
