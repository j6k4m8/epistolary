from fitz import Page

EmailID = str
DocumentID = str


class Document:
    pages: list[Page]

    def __init__(self, pages: list[Page] | None = None):
        """Initialize the document.

        Arguments:
            pages: The pages of the document.

        """
        self.pages = pages or []
