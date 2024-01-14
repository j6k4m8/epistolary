from typing import Protocol
from rmapy.api import Client, Folder, Document as RmDocument


_DEFAULT_SUBDIRECTORY = "mail"


class Message:
    """A class to represent a mail message."""

    def __init__(self, sender: str, recipient: str, subject: str, body: str):
        """Create a new mail message."""
        self.sender = sender
        self.recipient = recipient
        self.subject = subject
        self.body = body


class Document:
    """A class to represent a document."""

    def __init__(self, name: str, pages: list[str]):
        """Create a new document."""
        self.name = name
        self.pages = pages


class Mailbox(Protocol):
    """A protocol for mailboxes."""

    def get_new_mail(self) -> list[Message]:
        """Get new mail messages."""
        ...


class Tablet(Protocol):
    """A class to manage a tablet."""

    def has_directory(self, directory: str) -> bool:
        """Check if a directory exists."""
        ...

    def create_directory(self, directory: str):
        """Create a directory."""
        ...

    def get_all_documents_in_directory(self, directory: str) -> list[Document]:
        """Get all documents in a directory."""
        ...

    def delete_documents_in_directory(self, directory: str):
        """Delete all documents in a directory."""
        ...

    def upload_documents(self, documents: list[Document], directory: str):
        """Upload documents to a directory."""
        ...


class RmapyTablet(Tablet):
    def __init__(self):
        """Create a new tablet."""
        self._client = Client()
        self._client.renew_token()
        assert self._client.is_auth(), "Failed to authenticate with reMarkable cloud"

    def has_directory(self, directory: str) -> bool:
        """Check if a directory exists."""
        all_collection = self._client.get_meta_items()
        folders = [item for item in all_collection if isinstance(item, Folder)]
        root_folders = [folder for folder in folders if folder.Parent == ""]
        return any(folder.VissibleName == directory for folder in root_folders)

    def create_directory(self, directory: str):
        """Create a directory."""
        self._client.create_folder(directory)

    def get_all_documents_in_directory(self, directory: str) -> list[Document]:
        """Get all documents in a directory."""
        # Get the folder:
        all_collection = self._client.get_meta_items()
        folders = [item for item in all_collection if isinstance(item, Folder)]
        root_folders = [folder for folder in folders if folder.Parent == ""]
        mail_folder = [
            folder for folder in root_folders if folder.VissibleName == directory
        ]

    def delete_documents_in_directory(self, directory: str):
        """Delete all documents in a directory."""
        ...

    def upload_documents(self, documents: list[Document], directory: str):
        """Upload documents to a directory."""
        ...


class TabletSynchronizer:
    """A class to manage synchronizing mail documents with the tablet."""

    def __init__(
        self,
        mailbox: Mailbox,
        tablet: Tablet,
        directory: str = _DEFAULT_SUBDIRECTORY,
    ):
        """Create a new synchronizer pointing to a specific mailbox and tablet."""
        self._mailbox = mailbox
        self._tablet = tablet
        self._directory = directory

    def synchronize(self):
        """Synchronize the mail documents with the tablet.

        * OCR's any document with a reply.
        * Deletes all old documents.
        * Uploads fresh inbox.

        """
        all_docs = self._tablet.get_all_documents_in_directory(self._subdirectory)
        # Get the documents with a reply -- i.e., those where the last page is
        # a handwritten page.
        reply_docs = ...  # TODO
        # Send replies:
        for doc in reply_docs:
            # Get the reply:
            reply = ...

        # Next we get a fresh copy of the inbox. If we fail to fetch the mail,
        # we won't delete the old inbox.
        # Get a fresh inbox:
        new_mail = self._mailbox.get_new_mail()
        # Delete all old documents.
        self._tablet.delete_documents_in_directory(self._subdirectory)

        # Upload the new inbox:
        new_docs = [self.mail_to_document(msg) for msg in new_mail]
        self._tablet.upload_documents(new_docs, self._subdirectory)

    def mail_to_document(self, msg: Message) -> Document:
        """Convert a mail message to a document."""
        # TODO
        pass
