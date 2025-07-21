#
# Copyright (C) 2024 Red Hat, Inc.
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
from click import Context

from src.objects.configuration import Configuration
from src.objects.jira_base import Jira
from src.objects.job import Job
from src.report.report import Report


def validate_verbose_test_failure_reporting_ticket_limit(
    ctx: click.Context,
    param: click.Parameter,
    value: int,
) -> Optional[int]:
    """
    Validates the verbose_test_reporting_ticket_limit option. If verbose_test_reporting_ticket_limit is set, verbose_test_reporting must also be set.

    :param ctx: Click context
    :param param: Click parameter. The param argument is not used in the function, but it is required to match the expected type of the callback argument in the click.option decorator.
    :param value: Value of click parameter
    :return: The value of the click parameter.
    """
    if value is not None and not ctx.params.get("verbose_test_failure_reporting"):
        raise click.BadParameter(
            "You must set --verbose-test-reporting when --verbose-test-reporting-ticket-limit is set.",
        )
    return value


@click.option(
    "--job-name",
    help="The full name of a Prow job. The value of $JOB_NAME",
    required=False,
    type=click.STRING,
)
@click.option(
    "--job-name-safe",
    help="The safe name of a test in a Prow job. The value of $JOB_NAME_SAFE",
    required=False,
    type=click.STRING,
)
@click.option(
    "--build-id",
    help="The build ID that needs to be reported. The value of $BUILD_ID",
    required=False,
    type=click.STRING,
)
@click.option(
    "--pr-id",
    help="The pull request number that the rehearsal job is for. The value of $PULL_NUMBER",
    required=False,
    type=click.STRING,
)
@click.option(
    "--gcs-bucket",
    help="The name of the GCS bucket that holds OpenShift CI logs",
    default="test-platform-results",
    type=click.STRING,
)
@click.option(
    "--gcs-creds-file",
    help="The path to the GCS credentials file",
    type=click.Path(exists=True),
)
@click.option(
    "--firewatch-config-path",
    help="The path to the firewatch configuration file",
    required=False,
    type=click.Path(),
)
@click.option(
    "--jira-config-path",
    help="The path to the jira configuration file",
    default="/tmp/jira.config",
    type=click.Path(exists=True),
)
@click.option(
    "--transition-map-url",
    help="The path to the jira transition name map",
    required=False,
    type=click.Path(exists=True),
)
@click.option(
    "--fail-with-test-failures",
    help="Firewatch will fail with a non-zero exit code if a test failure is found.",
    is_flag=True,
    type=click.BOOL,
)
@click.option(
    "--fail-with-pod-failures",
    help="Firewatch will fail with a non-zero exit code if a pod failure is found. For use with jobs using best effort steps.",
    is_flag=True,
    type=click.BOOL,
)
@click.option(
    "--keep-job-dir",
    help="If set, firewatch will not delete the job directory (/tmp/12345) that is created to hold logs and results for a job following execution.",
    is_flag=True,
    type=click.BOOL,
)
@click.option(
    "--verbose-test-failure-reporting",
    help="If set, firewatch will report a bug for each test failure found.",
    is_flag=True,
    type=click.BOOL,
)
@click.option(
    "--verbose-test-failure-reporting-ticket-limit",
    help="Used to limit the number of bugs created when --verbose-test-reporting is set. If not specified, the default limit is 10.",
    required=False,
    type=click.INT,
    callback=validate_verbose_test_failure_reporting_ticket_limit,
)
@click.option(
    "--additional-labels-file",
    help="A file containing a list of additional labels separated by new lines to add to any new Jira issue.",
    type=click.Path(exists=True),
)
@click.option(
    "--pdb",
    help="Drop to `ipdb` shell on exception",
    is_flag=True,
)
@click.command("report")
@click.pass_context
def report(
    ctx: Context,
    job_name: str,
    job_name_safe: str,
    build_id: str,
    pr_id: str,
    gcs_bucket: str,
    gcs_creds_file: Optional[str],
    firewatch_config_path: Optional[str],
    jira_config_path: str,
    fail_with_test_failures: bool,
    fail_with_pod_failures: bool,
    keep_job_dir: bool,
    verbose_test_failure_reporting: bool,
    verbose_test_failure_reporting_ticket_limit: Optional[int],
    additional_labels_file: Optional[str],
    pdb: bool,
) -> None:
    ctx.obj["PDB"] = pdb

    # Build Objects
    jira_connection = Jira(jira_config_path=jira_config_path)
    config = Configuration(
        jira=jira_connection,
        fail_with_test_failures=fail_with_test_failures,
        fail_with_pod_failures=fail_with_pod_failures,
        keep_job_dir=keep_job_dir,
        verbose_test_failure_reporting=verbose_test_failure_reporting,
        verbose_test_failure_reporting_ticket_limit=verbose_test_failure_reporting_ticket_limit,
        config_file_path=firewatch_config_path,
        additional_lables_file=additional_labels_file,
    )
    job = Job(
        name=job_name,
        name_safe=job_name_safe,
        build_id=build_id,
        gcs_bucket=gcs_bucket,
        gcs_creds_file=gcs_creds_file,
        firewatch_config=config,
        pr_id=pr_id,
    )

    # Build the Report object and report issues to Jira
    Report(firewatch_config=config, job=job)
