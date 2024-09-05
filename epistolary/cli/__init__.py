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
from ..orchestrator import EpistolaryOrchestrator


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
    )

    click.echo(
        "Epistolary can optionally check that your email credentials are correct by performing a test login."
    )

    test_login = click.confirm("Would you like to perform a test login?", default=True)
    if test_login:
        click.echo("Attempting to log in...")
        try:
            _ = SMTPIMAPMailboxManager(
                imap_host=conf.imap_host,
                imap_port=conf.imap_port,
                username=conf.email,
                password=conf.password,
                smtp_host=conf.smtp_host,
                smtp_port=conf.smtp_port,
                smtp_username=conf.smtp_username,
                smtp_password=conf.smtp_password,
            )
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
        mailbox_manager=SMTPIMAPMailboxManager.from_file(config_path),
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
        mailbox_manager=SMTPIMAPMailboxManager.from_file(config_path),
        document_manager=_get_module_from_string(config.document_manager)(),
        text_extractor=_get_module_from_string(config.text_extractor)(),
    )

    EO.send_outbox()


if __name__ == "__main__":
    cli()
