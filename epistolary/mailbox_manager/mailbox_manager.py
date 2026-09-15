"""The mailbox interface and the email record the rest of the system works with."""

import email
import email.policy
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class Email:
    uid: int
    message_id: str
    sender: str
    reply_to: str
    subject: str
    text: str
    html: str
    bulk: bool = False  # a mailing list or marketing sender

    @classmethod
    def from_bytes(cls, uid: int, raw: bytes) -> "Email":
        """Parse an RFC 822 message. Headers and transfer encodings are decoded."""
        msg = email.message_from_bytes(raw, policy=email.policy.default)

        def body(kind: str) -> str:
            part = msg.get_body(preferencelist=(kind,))
            if part is None:
                return ""
            try:
                text = part.get_content()
            except (LookupError, UnicodeDecodeError):  # unknown or mislabeled charset
                text = part.get_payload(decode=True).decode("utf-8", "replace")
            return text.replace("\r\n", "\n")

        sender = str(msg.get("From", ""))
        return cls(
            uid=uid,
            message_id=str(msg.get("Message-ID", "")).strip(),
            sender=sender,
            reply_to=str(msg.get("Reply-To", "")) or sender,
            subject=str(msg.get("Subject", "")).strip() or "(no subject)",
            text=body("plain"),
            html=body("html"),
            bulk="List-Unsubscribe" in msg,
        )


class MailboxManager(Protocol):
    def unseen_uids(self, folder: str) -> list[int]:
        """UIDs of unread messages, ascending. Must not change any flags."""
        ...

    def fetch(self, folder: str, uids: list[int]) -> list[Email]:
        """Download messages by UID. Must not mark them read."""
        ...

    def mark_answered(self, folder: str, uid: int) -> None: ...

    def send(self, to: str, subject: str, body: str, in_reply_to: str | None = None) -> None:
        """Send a plain-text message. `in_reply_to` is the Message-ID being answered."""
        ...

    def check(self) -> None:
        """Log in to both servers and disconnect. Raises if either fails."""
        ...
