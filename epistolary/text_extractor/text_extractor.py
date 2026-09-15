from typing import Protocol

import fitz


class TextExtractor(Protocol):
    def extract(self, page: fitz.Page) -> str:
        """The handwriting on a page as text, or an empty string if there is none."""
        ...
