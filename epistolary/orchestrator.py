from epistolary.document_manager import DocumentManager
from epistolary.mailbox_manager import MailboxManager
from epistolary.text_extractor import TextExtractor

import fitz
import io
from fitz import Document
from epistolary.types import DocumentID, EmailID
import base64


class EpistolaryOrchestrator:
    """A class that orchestrates the Epistolary system."""

    def __init__(
        self,
        mailbox_manager: MailboxManager,
        document_manager: DocumentManager,
        text_extractor: TextExtractor,
        debug: bool = False,
    ):
        """Initialize the orchestrator.

        Arguments:
            mailbox_manager: The mailbox manager to use.
            document_manager: The document manager to use.
            debug: Whether to print debug messages.

        """
        self.mailbox_manager = mailbox_manager
        self.document_manager = document_manager
        self.text_extractor = text_extractor
        self._debug = debug

    def refresh_document_mailbox(self):
        """Refresh the document mailbox."""
        new_emails = self.mailbox_manager.get_emails(limit=10)
        if self._debug:
            print(f"Found {len(new_emails)} new emails.")

        # Delete all old documents:
        for document_id in self.document_manager.list_documents():
            # If not in the new emails, delete the document:
            if document_id not in new_emails:
                if self._debug:
                    print(f"Deleting document {document_id}: No longer in mailbox.")
                self.document_manager.delete_document(document_id)

        # Upload all current emails:
        for eid, msg in new_emails.items():
            # Check if the email has already been added to the document mailbox
            # (the document ID should be the same as the email ID)
            if self.document_manager.has_document(DocumentID(eid)):
                if self._debug:
                    print(f"Skipping email {eid}: Already in mailbox.")
                continue

            if (
                "unsubscribe" in msg.text_body.lower()
                or "unsubscribe" in msg.html_body.lower()
            ):
                if self._debug:
                    print(f"Skipping email {eid}: Unsubscribe link.")
                continue
            # If the email has not been added, add it:
            if self._debug:
                print(f"Uploading email {eid} to document mailbox.")
            self.upload_email_by_id(eid)

    def _email_to_document(self, email_id: EmailID) -> io.BytesIO:
        """Create a document by reflowing the text of an email.

        Arguments:
            email_id: The ID of the email to render to PDF.

        """
        email = self.mailbox_manager.get_email(email_id)
        sender = email.from_
        subject = email.subject
        html_body = email.html_body
        text_body = email.text_body

        # text_body is b64 encoded, so we need to decode it:

        try:
            text_body = base64.b64decode(text_body).decode("utf-8")
        except Exception as _e:
            text_body = text_body
        text_body_as_html = text_body.strip().replace("\n", "<br />")

        # html_body is the HTML content of the email, but it may also be in
        # the
        # date = email.date
        # Render the HTML email to a PDF using the library "fitz":
        pagebox = fitz.paper_rect("letter")
        story = fitz.Story(
            f"""
        <p><b>{sender}</b></p>
        <p><b>{subject}</b></p>
        <br />
        {text_body_as_html if text_body_as_html else html_body}
        """
        )
        page_with_margins = pagebox + (36, 36, -36, -36)  # 0.5in margins

        # Create in-memory PDF:
        pdfbytes = io.BytesIO()
        writer = fitz.DocumentWriter(pdfbytes)
        more = True
        while more:
            device = writer.begin_page(pagebox)
            more, _ = story.place(page_with_margins)
            story.draw(device)
            writer.end_page()
        writer.close()

        pdfbytes.seek(0)
        return pdfbytes

    def upload_email_by_id(self, email_id: EmailID) -> DocumentID:
        """Upload an email to the document manager.

        Arguments:
            email_id: The ID of the email to upload.

        Returns:
            The ID of the document.

        """
        # Create a document from the subject and text and then append a page
        # for the user to write on
        document_bytes = self._email_to_document(email_id)
        document = fitz.Document(stream=document_bytes.read(), filetype="pdf")

        document = self.document_manager.append_ruled_page_to_document(document)
        # Put the document into the document manager:
        document_id = self.document_manager.put_document(document, email_id)
        return document_id

    def get_edited_documents(self) -> dict[DocumentID, Document]:
        """Get all documents that have been edited."""
        docs = self.document_manager.get_edited_documents()
        return docs

    def get_last_page_ocr_text_for_document(self, doc: DocumentID | Document) -> str:
        """Get the OCR text for the last page of a document.

        Arguments:
            doc: The document to get the OCR text for. This can be either a
                document ID or a document object. If it is a document ID, the
                document will be retrieved from the document manager.

        Returns:
            The OCR text for the last page of the document.

        """
        if isinstance(doc, DocumentID):
            doc = self.document_manager.get_document(doc)
        last_page = doc[-1]
        return self.text_extractor.extract_text_from_page(last_page)

    def send_outbox(self) -> list[EmailID]:
        """Send all documents in the outbox."""
        outbox = self.document_manager.get_edited_documents()
        sent_emails = []
        for did, doc in outbox.items():
            outgoing_text = self.get_last_page_ocr_text_for_document(doc)
            relevant_received_email = self.mailbox_manager.get_email(did)
            result = self.mailbox_manager.send_message(
                to=relevant_received_email.from_,
                subject="Re: " + relevant_received_email.subject,
                body=outgoing_text,
                in_reply_to=did,
            )
            sent_emails.append(result)
            if result:
                self.document_manager.delete_document(did)
        return sent_emails
