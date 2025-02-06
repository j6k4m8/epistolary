import base64
import pathlib

import click

from ..epiconfig import (
    _DEFAULT_DOCUMENT_MANAGER,
    _DEFAULT_TEXT_EXTRACTOR,
    _DOCUMENT_MANAGER_OPTIONS,
    _TEXT_EXTRACTOR_OPTIONS,
    EpistolaryConfig,
    _get_module_from_string,
)
from ..mailbox_manager.smtpimap_mailbox_manager import SMTPIMAPMailboxManager
from ..mailbox_manager.gmail_mailbox_manager import GmailMailboxManager
from ..orchestrator import EpistolaryOrchestrator

_MAILBOX_MANAGER_OPTIONS = {
    "smtpimap": "epistolary.mailbox_manager.smtpimap_mailbox_manager:SMTPIMAPMailboxManager",
    "gmail": "epistolary.mailbox_manager.gmail_mailbox_manager:GmailMailboxManager",
}
_DEFAULT_MAILBOX_MANAGER = "smtpimap"

@click.group()
@click.option(
    "--config",
    "-c",
    default="~/.config/epistolary.json",
    help="Path to the config file.",
)
@click.pass_context
def cli(ctx, config):
    ctx.ensure_object(dict)
    ctx.obj["config_file_path"] = pathlib.Path(config).expanduser()


