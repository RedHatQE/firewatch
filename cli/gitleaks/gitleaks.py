#
# Copyright (C) 2023 Red Hat, Inc.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
import os
import shutil
import subprocess as sp
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from typing import Literal

import requests
from simple_logger.logger import get_logger

BUILD_ID_VAR: str = "BUILD_ID"
ARTIFACT_DIR_VAR: str = "ARTIFACT_DIR"


@dataclass
class GitleaksConfig:
    _server_url: str
    _token_path: str
    _output_file: str
    _gitleaks_version = "7.6.1"
    _artifact_dir: None | Path = None
    _job_dir: None | Path = None
    _patterns_file_url: None | str = None
    _keep_job_dir: None | bool = False
    _gitleaks_report_path: None | Path = None
    _patterns_file_path: None | Path = None
    _env_artifact_dir: str = ""
    _env_build_id: str = ""
    _job_dir_root: str | Path = "/tmp"
    _logger: Any = None
    _keep_patterns_file: bool = False

    def __post_init__(self) -> None:
        """
        Builds the GitleaksConfig object. This class is used to generate a Gitleaks detect scan using the latest Red Hat
        detection rules.

        The expected environment variables, directories, and secrets are gathered and checked for availability.

        The latest Gitleaks detection patterns are fetched from the Red Hat patterns distribution server and used to run
        a `gitleaks detect` scan on the job directory created by the `firewatch report` cli command.

        If any detections are found, a report is created and archived in the ARTIFACT_DIR.

        The detection patterns file and the job directory are removed during teardown.
        """

        self._get_env_vars()
        self._check_env()

    def _get_env_vars(self) -> None:
        """
        Get the values for the ARTIFACT_DIR and BUILD_ID environment variables.
        """
        self._env_artifact_dir = os.getenv(ARTIFACT_DIR_VAR, "")
        self._env_build_id = os.getenv(BUILD_ID_VAR, "")

    def _check_env(self) -> None:
        """
        Check that the required environment variables, directories, and secrets are available.
        Logs error message to the class logger object and raises OSError if one or more requirements are unmet.
        """

        def _log_err(msg: str, _logger: Any = self.logger) -> Literal[True]:
            """
            Log the message as an error and return True. Used to toggle the _has_env_err in the outer scope.

            Args:
                msg (str): The error message to log.
                _logger (Any): The class logger object.

            Returns:
                Literal[True]: Used to toggle flag in the outer scope
            """
            _logger.error(msg=msg)
            return True

        _has_env_err: bool = False

        if not self._env_artifact_dir:
            _has_env_err = _log_err(f"{ARTIFACT_DIR_VAR} was not set.")
        if not self._env_build_id:
            _has_env_err = _log_err(f"{BUILD_ID_VAR} was not set.")
        if not self.artifact_dir.is_dir():
            _has_env_err = _log_err(
                f"the artifact dir was not found at {os.getenv('ARTIFACT_DIR')}",
            )
        if not self.job_dir.is_dir():
            _has_env_err = _log_err(
                "the Firewatch report downloads directory was not found",
            )
        elif not any(p for p in self.job_dir.rglob("*") if p.is_file()):
            _has_env_err = _log_err(
                "the Firewatch report downloads directory is empty",
            )
        if not self.token_path.is_file():
            _has_env_err = _log_err(
                "the patterns server token file was not found",
            )
        if _has_env_err:
            raise OSError

    def _try_fetch_patterns_from_server(self) -> None:
        """
        If the detect patterns file is not found, try to fetch it from the patterns distribution server.
        If the patterns file is not created or has no contents, the error is logged and raised.
        """
        if not self.patterns_file_path.is_file():
            self.logger.info("pulling latest gitleaks detection patterns")
            try:
                self._fetch_patterns_file()
                assert self.patterns_file_path.is_file()
                assert any(self.patterns_file_path.read_text())
            except Exception as e:
                self.logger.error("error while fetching gitleaks detection patterns")
                raise e

    def _try_start_gitleaks_detect_subprocess(self) -> None:
        """
        Try to create the Gitleaks detect scan subprocess using the args stored in self.detect_args.
        If any exception occurs, the error is logged and the exception is raised.
        """
        self.logger.info(
            f"starting gitleaks detect scan",
        )
        try:
            sp.run(
                [
                    "gitleaks",
                    "detect",
                    *self.detect_args,
                ],
            )
        except Exception as e:
            self.logger.error("error while starting gitleaks detect scan")
            raise e

    def _cleanup(self) -> None:
        """
        Teardown method that removes the detection patterns file and the firewatch job_dir,
        unless the --keep-job-dir flag is used.

        If an OSError exception occurs during the removal of the job_dir,
        the error is logged and the exception is raised.
        """
        if self._patterns_file_path and not self._keep_patterns_file:
            self._patterns_file_path.unlink(missing_ok=True)
        if not self._keep_job_dir and self._job_dir and self._job_dir.is_dir():
            self.logger.info(
                f"Deleting job directory: {self._job_dir}",
            )
            try:
                shutil.rmtree(self._job_dir)
            except OSError as e:
                self.logger.error(
                    f"OS error while removing reports download directory: {self._job_dir.absolute()}",
                )
                raise e

    @property
    def logger(self) -> Any:
        """
        Instantiates the class logger from the outer scope, unless it is already set.
        """
        if not self._logger:
            self._logger = get_logger(__name__)
        return self._logger

    @property
    def detect_args(self) -> list[str]:
        """
        Generates the subprocess arguments used by the `gitleaks detect` command.

        Returns:
            list[str]: a list of strings to pass to the `gitleaks detect` command subprocess.
        """
        report = self.gitleaks_report_path.as_posix()
        path = self.job_dir.as_posix()
        config_path = self.patterns_file_path.as_posix()
        return [
            "--no-git",
            "--redact",
            f"--report={report}",
            f"--path={path}",
            f"--config-path={config_path}",
        ]

    @property
    def token_path(self) -> Path:
        """
        Get the token path string set by the `firewatch gitleaks` CLI command as a Path object.

        Returns:
            Path: The expected path to the file containing the detection patterns server bearer token.
        """
        return Path(self._token_path)

    @property
    def patterns_file_path(self) -> Path:
        """
        Get the expected patterns file path as a Path object.

        Returns:
            Path: The expected path to the file containing the Red Hat detection patterns.
                Defaults to "/tmp/patterns.toml" if not set.
        """
        if not self._patterns_file_path:
            self._patterns_file_path = Path("/tmp/patterns.toml")
        return self._patterns_file_path

    @property
    def patterns_file_url(self) -> str:
        """
        Generates the URL used to fetch the latest detection patterns using
        the base `_server_url` and the target `_gitleaks_version`.

        Returns:
            str: The URL used to fetch the latest detection patterns.
        """
        if not self._patterns_file_url:
            self._patterns_file_url = (
                f"{self._server_url}/patterns/gitleaks/{self._gitleaks_version}"
            )
        return self._patterns_file_url

    @property
    def patterns_server_auth_headers(self) -> dict[str, str]:
        """
        Generates the headers used to authenticate to the patterns distribution server using the path to the token file.

        Returns:
            dict[str, str]: A dictionary containing the bearer token, to be passed as request headers.
        """
        return {"Authorization": f"Bearer {self.token_path.read_text().strip()}"}

    @property
    def artifact_dir(self) -> Path:
        """
        Get the path string found in the environment variable ARTIFACT_DIR as a Path object.

        Returns:
            Path: Path object to the directory used to store artifacts.
                Used to archive the report generated by the `gitleaks detect` scan.
        """
        if not self._artifact_dir:
            self._artifact_dir = Path(self._env_artifact_dir)
        return self._artifact_dir

    @property
    def job_dir(self) -> Path:
        """
        Get the path of the job directory containing the files downloaded during the `firewatch report` command run.
        If not already set, the `_job_dir_root` and the job's build ID stored in the BUILD_ID environment variable are
        used to determine the expected path.

        Returns:
            Path: Path object to the directory containing the files downloaded
                during the `firewatch report` command run.
        """
        if not self._job_dir:
            self._job_dir = Path(self._job_dir_root) / self._env_build_id
        return self._job_dir

    @property
    def gitleaks_report_path(self) -> Path:
        """
        Get the path to the location of the report generated by the `gitleaks detect` command.
        If not already set, the filename will be set to the value of `_output_file` and archived in the ARTIFACT_DIR.

        Returns:
            Path: a Path object to the location and filename of the `gitleaks detect` report file
                that is created when any Gitleaks detections are found.
        """
        if not self._gitleaks_report_path:
            self._gitleaks_report_path = self.artifact_dir / self._output_file
        return self._gitleaks_report_path

    def _fetch_patterns_file(self) -> None:
        """
        Generate the request containing the bearer token for authentication to the patterns distribution server.
        Retrieve the latest `gitleaks` detection patterns and store them at the path defined in `patterns_file_path`.
        """
        with self.patterns_file_path.open("ab") as fo:
            for x in requests.get(
                url=self.patterns_file_url,
                headers=self.patterns_server_auth_headers,
            ).iter_content():
                fo.write(x)

    def start_detect_scan(self, keep_job_dir: bool | None = None) -> None:
        """
        Generate a Gitleaks detect scan using the latest Red Hat detection rules.
        """
        if isinstance(keep_job_dir, bool):
            self._keep_job_dir = keep_job_dir
        try:
            self._try_fetch_patterns_from_server()
            self._try_start_gitleaks_detect_subprocess()
        except OSError:
            self.logger.warning("nothing to scan. cleaning up and exiting.")
            raise
        finally:
            self._cleanup()
