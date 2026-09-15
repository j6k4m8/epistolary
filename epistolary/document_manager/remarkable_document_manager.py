"""Documents on a reMarkable tablet, through the rmapi and remarks command-line tools.

There is no maintained Python client for the reMarkable cloud. rmapi moves files
in and out; remarks turns a downloaded .rmdoc bundle into a PDF with the
handwriting drawn in.
"""

import logging
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

import fitz

log = logging.getLogger(__name__)


class RemarkableDocumentManager:
    def __init__(self, root: str = "Emails", outbox: str = "Outbox", archive: str = "_Archive", rmapi: str = "rmapi"):
        self.root = root
        self.outbox = f"{root}/{outbox}"
        self.archive_dir = f"{root}/{archive}"
        self.rmapi = rmapi
        self._tmp = tempfile.TemporaryDirectory(prefix="epistolary-")  # removed with this object
        self.cache = Path(self._tmp.name)
        for directory in (self.root, self.outbox, self.archive_dir):
            self._run("mkdir", directory)  # a no-op when it exists

    def _run(self, *args: str) -> str:
        log.debug("rmapi %s", " ".join(args))
        try:
            done = subprocess.run(
                [self.rmapi, *args],
                cwd=self.cache,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                check=True,
            )  # DEVNULL: a logged-out rmapi asks for a code instead of hanging
        except FileNotFoundError:
            raise RuntimeError(f"{self.rmapi!r} not found; install rmapi and run it once to log in") from None
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"rmapi {args[0]} failed: {e.stderr.strip() or e.stdout.strip()}") from None
        return done.stdout

    def _ls(self, path: str) -> list[str]:
        return [line.split("\t", 1)[1] for line in self._run("ls", path).splitlines() if line.startswith("[f]\t")]

    def list_inbox(self) -> list[str]:
        return self._ls(self.root)

    def list_outbox(self) -> list[str]:
        return self._ls(self.outbox)

    def get(self, name: str, outbox: bool = False) -> fitz.Document:
        bundles = [self.cache / f"{name}.rmdoc", self.cache / f"{name}.zip"]  # newer and older rmapi
        for bundle in bundles:
            bundle.unlink(missing_ok=True)
        self._run("get", f"{self.outbox if outbox else self.root}/{name}")
        bundle = next((b for b in bundles if b.exists()), None)
        if bundle is None:
            raise RuntimeError(f"rmapi get left no file for {name!r} in {self.cache}")
        return fitz.open(stream=_render(bundle), filetype="pdf")

    def put(self, name: str, doc: fitz.Document) -> None:
        pdf = self.cache / f"{name}.pdf"
        doc.save(pdf)
        self._run("put", str(pdf), self.root)

    def archive(self, name: str, outbox: bool = False) -> None:
        self._run("mv", f"{self.outbox if outbox else self.root}/{name}", self.archive_dir)


def _render(bundle: Path) -> bytes:
    """PDF bytes for a .rmdoc bundle, handwriting included."""
    with tempfile.TemporaryDirectory() as tmp:
        src, out = Path(tmp, "src"), Path(tmp, "out")
        with zipfile.ZipFile(bundle) as archive:
            archive.extractall(src)
        command = [sys.executable, "-m", "remarks", str(src), str(out)]
        log.debug("%s", " ".join(command))
        done = subprocess.run(command, capture_output=True, text=True)
        if done.returncode:
            raise RuntimeError(f"remarks failed on {bundle.name}:\n{done.stderr.strip()}")
        pdf = next(out.rglob("*.pdf"), None)
        if pdf is None:
            raise RuntimeError(f"remarks produced no PDF for {bundle.name}")
        return pdf.read_bytes()