@cli.command()
@click.pass_context
def init(ctx):
    # First we need to check if the config file exists.
    config_path = ctx.obj["config_file_path"]
    if config_path.exists():
        click.echo(
            click.style(f"Config file already exists at {config_path}", fg="red"),
            err=True,
        )
        return

    # If the config file does not exist, we can now prompt the user for the
    # necessary information.
    click.echo(f"Creating a new Epistolary config in {config_path}.")

    # Mailbox Manager
    click.echo("Epistolary can use different mailbox managers to manage the emails.")
    click.echo("\t- 'smtpimap': Use SMTP and IMAP protocols.")
    click.echo("\t- 'gmail': Use Gmail API.")
    mailbox_manager = click.prompt(
        "Which mailbox manager would you like to use?",
        type=click.Choice(list(_MAILBOX_MANAGER_OPTIONS.keys())),
        default=_DEFAULT_MAILBOX_MANAGER,
    )

    mailbox_manager_class = None
    try:
        mailbox_manager_class = _get_module_from_string(_MAILBOX_MANAGER_OPTIONS[mailbox_manager])
        if mailbox_manager_class is None:
            raise ValueError("Failed to load mailbox manager class")
    except Exception as e:
        click.echo(
            click.style(f"Failed to load mailbox manager: {e}", fg="red"), err=True
        )
        return

    if mailbox_manager == "gmail":
        click.echo("\nTo use Gmail, you need to set up OAuth2 credentials:")
        click.echo("1. Go to https://console.developers.google.com/")
        click.echo("2. Create a new project or select an existing one")
        click.echo("3. Enable the Gmail API")
        click.echo("4. Configure the OAuth consent screen")
        click.echo("5. Create credentials (OAuth client ID) for a desktop application")
        click.echo("6. Download the credentials JSON file")
        click.echo("\nOnce you have downloaded the credentials file:")

        credentials_path = click.prompt(
            "Enter the path to your credentials JSON file",
            type=str,
            default="~/.config/epistolary_gmail_credentials.json"
        )
        token_path = click.prompt(
            "Enter the path where you want to store the OAuth token",
            type=str,
            default="~/.config/epistolary_gmail_token.json"
        )
        email = click.prompt("Gmail address")

        # These are unused for Gmail
        password = ""
        imap_host = ""
        imap_port = 0
        smtp_host = ""
        smtp_port = 0
        smtp_username = None
        smtp_password = None
    else:
        email = click.prompt("Email")
        password = base64.b64encode(
            click.prompt("Password", hide_input=True).encode("utf-8")
        ).decode("utf-8")
        imap_host = click.prompt("IMAP Host")
        imap_port = click.prompt("IMAP Port", type=int)
        smtp_host = click.prompt("SMTP Host")
        smtp_port = click.prompt("SMTP Port", type=int)

        # Do we have a separate SMTP username and password y/N?
        smtp_username = None
        smtp_password = None
        if click.confirm(
            "Do you have a separate SMTP username and password?", default=False
        ):
            smtp_username = click.prompt("SMTP Username")
            smtp_password = click.prompt("SMTP Password", hide_input=True)

    # Should we ignore marketing emails y/N?
    click.echo(
        "By default, Epistolary will ignore marketing emails, defined as any email that has the text 'unsubscribe' in the body."
    )
    ignore_marketing_emails = not click.confirm(
        "Would you like to forward marketing emails to your device (true) or ignore them (false, default)?",
        default=False,
    )

    # We can now prompt for which extractor, doc mgr, and mailbox classes to
    # use, as a "choice":

    # Extractor
    click.echo(
        "Epistolary can use different extractors to extract the text from emails."
    )
    click.echo("\t- 'tesseract': Extract text using the Tesseract OCR engine.")
    click.echo(
        "\t- 'openai': Extract text using the OpenAI GPT-4o engine. NOTE: This transmits your email as an image to OpenAI servers."
    )
    extractor = click.prompt(
        "Which extractor would you like to use?",
        type=click.Choice(list(_TEXT_EXTRACTOR_OPTIONS.keys())),
        default=_DEFAULT_TEXT_EXTRACTOR,
    )

    try:
        _ = _get_module_from_string(_TEXT_EXTRACTOR_OPTIONS[extractor])
    except Exception as e:
        click.echo(click.style(f"Failed to load extractor: {e}", fg="red"), err=True)
        return

    # Document Manager
    click.echo("Epistolary can use different document managers to manage the emails.")
    click.echo("\t- 'files': Save email PDFs to the filesystem.")
    click.echo("\t- 'remarkable': Interact with emails on a reMarkable tablet.")
    document_manager = click.prompt(
        "Which document manager would you like to use?",
        type=click.Choice(list(_DOCUMENT_MANAGER_OPTIONS.keys())),
        default=_DEFAULT_DOCUMENT_MANAGER,
    )

    try:
        _ = _get_module_from_string(_DOCUMENT_MANAGER_OPTIONS[document_manager])
    except Exception as e:
        click.echo(
            click.style(f"Failed to load document manager: {e}", fg="red"), err=True
        )
        return

    # Now we can create the config object.
    conf = EpistolaryConfig(
        imap_host=imap_host,
        imap_port=imap_port,
        email=email,
        password=password,
        smtp_host=smtp_host,
        smtp_port=smtp_port,
        smtp_username=smtp_username,
        smtp_password=smtp_password,
        ignore_marketing_emails=ignore_marketing_emails,
        text_extractor=_TEXT_EXTRACTOR_OPTIONS[extractor],
        document_manager=_DOCUMENT_MANAGER_OPTIONS[document_manager],
        mailbox_manager=_MAILBOX_MANAGER_OPTIONS[mailbox_manager],
        token_path=token_path if mailbox_manager == "gmail" else None,
        credentials_path=credentials_path if mailbox_manager == "gmail" else None,
    )

    click.echo(
        "Epistolary can optionally check that your email credentials are correct by performing a test login."
    )

    test_login = click.confirm("Would you like to perform a test login?", default=True)
    if test_login:
        click.echo("Attempting to log in...")
        try:
            _ = mailbox_manager_class.from_file(config_path)
        except Exception as e:
            click.echo(click.style(f"Failed to log in: {e}", fg="red"), err=True)
            return
        click.echo(click.style("Successfully logged in!", fg="green"))

    # Finally, we can write the config to the file.
    conf.to_file(config_path)
    click.echo(click.style(f"Config successfully written to {config_path}", fg="green"))


@cli.command()
@click.pass_context
def receive(ctx):
    config_path = ctx.obj["config_file_path"]
    if not config_path.exists():
        click.echo(
            click.style(f"Config file does not exist at {config_path}", fg="red"),
            err=True,
        )
        return

    config = EpistolaryConfig.from_file(config_path)

    EO = EpistolaryOrchestrator(
        mailbox_manager=_get_module_from_string(config.mailbox_manager).from_file(config_path),
        document_manager=_get_module_from_string(config.document_manager)(),
        text_extractor=_get_module_from_string(config.text_extractor)(),
    )

    EO.refresh_document_mailbox()


@cli.command()
@click.pass_context
def send(ctx):
    config_path = ctx.obj["config_file_path"]
    if not config_path.exists():
        click.echo(
            click.style(f"Config file does not exist at {config_path}", fg="red"),
            err=True,
        )
        return

    config = EpistolaryConfig.from_file(config_path)

    EO = EpistolaryOrchestrator(
        mailbox_manager=_get_module_from_string(config.mailbox_manager).from_file(config_path),
        document_manager=_get_module_from_string(config.document_manager)(),
        text_extractor=_get_module_from_string(config.text_extractor)(),
    )

    EO.send_outbox()


if __name__ == "__main__":
    cli()
