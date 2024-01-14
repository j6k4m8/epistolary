# 💌 epistolary

I find writing emails to be one of the most tedious and unpleasant tasks of my day. But I find the act of handwriting to be one of the most pleasant! The reMarkable is an e-ink tablet with a very pleasant writing experience. This software allows you to respond to emails by writing on the reMarkable, and then sends an OCR'd version of your writing to the recipient.

---

This tool is designed to "print" emails to a PDF file (one thread per file), with a blank (ruled) page after each email.
You can write a reply to the email on the blank page, and Epistolary will convert your handwriting to text and send it as a reply to the email.

It is originally designed to be used with the [Remarkable](https://remarkable.com/) tablet, which is a great device for reading and annotating PDFs, but it should work with standalone PDFs, tablet devices, or scanned documents as well.

## Architecture

The tool comprises three main components:

-   `MailboxManager`: A class that manages the mailbox, and provides methods to get the next email to be printed, and to send a reply to an email.
-   `DocumentManager`: A class that manages the PDF document library.
-   `EpistolaryOrchestrator`: A class that manages the interaction between the `MailboxManager` and the `DocumentManager`, and provides OCR and main entry point functionality.
