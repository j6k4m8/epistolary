from epistolary.document_manager import RemarkableDocumentManager


class Offline(RemarkableDocumentManager):
    def __init__(self):
        self.calls = []
        super().__init__()

    def _run(self, *args):
        self.calls.append(args)
        return "[d]\tOutbox\n[f]\tHello - Ann\n[f]\tTabs\tin name\n" if args[0] == "ls" else ""


def test_listing_parses_files_only_and_setup_is_idempotent():
    rm = Offline()
    assert rm.calls == [("mkdir", "Emails"), ("mkdir", "Emails/Outbox"), ("mkdir", "Emails/_Archive")]
    assert rm.list_inbox() == ["Hello - Ann", "Tabs\tin name"]
    rm.archive("Hello - Ann", outbox=True)
    assert rm.calls[-1] == ("mv", "Emails/Outbox/Hello - Ann", "Emails/_Archive")
