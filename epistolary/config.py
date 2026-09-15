"""The config file, and building the pieces it describes."""

import base64
import binascii
import importlib
import json
import logging
import os
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path

log = logging.getLogger(__name__)

DEFAULT_PATH = Path("~/.config/epistolary.json")

DOCUMENT_MANAGERS = {
    "remarkable": "epistolary.document_manager:RemarkableDocumentManager",
    "files": "epistolary.document_manager:FilesystemDocumentManager",
}
TEXT_EXTRACTORS = {
    "openai": "epistolary.text_extractor:OpenAITextExtractor",
    "tesseract": "epistolary.text_extractor:TesseractTextExtractor",
}


def load_class(spec: str, options: dict[str, str]) -> type:
    """A class from a short name in `options` or from a `module:Class` string."""
    module, _, name = options.get(spec, spec).partition(":")
    return getattr(importlib.import_module(module), name)


def write_private(path: Path, text: str) -> None:
    """Write a file only its owner can read, replacing any old one in a single step."""
    path = path.resolve()  # write through a symlink, not over it
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(path.name + ".tmp")
    partial.unlink(missing_ok=True)  # the mode below only applies to a new file
    with open(os.open(partial, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600), "w") as f:
        f.write(text)
    os.replace(partial, path)


def encode(secret: str) -> str:
    """How passwords are stored in the file. This is obfuscation, not encryption."""
    return base64.b64encode(secret.encode()).decode()


def _decode(secret: str | None) -> str | None:
    if not secret:
        return None
    try:
        return base64.b64decode(secret, validate=True).decode()
    except (binascii.Error, UnicodeDecodeError):
        raise ValueError("passwords in the config file are base64 encoded since 0.3.0; see the README") from None


@dataclass
class EpistolaryConfig:
    email: str
    password: str  # base64, see `encode`
    imap_host: str
    imap_port: int
    smtp_host: str
    smtp_port: int
    smtp_username: str | None = None
    smtp_password: str | None = None  # base64, see `encode`
    ignore_marketing_emails: bool = True
    document_manager: str = "remarkable"
    document_manager_kwargs: dict = field(default_factory=dict)
    text_extractor: str = "openai"
    text_extractor_kwargs: dict = field(default_factory=dict)
    folder: str = "INBOX"
    limit: int = 10

    @classmethod
    def from_dict(cls, raw: dict) -> "EpistolaryConfig":
        known = {f.name for f in fields(cls)}
        if unknown := set(raw) - known - {"imap", "smtp"}:
            log.warning("ignoring unknown config keys: %s", ", ".join(sorted(unknown)))
        flat = {k: v for k, v in raw.items() if k in known}
        for server in ("imap", "smtp"):
            flat[f"{server}_host"], flat[f"{server}_port"] = raw[server]["host"], raw[server]["port"]
        return cls(**flat)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["imap"] = {"host": d.pop("imap_host"), "port": d.pop("imap_port")}
        d["smtp"] = {"host": d.pop("smtp_host"), "port": d.pop("smtp_port")}
        return d

    @classmethod
    def from_file(cls, path: str | Path = DEFAULT_PATH) -> "EpistolaryConfig":
        return cls.from_dict(json.loads(Path(path).expanduser().read_text()))

    def to_file(self, path: str | Path = DEFAULT_PATH) -> None:
        write_private(Path(path).expanduser(), json.dumps(self.to_dict(), indent=2))

    def mailbox(self):
        from .mailbox_manager import SMTPIMAPMailboxManager

        return SMTPIMAPMailboxManager(
            self.imap_host,
            self.imap_port,
            self.email,
            _decode(self.password),
            self.smtp_host,
            self.smtp_port,
            self.smtp_username,
            _decode(self.smtp_password),
        )

    def orchestrator(self, state_path: str | Path):
        from .orchestrator import EpistolaryOrchestrator

        return EpistolaryOrchestrator(
            self.mailbox(),
            load_class(self.document_manager, DOCUMENT_MANAGERS)(**self.document_manager_kwargs),
            load_class(self.text_extractor, TEXT_EXTRACTORS)(**self.text_extractor_kwargs),
            state_path,
            folder=self.folder,
            limit=self.limit,
            ignore_marketing=self.ignore_marketing_emails,
        )
