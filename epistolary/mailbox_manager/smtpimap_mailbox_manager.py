from redbox import EmailBox
from redbox.models import EmailMessage
from redmail import EmailSender

from ..types import EmailID
from .mailbox_manager import MailboxManager


def _get_msgid_from_header_dict(header_dict: dict[str, str]) -> EmailID:
    _possible_message_id_keys = [
        "Message-ID",
        "Message-Id",
        "Message-id",
        "message-id",
        "message_id",
        "messageid",
    ]
    for possible_key in _possible_message_id_keys:
        if possible_key in header_dict:
            return EmailID(header_dict[possible_key])

    raise ValueError("No message ID found in header dict")


class SMTPIMAPMailboxManager(MailboxManager):
    """
    A class representing a mailbox manager for SMTP and IMAP protocols.

    Args:
        host (str): The hostname of the mail server.
        port (int): The port number of the mail server.
        username (str): The username for authentication.
        password (str): The password for authentication.
    """

    def __init__(
        self,
        imap_host: str,
        imap_port: int,
        username: str,
        password: str,
        smtp_host: str,
        smtp_port: int = 465,
        smtp_username: str | None = None,
        smtp_password: str | None = None,
    ):
        """Create a new SMTPIMAPMailboxManager object.

        Arguments:
            host (str): The hostname of the mail server.
            port (int): The port number of the mail server.
            username (str): The username for authentication.
            password (str): The password for authentication.

        """
        if smtp_username is None:
            smtp_username = username
        if smtp_password is None:
            smtp_password = password
        self._box = EmailBox(imap_host, imap_port, username, password)
        self._sender = EmailSender(smtp_host, smtp_port, smtp_username, smtp_password)

    def get_emails(self, folder: str | None = None) -> dict[EmailID, EmailMessage]:
        """
        Get the emails from the specified folder.

        Arguments:
            folder (str | None, optional): The folder name. Defaults to "INBOX".

        Returns:
            dict[EmailID, EmailMessage]: A dictionary containing the emails,
                where keys are the email IDs and the values are the messages.
        """
        if folder is None:
            folder = "INBOX"
        messages = self._box[folder].search(unseen=True)
        return {
            EmailID(_get_msgid_from_header_dict(message.headers)): message
            for message in messages
        }

    def get_email(self, email_id: EmailID) -> EmailMessage:
        """
        Get the email with the specified ID.

        Arguments:
            email_id (EmailID): The email ID.

        Returns:
            EmailMessage: The email message.
        """
        # TODO: Sad puppy
        return self.get_emails()[email_id]

    def get_email_subject_and_text(self, uid: EmailID) -> tuple[str, str]:
        """
        Get the subject and text of the email with the specified ID.

        Arguments:
            uid (EmailID): The email ID.

        Returns:
            tuple[str, str]: The subject and text of the email.
        """
        email = self.get_email(uid)
        return email.subject, email.html_body

    def send_message(
        self, to: str, subject: str, body: str, in_reply_to: EmailID | None = None
    ) -> bool:
        """Send a message."""
        to = "epistolary-testing@matelsky.com"
        # sender = self._sender.username
        # sender = "jordan@matelsky.com"
        self._sender.send(
            subject=subject,
            receivers=[to],
            text=body,
            html=body,
            headers={"In-Reply-To": in_reply_to} if in_reply_to is not None else None,
        )
        return True
