import pytesseract
import fitz
from PIL import Image

from .text_extractor import TextExtractor


class TesseractTextExtractor(TextExtractor):
    """A class that extracts text from documents using Tesseract."""

    def extract_text_from_page(self, page: fitz.Page) -> str:
        """Extract text from a page.

        Arguments:
            page: The page to extract text from.

        Returns:
            The extracted text.

        """
        # Convert the PDF page to be readable as an image, using the
        # fitz library.
        pix = page.get_pixmap()
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        return pytesseract.image_to_string(img)
