import pathlib
import fitz
from .document_manager import DocumentManager

from epistolary.types import DocumentID


class FilesystemDocumentManager(DocumentManager):
    """A DocumentManager that stores documents in a local filesystem.

    Each document is a PDF, and they are lazily loaded with pypdf when the
    user requests them.
    """

    def __init__(self, root_path: pathlib.Path):
        self.root_path = root_path

    def get_documents(self) -> dict[DocumentID, fitz.Document]:
        """Return a list of documents.

        Returns:
            A dictionary of documents, with the document ID as the key and the
            document as the value.

        """
        return {
            DocumentID(path.stem): fitz.open(path)
            for path in self.root_path.glob("*.pdf")
        }

    def list_documents(self) -> list[DocumentID]:
        """Return a list of document IDs.

        Returns:
            A list of document IDs.

        """
        return [DocumentID(path.stem) for path in self.root_path.glob("*.pdf")]

    def get_document(self, document_id: DocumentID) -> fitz.Document:
        """Return a single document.

        Args:
            document_id: The ID of the document to return.

        Returns:
            The document with the given ID.

        """
        return fitz.open(self.root_path / f"{document_id}.pdf")

    def has_document(self, document_id: DocumentID) -> bool:
        """Return whether a document exists.

        Args:
            document_id: The ID of the document to check for.

        Returns:
            Whether the document exists.

        """
        return (self.root_path / f"{document_id}.pdf").exists()

    def append_ruled_page_to_document(self, document: fitz.Document) -> fitz.Document:
        """Append a ruled page to a document.

        Arguments:
            document: The document to append the page to.

        Returns:
            A NEW document with the page appended.

        """
        # TODO: For now, just append a blank page
        page = document.new_page(-1)  # type: ignore
        return document

    def put_document(
        self, document: fitz.Document, requested_document_id: DocumentID
    ) -> DocumentID:
        """Put a document into the document manager.

        Arguments:
            document: The document to put.
            requested_document_id: The ID to use for the document.

        Returns:
            The ID of the document that was put.

        """
        if self.has_document(requested_document_id):
            raise ValueError("Document already exists!")
        document.save(self.root_path / f"{requested_document_id}.pdf")
        return requested_document_id

    def delete_document(self, document_id: DocumentID) -> None:
        """Delete a document.

        Args:
            document_id: The ID of the document to delete.

        """
        (self.root_path / f"{document_id}.pdf").unlink()
