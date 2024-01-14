from typing import Protocol
from ..types import Document, DocumentID


class DocumentManager(Protocol):
    """A protocol for classes that manage documents."""

    def get_documents(self) -> dict[DocumentID, Document]:
        """Return a list of documents.

        Returns:
            A dictionary of documents, with the document ID as the key and the
            document as the value.

        """
        ...

    def list_documents(self) -> list[DocumentID]:
        """Return a list of document IDs.

        Returns:
            A list of document IDs.

        """
        ...

    def get_document(self, uid: DocumentID) -> Document:
        """Get a single document.

        Arguments:
            uid: The ID of the document to get.

        Returns:
            The requested document.

        """
        ...

    def has_document(self, uid: DocumentID) -> bool:
        """Check if a document exists.

        Arguments:
            uid: The ID of the document to check.

        Returns:
            True if the document exists, False otherwise.

        """
        ...

    def create_document_from_subject_and_text(
        self, subject: str, text: str
    ) -> Document:
        """Create a document from a subject and text.

        Arguments:
            subject: The subject of the document.
            text: The text of the document.

        Returns:
            The created document.

        """
        ...

    def create_email_from_document(self, document: Document) -> tuple[str, str]:
        """Create an email subject and text from a document.

        Arguments:
            document: The document to create the email from.

        Returns:
            The email subject and text.

        """
        ...

    def append_ruled_page_to_document(self, document: Document) -> Document:
        """Append a ruled page to a document.

        Does not modify the original document.

        Arguments:
            document: The document to append the page to.

        Returns:
            A NEW document with the page appended.

        """
        ...

    def put_document(
        self, document: Document, requested_document_id: DocumentID
    ) -> DocumentID:
        """Put a document into the document manager.

        Arguments:
            document: The document to put.
            requested_document_id: The ID to use for the document.

        Returns:
            The ID of the document.

        """
        ...

    def delete_document(self, uid: DocumentID) -> bool:
        """Delete a document.

        Arguments:
            uid: The ID of the document to delete.

        Returns:
            True if the document was deleted successfully, False otherwise.

        """
        ...
