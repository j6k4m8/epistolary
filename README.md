# 💌 epistolary

I find writing emails to be one of the most tedious and unpleasant tasks of my day. But I find the act of handwriting to be one of the most pleasant! The reMarkable is an e-ink tablet with a very pleasant writing experience. This software allows you to respond to emails by writing on the reMarkable, and then sends an OCR'd version of your writing to the recipient.

---

See [docs/Overview.md](docs/Overview.md) for an example!

---

This tool is designed to "print" emails to a PDF file (one thread per file), with a blank (ruled) page after each email.
You can write a reply to the email on the blank page, and Epistolary will convert your handwriting to text and send it as a reply to the email.

It is originally designed to be used with the [Remarkable](https://remarkable.com/) tablet, which is a great device for reading and annotating PDFs, but it should work with standalone PDFs, tablet devices, or scanned documents as well.

## Architecture

The tool comprises three main components:

-   `MailboxManager`: A class that manages the mailbox, and provides methods to get the next email to be printed, and to send a reply to an email.
-   `DocumentManager`: A class that manages the PDF document library.
-   `EpistolaryOrchestrator`: A class that manages the interaction between the `MailboxManager` and the `DocumentManager`, and provides OCR and main entry point functionality.

## Installation

### 0. Requirements

If you are using the tesseract OCR option, you must first install Tesseract for OCR. On MacOS, this can be done with `brew install tesseract`.

If you are using the OpenAI OCR option, you should configure your OpenAI API key globally, or you can pass it in a config to the TextExtractor directly.

If you are planning to use the reMarkable document management tools, you will also need to install [the `rmapi` tool](https://github.com/juruen/rmapi) and configure it with your reMarkable account.

### 1. Install the package

Then install Python dependencies:

```bash
uv install
```

### 2. Configure the package

Create a `~/.config/epistolary.json` file. (This is optional but recommended so that you don't have to put your password in the Python kernel directly.)

```json
{
    "email": "####",
    "password": "####",
    "imap": {
        "host": "####",
        "port": 993
    },
    "smtp": {
        "host": "####",
        "port": 587
    }
}
```

### 3. Run the package

Here's an example of a Python script that uses the package:

```python
from epistolary.orchestrator import EpistolaryOrchestrator
from epistolary.mailbox_manager import SMTPIMAPMailboxManager
from epistolary.document_manager.remarkable_document_manager import RemarkableDocumentManager
from epistolary.text_extractor.openai_text_extractor import OpenAITextExtractor

EO = EpistolaryOrchestrator(
    SMTPIMAPMailboxManager.from_file(),
    RemarkableDocumentManager(),
    text_extractor=OpenAITextExtractor(),
    debug=True,
)

EO.refresh_document_mailbox()
```

And to send:

```python
EO.send_outbox()
```

Note that the `SMTPIMAPMailboxManager` uses the `epistolary.json` file to get the email and password, and the `RemarkableDocumentManager` uses the `rmapi` tool to manage the reMarkable documents (which depends upon a `~/.rmapi` file with your reMarkable credentials).

If you do not choose to use the `#from_file()` method, you can pass in the email, password, and other parameters directly to the `SMTPIMAPMailboxManager` constructor.

## Known Limitations

-   No support for inline images or attachments yet... But it should be easy to add!
-   Spacing and formatting of the OCR'd text is not perfect, but it's usually good enough for a quick reply.
