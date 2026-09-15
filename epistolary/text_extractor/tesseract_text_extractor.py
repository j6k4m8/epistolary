import fitz
import pytesseract
from PIL import Image


class TesseractTextExtractor:
    """Local OCR. Needs the tesseract binary on PATH."""

    def __init__(self, dpi: int = 300):
        self.dpi = dpi

    def extract(self, page: fitz.Page) -> str:
        pix = page.get_pixmap(dpi=self.dpi)
        image = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        return pytesseract.image_to_string(image).strip()
