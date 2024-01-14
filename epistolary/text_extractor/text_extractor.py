from typing import Protocol

from pypdf import PageObject


class TextExtractor(Protocol):
    """A protocol for classes that extract text from documents."""

    def extract_text_from_page(self, page: PageObject) -> str:
        """Extract text from a page.

        Arguments:
            page: The page to extract text from.

        Returns:
            The extracted text.

        """
        ...
