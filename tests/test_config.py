import stat

import pytest

from epistolary.config import DOCUMENT_MANAGERS, TEXT_EXTRACTORS, EpistolaryConfig, encode, load_class
from epistolary.document_manager import FilesystemDocumentManager, RemarkableDocumentManager
from epistolary.text_extractor import TesseractTextExtractor

MINIMAL = {
    "email": "e@x.com",
    "password": encode("s3cret"),
    "imap": {"host": "i", "port": 993},
    "smtp": {"host": "s", "port": 587},
}


def test_short_names_and_module_paths_both_resolve():
    conf = EpistolaryConfig.from_dict(MINIMAL)
    assert load_class(conf.document_manager, DOCUMENT_MANAGERS) is RemarkableDocumentManager
    assert load_class("files", DOCUMENT_MANAGERS) is FilesystemDocumentManager
    assert load_class(TEXT_EXTRACTORS["tesseract"], TEXT_EXTRACTORS) is TesseractTextExtractor


def test_file_round_trip_is_private_and_decodes_password(tmp_path):
    conf = EpistolaryConfig.from_dict({**MINIMAL, "limit": 3, "mailbox_manager": "gone"})
    path = tmp_path / "c.json"
    conf.to_file(path)
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert EpistolaryConfig.from_file(path) == conf and conf.limit == 3
    assert conf.mailbox().imap == ("i", 993, "e@x.com", "s3cret")


def test_plaintext_password_is_explained():
    with pytest.raises(ValueError, match="base64"):
        EpistolaryConfig.from_dict({**MINIMAL, "password": "hunter2!"}).mailbox()
