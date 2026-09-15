# CHANGELOG

## v0.3.0 (September 14, 2026)

-   Breaking
    -   Documents are named `Subject - Sender`, and what has been uploaded is tracked in a state file next to the config. Mail is never marked read, and nothing is archived until it is sent; `receive --prune` archives documents whose email was read elsewhere, when asked.
    -   `send` shows each transcription and asks first. `--yes` skips the question, `--dry-run` sends nothing.
    -   Marketing detection uses the `List-Unsubscribe` header instead of the word "unsubscribe" in the body.
    -   `smtp_password` in the config file is base64-encoded like `password`.
    -   Send or archive your `Outbox` before upgrading. Old-style names there still send, as new messages rather than threaded replies.
    -   Python API: `epistolary.epiconfig` is `epistolary.config`; `refresh_document_mailbox()` and `send_outbox()` are `receive()` and `send()`; `TextExtractor.extract_text_from_page` is `extract`; `FilesystemDocumentManager(root_path)` is `(root)`; the orchestrator takes a `state_path`; `RemarkableDocumentManager` takes `root`, `outbox`, `archive`, and `rmapi`; `OpenAITextExtractor` takes `model` and `dpi` instead of `page_shrink_factor`; `EpistolaryConfig.password` is the stored (encoded) value. `SMTPIMAPMailboxManager.from_file` is gone; use `EpistolaryConfig.from_file().mailbox()`.
    -   The default OpenAI model is `gpt-4o`, was `gpt-4o-mini`. Set `"text_extractor_kwargs": {"model": "gpt-4o-mini"}` to keep the old one.
    -   `remarks` is no longer a hard dependency. `uv sync` installs it; PyPI installs add it by hand for reMarkable support. `redbox` and `redmail` are replaced by the standard library. Python 3.12 or newer.
-   Fixes
    -   Single-part, quoted-printable, base64, and non-ASCII emails render correctly, and senders no longer vanish from the PDF.
    -   Replies carry a real `In-Reply-To`, keep their line breaks, and go to `Reply-To` when set. A reply whose archiving fails is not sent twice.
    -   Every page written after the email is transcribed, from a 150 dpi image instead of one shrunk to 153 by 198 pixels.
    -   `init` tests the login for real, SMTP on port 465 works, connections time out, and the config and state files are written `0600`.
    -   `pymupdf` is declared and `boto3` is gone.

## v0.2.0 (September 05, 2024)

-   Features
    -   Added the command-line `epistolary` tool, which can be used to interact with the package from the command line (#6)
-   Housekeeping
    -   Added GitHub Actions CI/CD for PyPI
