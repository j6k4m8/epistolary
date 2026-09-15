import base64

import fitz
from openai import OpenAI

PROMPT = (
    "Transcribe the handwriting in this image. Reply with the transcribed text only, "
    "keeping the writer's line breaks and paragraphs. If there is no writing, reply with nothing."
)


class OpenAITextExtractor:
    """Sends a rendering of the page to an OpenAI vision model."""

    def __init__(self, client: OpenAI | None = None, api_key: str | None = None, model: str = "gpt-4o", dpi: int = 150):
        self.client = client
        self.api_key = api_key
        self.model = model
        self.dpi = dpi

    def extract(self, page: fitz.Page) -> str:
        self.client = self.client or OpenAI(api_key=self.api_key)  # here, so that `receive` needs no key
        png = base64.b64encode(page.get_pixmap(dpi=self.dpi).tobytes("png")).decode()
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": PROMPT},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{png}"}},
                    ],
                }
            ],
        )
        return (response.choices[0].message.content or "").strip()
