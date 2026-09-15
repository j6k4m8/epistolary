import fitz
from click.testing import CliRunner
from fakes import FakeExtractor, FakeMailbox, write_on

from epistolary import config
from epistolary.cli import cli
from epistolary.document_manager import FilesystemDocumentManager


def test_send_dry_run_shows_and_sends_nothing(tmp_path, monkeypatch):
    docs = FilesystemDocumentManager(tmp_path / "docs")
    doc = fitz.open()
    doc.new_page()
    write_on(doc)
    doc.save(docs.outbox / "bob@example.com:::Lunch.pdf")
    conf = tmp_path / "c.json"
    config.EpistolaryConfig("e@x.com", config.encode("pw"), "i", 993, "s", 587, document_manager="files").to_file(conf)
    monkeypatch.setattr(
        config, "load_class", lambda spec, options: {"files": lambda: docs, "openai": FakeExtractor}[spec]
    )
    mailbox = FakeMailbox()
    monkeypatch.setattr(config.EpistolaryConfig, "mailbox", lambda self: mailbox)

    result = CliRunner().invoke(cli, ["-c", str(conf), "send", "--dry-run"])
    assert result.exit_code == 0, result.output
    assert "To: bob@example.com\nSubject: Lunch\n\ntranscribed" in result.output and "0 sent." in result.output
    assert docs.list_outbox() == ["bob@example.com:::Lunch"] and mailbox.sent == []

    result = CliRunner().invoke(cli, ["-c", str(conf), "init"])
    assert result.exit_code == 1 and "already exists" in result.output
