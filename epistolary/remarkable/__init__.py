import enum
import pathlib
import tempfile

import subprocess


class ReMarkablePathType(enum.Enum):
    """Enum for the type of path on the reMarkable."""

    FILE = "[f]"
    DIRECTORY = "[d]"

    def __str__(self):
        return self.value


class RMAPIWrapper:
    """A wrapper around the rmapi tool."""

    def __init__(
        self,
        confirm_rmapi: bool = True,
        rmapi_path: str = "rmapi",
        cache_dir: str | pathlib.Path | None = None,
    ):
        self._rmapi_path = rmapi_path
        self._cache_dir = (
            pathlib.Path(cache_dir)
            if cache_dir
            else pathlib.Path(tempfile.gettempdir())
        )

        if confirm_rmapi:
            self._confirm_rmapi()

    def _run_rmapi(self, *args):
        """
        Run the rmapi tool with the given arguments.
        """
        try:
            return subprocess.run(
                [self._rmapi_path, *args],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
                cwd=self._cache_dir,
            )
        except subprocess.CalledProcessError as e:
            raise Exception(e.stderr.decode("utf-8")) from e

    def _confirm_rmapi(self):
        """
        Confirm that the rmapi tool is installed and running.
        """
        try:
            self._run_rmapi("version")
        except FileNotFoundError:
            raise FileNotFoundError(f"rmapi tool not found at {self._rmapi_path}")

    def ls(self, remote_path: str = "") -> list[tuple[ReMarkablePathType, str]]:
        """
        List files in the remote path.
        """
        result = self._run_rmapi("ls", remote_path)
        printout = result.stdout.decode("utf-8").split("\n")
        files = []
        for line in printout:
            if line:
                path_type, path = line.split("\t")
                files.append((ReMarkablePathType(path_type), path))
        return files

    def download(self, remote_path: str, local_path: pathlib.Path):
        """
        Download a file from the reMarkable.
        """
        # remove extension from local path
        local_path = pathlib.Path(
            str(local_path).replace(".pdf", "").replace(".zip", "")
        )
        # Create the local path if it doesn't exist
        local_path.parent.mkdir(parents=True, exist_ok=True)
        self._run_rmapi("get", remote_path)
        base_fname = pathlib.Path(remote_path).name
        pathlib.Path(str(self._cache_dir / base_fname) + ".zip").rename(
            str(local_path) + ".zip"
        )

    def upload(self, local_path: pathlib.Path, remote_path: str):
        """
        Upload a file to the reMarkable.
        """
        self._run_rmapi("put", str(local_path), remote_path)

    def delete(self, remote_path: str):
        """
        Delete a file from the reMarkable.
        """
        self._run_rmapi("rm", remote_path)

    def mkdir(self, remote_path: str):
        """
        Create a directory on the reMarkable.
        """
        self._run_rmapi("mkdir", remote_path)


class RemarksWrapper:
    """
    The remarks tool is a command line tool that can be used to interpret the
    reMarkable rmv6 files and convert them to, say, PDF.
    """

    def __init__(
        self,
        confirm_remarks: bool = True,
        remarks_path: str = "python3 -m remarks",
        debug: bool = False,
    ):
        self._remarks_path = remarks_path
        self._debug = debug

        if confirm_remarks:
            self._confirm_remarks()

    def _run_remarks(self, *args):
        """
        Run the remarks tool with the given arguments.
        """
        if self._debug:
            print(f"[REMARKS] {self._remarks_path} {' '.join(args)}")
        try:
            return subprocess.run(
                [*self._remarks_path.split(" "), *args],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
                # shell=True
            )
        except subprocess.CalledProcessError as e:
            raise Exception(e.stderr.decode("utf-8")) from e

    def _confirm_remarks(self):
        """
        Confirm that the remarks tool is installed and running.
        """
        try:
            self._run_remarks("--version")
        except FileNotFoundError:
            raise FileNotFoundError(f"remarks tool not found at {self._remarks_path}")

    def rm_to_pdf(
        self, input_path: str | pathlib.Path, output_path: str | pathlib.Path
    ):
        """
        Convert a reMarkable file to PDF.
        """
        input_path = pathlib.Path(input_path)
        output_path = pathlib.Path(output_path)
        # Create outputpath.parent if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path_without_extension = output_path.with_suffix("")
        # If input path is a .zip, extract it
        if not input_path.suffix == ".zip":
            raise NotImplementedError("Input path must be a .zip file.")
        temp_dir = tempfile.mkdtemp()
        subprocess.run(["unzip", str(input_path), "-d", temp_dir], check=True)
        self._run_remarks(str(temp_dir), str(output_path_without_extension))

        # The output path (without ext) is a dir. There is a pdf inside of
        # it that we need to move to the correct location:
        print(list(output_path_without_extension.glob("*.pdf")))
        list(output_path_without_extension.glob("*.pdf"))[0].rename(
            str(output_path.parent / output_path.name)
        )
        # # Delete the temp file
        # (output_path.parent / output_path.name).rmdir()
        # list(output_path.parent.glob("*.this-is-a-tempfile"))[0].rename(
        #     str(output_path)
        # )
