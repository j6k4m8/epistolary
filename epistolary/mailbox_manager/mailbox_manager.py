from typing import Protocol
from redbox.models import EmailMessage
from .types import EmailID


class MailboxManager(Protocol):
    """A protocol for classes that manage mailboxes."""

    def get_emails(self, folder: str | None = None) -> dict[EmailID, EmailMessage]:
        """Return a list of emails in the specified folder.

        Arguments:
            folder: The folder to get emails from. If None, get emails from
                all folders.

        Returns:
            A dictionary of emails, with the email ID as the key and the email
            as the value.
        """
        ...

    def get_email(self, uid: EmailID) -> EmailMessage:
        """Get a single email.

        Arguments:
            uid: The ID of the email to get.

        Returns:
            The requested email.

        """
        ...

    def get_email_subject_and_text(self, uid: EmailID) -> tuple[str, str]:
        """Get the subject and text of an email.

        Arguments:
            uid: The ID of the email to get.

        Returns:
            The subject and text of the email.

        """
        ...

    def send_message(
        self, to: str, subject: str, body: str, in_reply_to: EmailID | None = None
    ) -> bool:
        """
        Send a message to the specified recipient.

        Argumentss:
            to: The email address of the recipient.
            subject: The subject of the email.
            body: The body of the email.
            in_reply_to: The ID of the email to reply to, if any.

        Returns:
            True if the message was sent successfully, False otherwise.

        """
        ...
