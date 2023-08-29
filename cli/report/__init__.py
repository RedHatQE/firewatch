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
"""Module building report cli command"""
from typing import Optional

import click

from cli.objects.configuration import Configuration
from cli.objects.jira_base import Jira
from cli.objects.job import Job
from cli.report.report import Report


@click.option(
    "--job_name",
    help="The full name of a Prow job. The value of $JOB_NAME",
    required=False,
    type=click.STRING,
)
@click.option(
    "--job_name_safe",
    help="The safe name of a test in a Prow job. The value of $JOB_NAME_SAFE",
    required=False,
    type=click.STRING,
)
@click.option(
    "--build_id",
    help="The build ID that needs to be reported. The value of $BUILD_ID",
    required=False,
    type=click.STRING,
)
@click.option(
    "--gcs_bucket",
    help="The name of the GCS bucket that holds OpenShift CI logs",
    required=True,
    default="origin-ci-test",
    type=click.STRING,
)
@click.option(
    "--firewatch_config_path",
    help="The path to the firewatch configuration file",
    required=False,
    type=click.STRING,
)
@click.option(
    "--jira_config_path",
    help="The path to the jira configuration file",
    required=True,
    default="/tmp/jira.config",
    type=click.STRING,
)
@click.option(
    "--fail_with_test_failures",
    help="Firewatch will fail with a non-zero exit code if a test failure is found.",
    is_flag=True,
    default=False,
    type=click.BOOL,
)
@click.command("report")
@click.pass_context
def report(
    ctx: click.Context,
    job_name: str,
    job_name_safe: str,
    build_id: str,
    gcs_bucket: str,
    firewatch_config_path: Optional[str],
    jira_config_path: str,
    fail_with_test_failures: bool,
) -> None:
    # Build Objects
    jira_connection = Jira(jira_config_path=jira_config_path)
    config = Configuration(
        jira=jira_connection,
        fail_with_test_failures=fail_with_test_failures,
        config_file_path=firewatch_config_path,
    )
    job = Job(
        name=job_name,
        name_safe=job_name_safe,
        build_id=build_id,
        gcs_bucket=gcs_bucket,
    )

    # Build the Report object and report issues to Jira
    Report(firewatch_config=config, job=job)
