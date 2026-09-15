from epistolary.mailbox_manager import Email
from epistolary.pdf import append_ruled_page, email_to_pdf, has_ink


def make(text: str = "hello") -> Email:
    return Email(1, "<m@x>", '"J M" <j@x.com>', "j@x.com", "Sub < & >", text, "")


def test_email_to_pdf_escapes_markup_and_paginates():
    doc = email_to_pdf(make("a < b & c\n" * 400))
    assert doc.page_count > 1
    first = doc[0].get_text()
    assert '"J M" <j@x.com>' in first and "Sub < & >" in first and "a < b & c" in first


def test_ruled_page_matches_size_and_reads_as_blank_until_written_on():
    doc = email_to_pdf(make())
    append_ruled_page(doc)
    page = doc[1]
    assert doc.page_count == 2 and page.rect == doc[0].rect
    assert not has_ink(page)
    for x in range(72, 102, 10):  # one word in a thin ballpoint stroke
        page.draw_bezier((x, 200), (x + 3, 190), (x + 7, 210), (x + 10, 200), color=(0, 0, 0), width=0.6)
    assert has_ink(page)
