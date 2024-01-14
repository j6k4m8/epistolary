from .document_manager import DocumentManager
from .mailbox_manager import MailboxManager
from .text_extractor import TextExtractor
from .types import DocumentID, EmailID


class EpistolaryOrchestrator:
    """A class that orchestrates the Epistolary system."""

    def __init__(
        self,
        mailbox_manager: MailboxManager,
        document_manager: DocumentManager,
    ):
        """Initialize the orchestrator.

        Arguments:
            mailbox_manager: The mailbox manager to use.
            document_manager: The document manager to use.

        """
        self.mailbox_manager = mailbox_manager
        self.document_manager = document_manager

    def upload_email_by_id(self, email_id: EmailID) -> DocumentID:
        """Upload an email to the document manager.

        Arguments:
            email_id: The ID of the email to upload.

        Returns:
            The ID of the document.

        """
        # Get the subject and text of the email
        subject, text = self.mailbox_manager.get_email_subject_and_text(email_id)
        # Create a document from the subject and text and then append a page
        # for the user to write on
        document = self.document_manager.create_document_from_subject_and_text(
            subject, text
        )
        document = self.document_manager.append_ruled_page_to_document(document)
        # Put the document into the document manager:
        document_id = self.document_manager.put_document(document, email_id)
        return document_id

    def refresh_document_mailbox(self):
        """Refresh the document mailbox."""
        # TODO: Only delete documents that are no longer in the mailbox.
        # (Prevent delete and immediately re-upload)

        # Delete all old documents:
        for document_id in self.document_manager.list_documents():
            self.document_manager.delete_document(document_id)

        # Upload all current emails:
        for eid, _ in self.mailbox_manager.get_emails():
            # Check if the email has already been added to the document mailbox
            # (the document ID should be the same as the email ID)
            if self.document_manager.has_document(DocumentID(eid)):
                continue

            # If the email has not been added, add it:
            self.upload_email_by_id(eid)

    def send_document_by_id(self, document_id: DocumentID, to: str) -> bool:
        """Send a document to an email address."""
        # Get the document:
        document = self.document_manager.get_document(document_id)
        # Create an email from the document:
        subject, text = self.document_manager.create_email_from_document(document)
        # Send the email:
        return self.mailbox_manager.send_message(to, subject, text)
