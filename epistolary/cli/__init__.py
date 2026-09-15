import logging
from pathlib import Path

import click

from ..config import DEFAULT_PATH, DOCUMENT_MANAGERS, TEXT_EXTRACTORS, EpistolaryConfig, encode


@click.group()
@click.option("--config", "-c", default=str(DEFAULT_PATH), show_default=True, help="Config file.")
@click.option("--debug", is_flag=True, help="Verbose logging.")
@click.pass_context
def cli(ctx, config: str, debug: bool):
    """Answer email by hand."""
    logging.basicConfig(level=logging.DEBUG if debug else logging.INFO, format="%(message)s")
    if not debug:
        logging.getLogger("httpx").setLevel(logging.WARNING)  # one line per OCR call otherwise
    ctx.obj = Path(config).expanduser()


def _orchestrator(path: Path):
    if not path.exists():
        raise click.ClickException(f"no config at {path}; run `epistolary init`")
    try:
        return EpistolaryConfig.from_file(path).orchestrator(path.with_suffix(".state.json"))
    except (ValueError, RuntimeError) as e:  # a bad config value, or rmapi missing
        raise click.ClickException(str(e))


@cli.command()
@click.pass_obj
def init(path: Path):
    """Write a config file, asking for each setting."""
    if path.exists():
        raise click.ClickException(f"{path} already exists")
    conf = EpistolaryConfig(
        email=click.prompt("Email address"),
        password=encode(click.prompt("Password", hide_input=True)),
        imap_host=click.prompt("IMAP host"),
        imap_port=click.prompt("IMAP port", type=int, default=993),
        smtp_host=click.prompt("SMTP host"),
        smtp_port=click.prompt("SMTP port", type=int, default=587),
    )
    if click.confirm("Different username and password for SMTP?", default=False):
        conf.smtp_username = click.prompt("SMTP username")
        conf.smtp_password = encode(click.prompt("SMTP password", hide_input=True))
    conf.ignore_marketing_emails = click.confirm("Skip mailing lists and marketing email?", default=True)
    conf.text_extractor = click.prompt(
        "Handwriting recognition: 'openai' sends page images to OpenAI, 'tesseract' runs locally",
        type=click.Choice(list(TEXT_EXTRACTORS)),
        default="openai",
    )
    conf.document_manager = click.prompt(
        "Documents go to a 'remarkable' tablet or to 'files' on disk",
        type=click.Choice(list(DOCUMENT_MANAGERS)),
        default="remarkable",
    )
    if click.confirm("Test the email login now?", default=True):
        try:
            conf.mailbox().check()
        except Exception as e:
            raise click.ClickException(f"login failed: {e}")
        click.echo("Login OK.")
    conf.to_file(path)
    click.echo(f"Wrote {path}")


@cli.command()
@click.option("--prune", is_flag=True, help="Also archive inbox documents whose email is no longer unread.")
@click.pass_obj
def receive(path: Path, prune: bool):
    """Turn unread emails into documents."""
    orchestrator = _orchestrator(path)
    created = orchestrator.receive()
    pruned = orchestrator.prune() if prune else []
    click.echo(f"{len(created)} new, {len(pruned)} archived.")


@cli.command()
@click.option("--yes", "-y", is_flag=True, help="Send without asking.")
@click.option("--dry-run", is_flag=True, help="Show what would be sent and send nothing.")
@click.pass_obj
def send(path: Path, yes: bool, dry_run: bool):
    """Transcribe the outbox and email it."""

    def confirm(to: str, subject: str, body: str) -> bool:
        click.echo(f"\nTo: {to}\nSubject: {subject}\n\n{body}\n")
        return not dry_run and (yes or click.confirm("Send it?", default=True))

    sent = _orchestrator(path).send(confirm)
    click.echo(f"{len(sent)} sent.")
