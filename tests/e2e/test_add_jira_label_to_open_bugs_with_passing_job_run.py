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
import re

import pytest
import simple_logger.logger
from click.testing import CliRunner
from jira import Issue

from src import cli
from src.objects.job import Job
from src.report.constants import JOB_PASSED_SINCE_TICKET_CREATED_LABEL

logger = simple_logger.logger.get_logger(__name__)


@pytest.fixture
def job_name():
    yield "periodic-ci-openshift-pipelines-release-tests-release-v1.14-openshift-pipelines-ocp-4.16-lp-interop-openshift-pipelines-interop-aws"


@pytest.fixture
def job_name_safe():
    yield "openshift-pipelines-interop-aws"


@pytest.fixture
def build_id():
    yield "1805119554108526592"


@pytest.fixture
def report_cli_command_args(
    jira_config_path,
    firewatch_config_path,
    build_id,
    job_name,
    job_name_safe,
):
    yield (
        f"--build-id={build_id}",
        f"--job-name-safe={job_name_safe}",
        f"--job-name={job_name}",
        f"--jira-config-path={jira_config_path.as_posix()}",
        f"--firewatch-config-path={firewatch_config_path.as_posix()}",
    )


@pytest.fixture
def issue_keys_cache_key():
    yield "issues/keys"


@pytest.fixture
def target_label():
    yield JOB_PASSED_SINCE_TICKET_CREATED_LABEL


@pytest.fixture(autouse=True)
def cleanup(request, issue_keys_cache_key, jira, target_label):
    yield
    logger.info("cleaning up labels added to Jira issues")
    for issue_key in request.config.cache.get(issue_keys_cache_key, []):
        issue = jira.get_issue_by_id_or_key(issue_key)
        if issue_has_label(issue, target_label):
            logger.info(f'removing label "{target_label}" from {issue_key}')
            remove_label_from_issue(issue, target_label)


def test_add_jira_label_to_open_bugs_with_passing_job_run(
    report_cli_command_args,
    jira,
    monkeypatch,
    job_log_dir,
    job_artifacts_dir,
    target_label,
    request,
    job_name,
):
    logger.info(f"invoking report command with args: {report_cli_command_args}")
    result = run_report_cli_command(report_cli_command_args)

    assert cli_command_completed_successfully(result)
    logger.info("cli command completed successfully")

    assert cli_result_logged_job_failure_in_stdout(
        result,
        job_name,
    ), f"failures were not found for {job_name}; unable to complete test run"
    logger.info("the report cli command logged a job failure, as expected")

    issue_keys_from_stdout = parse_jira_issue_keys_from_cli_command_stdout(result)
    cache_issue_keys(issue_keys_from_stdout, request)
    logger.info(f"open issues found: {issue_keys_from_stdout}")

    logger.info("fetching Jira issues")
    issues: list[Issue] = [jira.get_issue_by_id_or_key(k) for k in issue_keys_from_stdout]
    assert not any_issue_has_target_label(issues)
    logger.info(f'verified that "{target_label}" is not set on identified issues')

    logger.info(
        "patching the job download paths to simulate a test run with no failures",
    )
    with monkeypatch.context() as m:
        m.setattr(Job, "_download_logs", lambda *x, **y: job_log_dir.as_posix())
        m.setattr(Job, "_download_junit", lambda *x, **y: job_artifacts_dir.as_posix())

        logger.info(f"invoking report command with args: {report_cli_command_args}")
        result = run_report_cli_command(report_cli_command_args)

        assert cli_command_completed_successfully(result)
        logger.info("cli command completed successfully")

        assert not cli_result_logged_job_failure_in_stdout(result, job_name)
        logger.info("the report cli command did NOT log a job failure, as expected")

    logger.info(
        f'checking that all identified open issues now have the label "{target_label}"',
    )
    for issue_key in issue_keys_from_stdout:
        issue = jira.get_issue_by_id_or_key(issue_key)
        assert issue_has_label(issue, target_label)
        logger.info(f"{issue.key} was successfully labeled")


def cli_result_logged_job_failure_in_stdout(result, job_name) -> bool:
    return f"Failure in {job_name}" in result.stdout


def any_issue_has_target_label(issues):
    return any(filter(lambda x: issue_has_label(x, target_label), issues))


def cache_issue_keys(issue_keys_from_stdout, request):
    request.config.cache.set("issues/keys", issue_keys_from_stdout)


def remove_label_from_issue(issue, target_label):
    issue.update(update={"labels": [{"remove": target_label}]})


def issue_has_label(issue, target_label):
    return target_label in issue.fields.labels


def parse_jira_issue_keys_from_cli_command_stdout(result):
    issue_keys_from_stdout = set(
        re.findall(r"\shttps?://.+/browse/([\w-]+)", result.stdout),
    )
    return list(issue_keys_from_stdout)


def cli_command_completed_successfully(result) -> bool:
    return result.exit_code == 0


def run_report_cli_command(report_cli_command_args):
    runner = CliRunner()
    result = runner.invoke(cli=cli.main, args=("report", *report_cli_command_args))
    print(result.stdout)
    return result
