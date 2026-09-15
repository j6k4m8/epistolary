from epistolary.mailbox_manager import Email


def parse(raw: str) -> Email:
    return Email.from_bytes(7, raw.replace("\n", "\r\n").encode())


def test_single_part_plain_text():
    e = parse("From: a@b.com\nSubject: hi\nContent-Type: text/plain\n\nHello there\n")
    assert (e.uid, e.text, e.html, e.reply_to) == (7, "Hello there\n", "", "a@b.com")


def test_transfer_encodings_are_decoded():
    e = parse(
        "From: a@b.com\nSubject: qp\nContent-Type: multipart/alternative; boundary=X\n\n"
        "--X\nContent-Type: text/plain; charset=utf-8\nContent-Transfer-Encoding: quoted-printable\n\n"
        "Let=E2=80=99s meet =\ntomorrow\n"
        "--X\nContent-Type: text/html\nContent-Transfer-Encoding: base64\n\nPHA+aGk8L3A+\n--X--\n"
    )
    assert e.text.strip() == "Let’s meet tomorrow"
    assert e.html.strip() == "<p>hi</p>"


def test_bulk_mail_is_the_header_not_the_body():
    assert not parse("From: a@b.com\nContent-Type: text/plain\n\nplease unsubscribe me from this thread\n").bulk
    assert parse("From: a@b.com\nlist-unsubscribe: <mailto:x@y>\nContent-Type: text/plain\n\nhi\n").bulk


def test_headers_are_decoded_and_defaulted():
    e = parse(
        "From: =?UTF-8?Q?J=C3=B6rg?= <j@x.de>\nReply-To: r@x.de\nMessage-ID: <m1@x>\nContent-Type: text/plain\n\nx\n"
    )
    assert (e.sender, e.reply_to, e.subject, e.message_id) == ("Jörg <j@x.de>", "r@x.de", "(no subject)", "<m1@x>")
