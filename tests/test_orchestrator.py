import json

import fitz
import pytest
from fakes import ANN, FakeDocuments, FakeExtractor, FakeMailbox, email, write_on

from epistolary.orchestrator import EpistolaryOrchestrator, _name_for


@pytest.fixture
def system(tmp_path):
    mailbox = FakeMailbox(email(1), email(2), email(3, "Deals", bulk=True))
    docs = FakeDocuments()
    return EpistolaryOrchestrator(mailbox, docs, FakeExtractor(), tmp_path / "state.json"), mailbox, docs


def test_receive_uploads_once_dedupes_names_and_skips_bulk(system):
    o, mailbox, docs = system
    assert o.receive() == ["Hello - Ann", "Hello - Ann (2)"]
    assert docs.inbox["Hello - Ann"].page_count == 2
    assert o.state["skipped"] == [3]
    assert o.receive() == []
    assert json.loads(o.state_path.read_text())["docs"]["Hello - Ann"]["uid"] == 1


def test_receive_takes_the_newest_limit(tmp_path):
    mailbox = FakeMailbox(*(email(u, f"S{u}") for u in range(1, 6)))
    o = EpistolaryOrchestrator(mailbox, FakeDocuments(), FakeExtractor(), tmp_path / "s.json", limit=2)
    assert o.receive() == ["S4 - Ann", "S5 - Ann"]
    assert o.receive() == ["S2 - Ann", "S3 - Ann"]


def test_send_replies_archives_and_flags(system):
    o, mailbox, docs = system
    o.receive()
    docs.move_to_outbox("Hello - Ann")
    write_on(docs.outbox["Hello - Ann"])
    assert o.send() == ["Hello - Ann"]
    assert mailbox.sent == [(ANN, "Re: Hello", "transcribed", "<1@x>")]
    assert docs.archived == ["Hello - Ann"] and mailbox.answered == [1]
    assert o.receive() == []  # the answered email stays known


def test_send_never_resends_when_archiving_fails(system):
    o, mailbox, docs = system
    o.receive()
    docs.move_to_outbox("Hello - Ann")
    write_on(docs.outbox["Hello - Ann"])
    docs.fail_archive = True
    assert o.send() == ["Hello - Ann"] and len(mailbox.sent) == 1
    assert o.send() == [] and len(mailbox.sent) == 1
    docs.fail_archive = False
    assert o.send() == [] and len(mailbox.sent) == 1 and docs.archived == ["Hello - Ann"]


def test_send_transcribes_every_written_reply_page(system):
    o, mailbox, docs = system
    o.receive()
    docs.move_to_outbox("Hello - Ann")
    doc = docs.outbox["Hello - Ann"]
    doc.new_page()
    write_on(doc, 1)
    write_on(doc, 2)
    o.send()
    assert mailbox.sent[0][2] == "transcribed\n\ntranscribed"


def test_send_skips_blank_pages_and_honors_confirm(system):
    o, mailbox, docs = system
    o.receive()
    docs.move_to_outbox("Hello - Ann")
    assert o.send() == [] and docs.list_outbox() == ["Hello - Ann"]  # the email's own page is not a reply
    write_on(docs.outbox["Hello - Ann"])
    assert o.send(confirm=lambda *_: False) == [] and mailbox.sent == []
    assert o.send(confirm=lambda to, subject, body: body == "transcribed") == ["Hello - Ann"]


def test_send_new_message_from_name(system):
    o, mailbox, docs = system
    doc = fitz.open()
    doc.new_page()
    write_on(doc)
    docs.outbox["bob@example.com:::Lunch?"] = doc
    docs.outbox["%22Old%20Style%22%20%3Cold@x.com%3E:::Hi"] = doc  # named by 0.2
    docs.outbox["not a reply"] = doc
    assert o.send() == ["%22Old%20Style%22%20%3Cold@x.com%3E:::Hi", "bob@example.com:::Lunch?"]
    assert mailbox.sent[1] == ("bob@example.com", "Lunch?", "transcribed", None)
    assert mailbox.sent[0][0] == '"Old Style" <old@x.com>'
    assert docs.list_outbox() == ["not a reply"] and o.state["docs"] == {}


def test_prune_archives_documents_whose_email_was_read_elsewhere(system):
    o, mailbox, docs = system
    o.receive()
    del mailbox.emails[1]
    assert o.prune() == ["Hello - Ann"]
    assert docs.list_inbox() == ["Hello - Ann (2)"]


def test_names_are_safe_and_short():
    assert _name_for(email(1, "a/b\\c\tsee", text="")) == "a b c see - Ann"
    long = _name_for(email(1, "- x " * 40))
    assert len(long) <= 80 and not long.endswith((" ", "-", "."))
    e = email(1)
    plain = e.__class__(**{**e.__dict__, "sender": "a@b.com, c@d.com"})
    assert _name_for(plain) == "Hello - a@b.com"
