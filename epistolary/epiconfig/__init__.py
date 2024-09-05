import base64
import json
import pathlib
from typing import Optional
import importlib


def _get_module_from_string(module_str):
    # The string should be in the format of 'module.submodule:class'
    module_str, class_str = module_str.split(":")
    module = importlib.import_module(module_str)
    return getattr(module, class_str)


# Schema:
_CONFIG_SCHEMA = {
    "imap": {
        "host": str,
        "port": int,
    },
    "email": str,
    "password": str,
    "smtp": {
        "host": str,
        "port": int,
    },
    "smtp_username": Optional[str],
    "smtp_password": Optional[str],
    "ignore_marketing_emails": Optional[bool],
    "mailbox_manager": str,
    "text_extractor": str,
    "document_manager": str,
}

_MAILBOX_MANAGER_OPTIONS = {
    "default": "epistolary.mailbox_manager.smtpimap_mailbox_manager:SMTPIMAPMailboxManager",
}
_DEFAULT_MAILBOX_MANAGER = "default"


_TEXT_EXTRACTOR_OPTIONS = {
    "openai": "epistolary.text_extractor.openai_text_extractor:OpenAITextExtractor",
    "tesseract": "epistolary.text_extractor.tesseract_text_extractor:TesseractTextExtractor",
}
_DEFAULT_TEXT_EXTRACTOR = "openai"

_DOCUMENT_MANAGER_OPTIONS = {
    "files": "epistolary.document_manager.filesystem_document_manager:FilesystemDocumentManager",
    "remarkable": "epistolary.document_manager.remarkable_document_manager:RemarkableDocumentManager",
}
_DEFAULT_DOCUMENT_MANAGER = "remarkable"


class EpistolaryConfig:
    """The configuration for Epistolary."""

    def __init__(
        self,
        imap_host: str,
        imap_port: int,
        email: str,
        password: str,
        smtp_host: str,
        smtp_port: int,
        smtp_username: Optional[str] = None,
        smtp_password: Optional[str] = None,
        ignore_marketing_emails: Optional[bool] = True,
        document_manager: str = _DEFAULT_DOCUMENT_MANAGER,
        text_extractor: str = _DEFAULT_TEXT_EXTRACTOR,
    ):
        """Create a new EpistolaryConfig object.

        Arguments:
            imap_host (str): The hostname of the IMAP server.
            imap_port (int): The port number of the IMAP server.
            email (str): The email address.
            password (str): The password.
            smtp_host (str): The hostname of the SMTP server.
            smtp_port (int): The port number of the SMTP server.
            smtp_username (str, optional): The username for the SMTP server.
                Defaults to None.
            smtp_password (str, optional): The password for the SMTP server.
                Defaults to None.
            ignore_marketing_emails (bool, optional): Whether to ignore
                marketing emails. Defaults to True.
            document_manager (str, optional): The document manager to use.
                Defaults to _DEFAULT_DOCUMENT_MANAGER.
            text_extractor (str, optional): The text extractor to use.
                Defaults to _DEFAULT_TEXT_EXTRACTOR.

        """
        self.imap_host = imap_host
        self.imap_port = imap_port
        self.email = email
        self._password = password
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_username = smtp_username
        self.smtp_password = smtp_password
        self.ignore_marketing_emails = ignore_marketing_emails
        self.document_manager = document_manager
        self.text_extractor = text_extractor

    @property
    def password(self) -> str:
        """Get the decoded password."""
        return base64.b64decode(self._password.encode("utf-8")).decode("utf-8")

    @classmethod
    def from_dict(cls, config: dict) -> "EpistolaryConfig":
        """Create a new EpistolaryConfig object from a dictionary.

        Arguments:
            config (dict): The configuration dictionary.

        Returns:
            EpistolaryConfig: The configuration object.

        """
        return cls(
            imap_host=config["imap"]["host"],
            imap_port=config["imap"]["port"],
            email=config["email"],
            password=config["password"],
            smtp_host=config["smtp"]["host"],
            smtp_port=config["smtp"]["port"],
            smtp_username=config.get("smtp_username"),
            smtp_password=config.get("smtp_password"),
            ignore_marketing_emails=config.get("ignore_marketing_emails", True),
            document_manager=config.get("document_manager", _DEFAULT_DOCUMENT_MANAGER),
            text_extractor=config.get("text_extractor", _DEFAULT_TEXT_EXTRACTOR),
        )

    @classmethod
    def from_file(
        cls, path: str | pathlib.Path = "~/.config/epistolary.json"
    ) -> "EpistolaryConfig":
        """Create a new EpistolaryConfig object from a file.

        Arguments:
            path (str | pathlib.Path, optional): The path to the file.
                Defaults to "~/.config/epistolary.json".

        Returns:
            EpistolaryConfig: The configuration object.

        """
        path = pathlib.Path(path).expanduser().resolve()
        with open(path) as f:
            config = json.load(f)
        return cls.from_dict(config)

    def to_dict(self) -> dict:
        """Convert the configuration object to a dictionary.

        Returns:
            dict: The configuration dictionary.

        """
        return {
            "imap": {
                "host": self.imap_host,
                "port": self.imap_port,
            },
            "email": self.email,
            "password": self._password,
            "smtp": {
                "host": self.smtp_host,
                "port": self.smtp_port,
            },
            "smtp_username": self.smtp_username,
            "smtp_password": self.smtp_password,
            "ignore_marketing_emails": self.ignore_marketing_emails,
            "document_manager": self.document_manager,
            "text_extractor": self.text_extractor,
        }

    def to_file(self, path: str | pathlib.Path = "~/.config/epistolary.json") -> None:
        """Write the configuration object to a file.

        Arguments:
            path (str | pathlib.Path, optional): The path to the file.
                Defaults to "~/.config/epistolary.json".

        """
        path = pathlib.Path(path).expanduser().resolve()
        with open(path, "w") as f:
            json.dump(self.to_dict(), f)
