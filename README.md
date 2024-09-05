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

Optionally, install Python dependencies:

```bash
uv install
```

(If you do not do this explicitly, the package will install the dependencies automatically when you run the package.)

### 2. Configure the package

This can be done in one of two ways: Manually, editing a config file; or by running the `init` wizard.

We STRONGLY recommend using the `init` wizard, as it will guide you through the process of setting up the config file.

#### Option 1: Run the `init` wizard

```bash
uv run epistolary init
```

This will guide you through the process of setting up the config file, passing in email credentials and the configurations for the document managers you'd like to use. You can also specify the location of a config file by passing the `--config`/`-c` flag:

```bash
uv run epistolary --config ~/.config/epistolary.json init
```

#### Option 2: Manually edit the config file

Create a `~/.config/epistolary.json` file. Here's an example of what it might look like:

```jsonc
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
    },

    // Optional (defaults shown)

    "smtp_username": null,
    "smtp_password": null,

    "ignore_marketing_emails": true,
    "document_manager": "epistolary.document_manager.remarkable_document_manager:RemarkableDocumentManager",
    "text_extractor": "epistolary.text_extractor.openai_text_extractor:OpenAITextExtractor"
}
```

## Usage

We recommend doing this with the `epistolary` cli:

```bash
# Get new emails and "print" them to your device:
uv run epistolary receive
```

```bash
# Send the replies you've written:
uv run epistolary send
```

Alternatively, here's an example of a Python script that does the same thing as the above commands:

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

```

To receive emails:

```python
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
