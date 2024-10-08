"""
The reMarkable paper tablet has a long and storied hacker-facing API history.

The short version is that there is no reliable way to interact with the
reMarkable tablet filesystem with Python directly. Instead the current standard
way to talk to the tablet is with the Go rmapi tool, which is no longer main-
tained because the reMarkable company has continued to move the goalposts on
their API. Oh well!

Annoyingly they have also changed the standard format for the documents stored
on the tablet, so even though the "actual" format is a PDF, the files come off
of the tablet in an undocumented directory tree that includes several files per
document. The best way I've found to interact with this is through a fork of
the `remarks` tool, which, although Python, is not really intended for use as a
Python library.

So this class unfortunately serves more as a coordinator between the reMarkable
API and the rest of the epistolary codebase, rather than a true DocumentManager
implementation.
"""

import pathlib
import tempfile
import fitz
from .document_manager import DocumentManager

from ..types import DocumentID
from ..remarkable import RemarksWrapper, RMAPIWrapper, ReMarkablePathType


class RemarkableDocumentManager(DocumentManager):
    """A DocumentManager that stores documents on a reMarkable tablet."""

    _local_cache_root_path: pathlib.Path

    def __init__(
        self,
        local_cache_root_path: pathlib.Path | None = None,
        remarkable_root_path: str = "Emails",
        remarkable_outbox_subdirectory: str = "Outbox",
        debug: bool = False,
    ):
        """
        Create a new RemarkableDocumentManager.

        Arguments:
            local_cache_root_path: The path to the local cache directory where
                the document manager. Defaults to None, in which case a new
                temp directory is created and used.
            remarkable_root_path: The path to the root directory on the tablet
                where the documents are stored. Defaults to "Emails".
            remarkable_outbox_subdirectory: The subdirectory of the root
                directory where the outbox is stored. Defaults to "Outbox".
            debug: Whether to print debug information. Defaults to False.
        """
        self._local_cache_root_path = local_cache_root_path  # type: ignore
        self._provision_local_cache()

        self._rmapi = RMAPIWrapper(cache_dir=self._local_cache_root_path)
        self._remarkable_root_path = remarkable_root_path
        self._remarkable_outbox_subdirectory = remarkable_outbox_subdirectory
        self._provision_remarkable_directory()
        self._remarks = RemarksWrapper(debug=debug)
        self._debug = debug

    def _provision_local_cache(self):
        """Provision the local cache directory."""
        if self._local_cache_root_path is None:
            self._local_cache_root_path = pathlib.Path(tempfile.mkdtemp())
        self._local_cache_root_path.mkdir(parents=True, exist_ok=True)

    def _provision_remarkable_directory(self):
        """Provision the reMarkable directory."""
        # Check if the directory exists
        self._rmapi.mkdir(self._remarkable_root_path)
        self._rmapi.mkdir(
            self._remarkable_root_path + "/" + self._remarkable_outbox_subdirectory
        )

    def get_documents(self) -> dict[DocumentID, fitz.Document]:
        """Return a list of documents.

        This function works by performing two steps in sequence:

        It first reads from the tablet (using rmapi) and mirrors the files to
        the local cache. Then it converts each document in the local cache to a
        fitz.Document object by first converting the document to a PDF with the
        `remarks` tool and then opening the PDF with fitz.

        Note that this makes this function very slow, and it should only be
        used if you _actually_ need all of the documents. Instead, we recommend
        using the `get_document` function to get a single document, or the
        `list_documents` function to get a list of document IDs.

        Returns:
            A dictionary of documents, with the document ID as the key and the
            document as the value.

        """
        document_ids = self.list_documents()
        documents = {}
        for document_id in document_ids:
            documents[document_id] = self.get_document(document_id)
        return documents

    def get_edited_documents(self) -> dict[DocumentID, fitz.Document]:
        """Return a list of edited documents.

        Returns:
            A dictionary of documents, with the document ID as the key and the
            document as the value.

        """
        # Get all docs from the outbox
        files = self._rmapi.ls(
            self._remarkable_root_path + "/" + self._remarkable_outbox_subdirectory
        )
        return {
            document_id: self.get_document(
                f"{self._remarkable_outbox_subdirectory}/{document_id}"
            )
            for document_type, document_id in files
            if document_type == ReMarkablePathType.FILE
        }

    def list_documents(self) -> list[DocumentID]:
        """Return a list of document IDs.

        Returns:
            A list of document IDs.

        """
        files = self._rmapi.ls(self._remarkable_root_path)
        return [
            path for path_type, path in files if path_type == ReMarkablePathType.FILE
        ]

    def get_document(self, uid: DocumentID) -> fitz.Document:
        """Get a single document.

        This is the function that actually downloads the document from the
        reMarkable cloud using rmapi, converts it to a PDF using the `remarks`
        tool, and then opens the PDF with fitz.

        Arguments:
            uid: The ID of the document to get.

        Returns:
            The requested document.

        """
        abs_path = self._local_cache_root_path / uid
        self._rmapi.download(self._remarkable_root_path + "/" + uid, abs_path)
        zip_path = pathlib.Path(str(abs_path) + ".zip")
        pdf_path = pathlib.Path(str(abs_path) + ".pdf")
        self._remarks.rm_to_pdf(zip_path, pdf_path)
        if self._debug:
            print(zip_path, pdf_path)
        return fitz.open(pdf_path)  # type: ignore

    def has_document(self, uid: DocumentID) -> bool:
        """Check if a document exists.

        Arguments:
            uid: The ID of the document to check for.

        Returns:
            True if the document exists, False otherwise.

        """
        return (uid + ".pdf") in self.list_documents()

    def put_document(self, document: fitz.Document, uid: DocumentID):
        """Upload a document to the reMarkable.

        Arguments:
            document: The document to upload.
            uid: The ID of the document.

        """
        pdf_path = pathlib.Path(str(self._local_cache_root_path / uid) + ".pdf")
        document.save(pdf_path)
        self._rmapi.upload(pdf_path, self._remarkable_root_path)

    def delete_document(self, uid: DocumentID) -> bool:
        # Create a `_Archive` directory if it doesn't exist, inside the root:
        self._rmapi.mkdir(self._remarkable_root_path + "/_Archive")
        # Move the document to the `_Archive` directory:
        try:
            self._rmapi.move(
                f"{self._remarkable_root_path}/{uid}",
                f"{self._remarkable_root_path}/_Archive",
            )
        except Exception as _e:
            try:
                self._rmapi.move(
                    f"{self._remarkable_root_path}/{self._remarkable_outbox_subdirectory}/{uid}",
                    f"{self._remarkable_root_path}/_Archive",
                )
            except Exception as _e:
                return False
        return True

    def append_ruled_page_to_document(self, document: fitz.Document) -> fitz.Document:
        _page = document.new_page(-1)  # type: ignore
        return document
