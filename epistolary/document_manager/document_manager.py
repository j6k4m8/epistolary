"""Where documents live: an inbox to read and write on, an outbox for finished replies, and an archive."""

from typing import Protocol

import fitz


class DocumentManager(Protocol):
    def list_inbox(self) -> list[str]: ...

    def list_outbox(self) -> list[str]: ...

    def get(self, name: str, outbox: bool = False) -> fitz.Document: ...

    def put(self, name: str, doc: fitz.Document) -> None:
        """Add a document to the inbox."""
        ...

    def archive(self, name: str, outbox: bool = False) -> None: ...
