from pypdf import PageObject

EmailID = str
DocumentID = str


class Document:
    pages: list[PageObject]
