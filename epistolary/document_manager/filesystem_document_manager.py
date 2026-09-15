"""Documents as PDFs in a directory."""

from pathlib import Path

import fitz


class FilesystemDocumentManager:
    def __init__(self, root: str | Path = "~/Epistolary", outbox: str = "Outbox", archive: str = "_Archive"):
        self.root = Path(root).expanduser()
        self.outbox = self.root / outbox
        self.archive_dir = self.root / archive
        for d in (self.root, self.outbox, self.archive_dir):
            d.mkdir(parents=True, exist_ok=True)

    def _path(self, name: str, outbox: bool) -> Path:
        return (self.outbox if outbox else self.root) / f"{name}.pdf"

    def list_inbox(self) -> list[str]:
        return sorted(p.stem for p in self.root.glob("*.pdf"))

    def list_outbox(self) -> list[str]:
        return sorted(p.stem for p in self.outbox.glob("*.pdf"))

    def get(self, name: str, outbox: bool = False) -> fitz.Document:
        return fitz.open(self._path(name, outbox))

    def put(self, name: str, doc: fitz.Document) -> None:
        doc.save(self._path(name, False))

    def archive(self, name: str, outbox: bool = False) -> None:
        self._path(name, outbox).rename(self.archive_dir / f"{name}.pdf")
