"""Rendering an email to pages, adding a page to write on, and telling whether a page was written on."""

import html
import io

import fitz

from .mailbox_manager import Email

MARGIN = 36  # half an inch
LINE_SPACING = 24


def email_to_pdf(email: Email) -> fitz.Document:
    """Sender and subject as a heading, then the plain-text body, or the HTML one if that is all there is."""
    text = html.escape(email.text).replace("\n", "<br>")
    body = f"<p>{text}</p>" if email.text.strip() else email.html
    story = fitz.Story(f"<p><b>{html.escape(email.sender)}</b></p><p><b>{html.escape(email.subject)}</b></p><hr>{body}")
    page = fitz.paper_rect("letter")
    buffer = io.BytesIO()
    writer = fitz.DocumentWriter(buffer)
    for _ in range(100):  # a page cap, in case the story never fits
        device = writer.begin_page(page)
        more, _ = story.place(page + (MARGIN, MARGIN, -MARGIN, -MARGIN))
        story.draw(device)
        writer.end_page()
        if not more:
            break
    writer.close()
    return fitz.open(stream=buffer.getvalue(), filetype="pdf")


def append_ruled_page(doc: fitz.Document) -> None:
    """A lined page the size of the last page, for the reply."""
    rect = doc[-1].rect
    page = doc.new_page(width=rect.width, height=rect.height)
    for y in range(2 * MARGIN, int(rect.height) - MARGIN, LINE_SPACING):
        page.draw_line((MARGIN, y), (rect.width - MARGIN, y), color=(0.75, 0.75, 0.75), width=0.5)


def has_ink(page: fitz.Page, minimum: float = 0.00005) -> bool:
    """True if at least `minimum` of the page's pixels are darker than the ruling.

    One word in a 0.6 pt ballpoint stroke is about twice the default; the ruling alone is exactly zero.
    """
    pix = page.get_pixmap(dpi=72, colorspace=fitz.csGRAY)
    dark = len(pix.samples.translate(None, bytes(range(200, 256))))  # drops every byte from 200 up
    return dark / len(pix.samples) >= minimum
