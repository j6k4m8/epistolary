import base64
from fitz import Page
from openai import OpenAI

from .text_extractor import TextExtractor


class OpenAITextExtractor(TextExtractor):
    def __init__(self, client: OpenAI | None = None, api_key: str | None = None):
        self._client = client or (OpenAI(api_key=api_key) if api_key else OpenAI())

    def extract_text_from_page(self, page: Page) -> str:
        png = page.get_pixmap()
        png.shrink(4)
        png_bytes = png.tobytes("png")
        png_b64 = base64.b64encode(png_bytes).decode("utf-8")

        res = self._client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a powerful handwriting parser robot. You respond ONLY with the transcribed text, NEVER with any other information, questions, or discussion.",
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "What is the (formatted) text content of this hand-written message?",
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{png_b64}",
                            },
                        },
                    ],
                },
            ],
        )
        if len(res.choices) and res.choices[0].message.role == "assistant":
            return (
                res.choices[0].message.content if res.choices[0].message.content else ""
            )
        raise ValueError("No response from OpenAI")
