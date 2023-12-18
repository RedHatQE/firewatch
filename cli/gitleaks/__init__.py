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
"""Module building gitleaks cli command"""
from typing import Any

import click

from cli.gitleaks.gitleaks import GitleaksConfig

DEFAULT_SERVER_URL = "https://patterns.security.redhat.com"
DEFAULT_TOKEN_PATH = "/tmp/secrets/rh-patterns-server/access-token"
DEFAULT_OUTPUT_FILE = "gitleaks_report.json"


@click.option(
    "--server-url",
    help="Redhat patterns server URL",
    default=DEFAULT_SERVER_URL,
    required=True,
    type=click.STRING,
)
@click.option(
    "--token-path",
    help="Path to the Redhat patterns server token",
    default=DEFAULT_TOKEN_PATH,
    required=True,
    type=click.Path(exists=True),
)
@click.option(
    "--output-file",
    help="The name of the gitleaks detect report to be stored as an artifact",
    default=DEFAULT_OUTPUT_FILE,
    type=click.Path(),
)
@click.option(
    "--keep-job-dir",
    help="If set, firewatch will not delete the job directory (/tmp/12345) that is created to hold logs and results for a job following execution.",
    is_flag=True,
    default=False,
    type=click.BOOL,
)
@click.command("gitleaks")
def gitleaks(
    server_url: str,
    token_path: str,
    output_file: str,
    keep_job_dir: bool,
) -> None:
    GitleaksConfig(
        _server_url=server_url,
        _token_path=token_path,
        _output_file=output_file,
        _keep_job_dir=keep_job_dir,
    ).start_detect_scan()


def get_default_gitleaks_config(**kwargs: dict[str, Any]) -> GitleaksConfig:
    kw: dict[str, Any] = {
        "_server_url": DEFAULT_SERVER_URL,
        "_token_path": DEFAULT_TOKEN_PATH,
        "_output_file": DEFAULT_OUTPUT_FILE,
        "_keep_job_dir": False,
    }
    kw.update(**kwargs)
    return GitleaksConfig(**kw)
