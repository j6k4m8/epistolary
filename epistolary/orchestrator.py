"""The receive and send flows. Everything else is a backend behind one of the three protocols."""

import json
import logging
import re
from email.utils import getaddresses
from pathlib import Path
from typing import Callable
from urllib.parse import unquote

from .config import write_private
from .document_manager import DocumentManager
from .mailbox_manager import Email, MailboxManager
from .pdf import append_ruled_page, email_to_pdf, has_ink
from .text_extractor import TextExtractor

log = logging.getLogger(__name__)

Confirm = Callable[[str, str, str], bool]
"""Called with (to, subject, body) before each send. Return False to leave the document in the outbox."""

NEW_MESSAGE_SEPARATOR = ":::"
"""An outbox document named `someone@example.com:::Subject` that did not come from an email is a new message."""


class EpistolaryOrchestrator:
    def __init__(
        self,
        mailbox: MailboxManager,
        documents: DocumentManager,
        extractor: TextExtractor,
        state_path: str | Path,
        folder: str = "INBOX",
        limit: int = 10,
        ignore_marketing: bool = True,
    ):
        self.mailbox = mailbox
        self.documents = documents
        self.extractor = extractor
        self.folder = folder
        self.limit = limit
        self.ignore_marketing = ignore_marketing
        self.state_path = Path(state_path).expanduser()
        # state["docs"] maps a document name to what is known about it. For a document made from an
        # email: uid, message_id, reply_to, subject, pages (before the reply page), and sent once it is.
        # For a new message: only sent, and only until it is archived. state["skipped"] lists UIDs that
        # were deliberately not uploaded. Together these are the UIDs already handled.
        self.state = (
            json.loads(self.state_path.read_text()) if self.state_path.exists() else {"docs": {}, "skipped": []}
        )

    def _save(self) -> None:
        write_private(self.state_path, json.dumps(self.state, indent=1))

    def receive(self) -> list[str]:
        """Upload unread emails not handled before, the newest `limit` of them. Returns the new document names."""
        docs = self.state["docs"]
        known = {d["uid"] for d in docs.values() if "uid" in d} | set(self.state["skipped"])
        uids = [u for u in self.mailbox.unseen_uids(self.folder) if u not in known][-self.limit :]
        taken = set(docs) | set(self.documents.list_inbox())
        created = []
        for e in self.mailbox.fetch(self.folder, uids):
            try:
                if self.ignore_marketing and e.bulk:
                    log.info("skipping %r from %s: bulk mail", e.subject, e.sender)
                    self.state["skipped"].append(e.uid)
                    continue
                name = _unique(_name_for(e), taken)
                doc = email_to_pdf(e)
                pages = doc.page_count
                append_ruled_page(doc)
                self.documents.put(name, doc)
                docs[name] = {
                    "uid": e.uid,
                    "message_id": e.message_id,
                    "reply_to": e.reply_to,
                    "subject": e.subject,
                    "pages": pages,
                }
                taken.add(name)
                created.append(name)
                log.info("uploaded %r", name)
            except Exception:
                log.exception("could not process uid %s (%r); will retry next time", e.uid, e.subject)
            self._save()
        return created

    def prune(self) -> list[str]:
        """Archive inbox documents whose email is no longer unread, that is, handled somewhere else."""
        unseen = set(self.mailbox.unseen_uids(self.folder))
        inbox = set(self.documents.list_inbox())
        stale = [n for n, d in self.state["docs"].items() if n in inbox and "uid" in d and d["uid"] not in unseen]
        for name in stale:
            self.documents.archive(name)
            log.info("archived %r: its email is no longer unread", name)
        return stale

    def send(self, confirm: Confirm | None = None) -> list[str]:
        """Transcribe every document in the outbox and email it. Returns the names sent."""
        sent = []
        for name in self.documents.list_outbox():
            meta = self.state["docs"].get(name, {})
            try:
                if meta.get("sent"):
                    log.info("%r already went out last time; archiving it", name)
                else:
                    message = self._compose(name, meta)
                    if message is None:
                        continue
                    to, subject, text = message
                    if confirm and not confirm(to, subject, text):
                        continue
                    self.mailbox.send(to, subject, text, meta.get("message_id") or None)
                    meta["sent"] = True
                    self.state["docs"][name] = meta
                    self._save()
                    sent.append(name)
                    log.info("sent %r to %s", name, to)
                self.documents.archive(name, outbox=True)
            except Exception:
                log.exception("could not finish %r; will retry next time", name)
                continue
            if "uid" in meta:
                try:
                    self.mailbox.mark_answered(self.folder, meta["uid"])
                except Exception:
                    log.warning("could not flag uid %s as answered", meta["uid"])
            else:
                del self.state["docs"][name]
                self._save()
        return sent

    def _compose(self, name: str, meta: dict) -> tuple[str, str, str] | None:
        """(to, subject, text) for an outbox document, or None if nothing is written on its reply pages."""
        pages = list(self.documents.get(name, outbox=True))
        written = [p for p in pages[meta.get("pages", 0) :] if has_ink(p)]
        text = "\n\n".join(self.extractor.extract(p) for p in written).strip()
        if not text:
            log.warning("%r has no handwriting on its reply pages; leaving it in the outbox", name)
            return None
        if "uid" in meta:
            return meta["reply_to"], _reply_subject(meta["subject"]), text
        to, subject = _parse_new_message_name(name)
        return to, subject, text


def _name_for(e: Email) -> str:
    """`Subject - Sender`, safe as a reMarkable or file name."""
    addresses = getaddresses([e.sender])
    realname, address = addresses[0] if addresses else ("", "")
    name = re.sub(r"[\\/\x00-\x1f]+", " ", f"{e.subject} - {realname or address or 'unknown'}")
    return re.sub(r"\s+", " ", name)[:80].strip(" -.")


def _unique(name: str, taken: set[str]) -> str:
    candidate, n = name, 2
    while candidate in taken:
        candidate, n = f"{name} ({n})", n + 1
    return candidate


def _reply_subject(subject: str) -> str:
    return subject if subject.lower().startswith("re:") else f"Re: {subject}"


def _parse_new_message_name(name: str) -> tuple[str, str]:
    to, sep, subject = name.partition(NEW_MESSAGE_SEPARATOR)
    to = unquote(to).strip()  # 0.2 percent-encoded the address
    if not sep or "@" not in to:
        raise ValueError(
            f"{name!r} is not a reply and is not named like `to@example.com{NEW_MESSAGE_SEPARATOR}Subject`"
        )
    return to, subject.strip()
