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
import uuid

import pytest
import simple_logger.logger
from click.testing import CliRunner
from jira import Issue

from src import cli
from src.objects.jira_base import Jira
from src.objects.job import Job
from src.report.constants import JOB_PASSED_SINCE_TICKET_CREATED_LABEL

logger = simple_logger.logger.get_logger(__name__)

PASSING_LABEL_STEP = "e2e-passing-label-step"


@pytest.fixture
def build_id():
    yield f"e2e-pl-{uuid.uuid4().hex[:16]}"


@pytest.fixture
def job_name(build_id):
    yield f"periodic-ci-firewatch-e2e-passing-label-{build_id}"


@pytest.fixture
def job_name_safe(build_id):
    yield f"firewatch-e2e-passing-label-{build_id}"


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
def target_label():
    yield JOB_PASSED_SINCE_TICKET_CREATED_LABEL


def test_add_jira_label_to_open_bugs_with_passing_job_run(
    report_cli_command_args,
    jira,
    monkeypatch,
    job_dir,
    target_label,
    register_jira_issues_for_e2e_cleanup,
    job_name,
    build_id,
):
    job_dir.mkdir(parents=True, exist_ok=True)
    fail_logs = job_dir / "logs"
    step_dir = fail_logs / PASSING_LABEL_STEP
    step_dir.mkdir(parents=True)
    (step_dir / "finished.json").write_text('{"passed": false}')
    artifacts_fail = job_dir / "artifacts"
    artifacts_fail.mkdir(parents=True)

    pass_logs = job_dir / "logs-pass"
    pass_step = pass_logs / PASSING_LABEL_STEP
    pass_step.mkdir(parents=True, exist_ok=True)
    (pass_step / "finished.json").write_text('{"passed": true}')
    artifacts_pass = job_dir / "artifacts-pass"
    artifacts_pass.mkdir(parents=True)

    keys_created: list[str] = []
    real_create = Jira.create_issue

    def capture_create_issue(self, *args, **kwargs):
        issue = real_create(self, *args, **kwargs)
        keys_created.append(issue.key)
        register_jira_issues_for_e2e_cleanup(issue.key)
        return issue

    monkeypatch.setattr(Jira, "create_issue", capture_create_issue)

    monkeypatch.setattr(Job, "_get_steps", lambda *a, **k: [PASSING_LABEL_STEP])
    monkeypatch.setattr(Job, "_download_logs", lambda *x, **y: fail_logs.as_posix())
    monkeypatch.setattr(Job, "_download_junit", lambda *x, **y: artifacts_fail.as_posix())

    logger.info(f"invoking report command with args: {report_cli_command_args}")
    result = run_report_cli_command(report_cli_command_args)

    assert cli_command_completed_successfully(result), format_cli_result_for_debug(result)
    logger.info("cli command completed successfully")

    assert keys_created, "expected file_jira_issues to create at least one ticket " + format_cli_result_for_debug(
        result
    )

    issue_keys_from_stdout = list(dict.fromkeys(keys_created))
    logger.info(f"open issues found: {issue_keys_from_stdout}")

    logger.info("fetching Jira issues")
    issues: list[Issue] = [jira.get_issue_by_id_or_key(k) for k in issue_keys_from_stdout]
    assert not any_issue_has_target_label(issues, target_label)
    logger.info(f'verified that "{target_label}" is not set on identified issues')

    logger.info(
        "patching the job download paths to simulate a test run with no failures",
    )
    monkeypatch.setattr(Job, "_download_logs", lambda *x, **y: pass_logs.as_posix())
    monkeypatch.setattr(Job, "_download_junit", lambda *x, **y: artifacts_pass.as_posix())

    logger.info(f"invoking report command with args: {report_cli_command_args}")
    passing_run_result = run_report_cli_command(report_cli_command_args)

    assert cli_command_completed_successfully(passing_run_result), format_cli_result_for_debug(
        passing_run_result,
    )
    logger.info("cli command completed successfully")

    assert not cli_result_logged_job_failure_in_output(
        passing_run_result,
        job_name,
    ), f"unexpected job failure log line for {job_name}\n{format_cli_result_for_debug(passing_run_result)}"
    logger.info("the report cli command did NOT log a job failure, as expected")

    logger.info(
        f'checking that all identified open issues now have the label "{target_label}"',
    )
    for issue_key in issue_keys_from_stdout:
        issue = jira.get_issue_by_id_or_key(issue_key)
        assert issue_has_label(issue, target_label)
        logger.info(f"{issue.key} was successfully labeled")


def cli_captured_text(result) -> str:
    text = result.stdout or ""
    if result.stderr_bytes is not None:
        text += result.stderr or ""
    return text


def format_cli_result_for_debug(result) -> str:
    lines = [f"exit_code={result.exit_code}"]
    if result.exception is not None:
        lines.append(f"exception={result.exception!r}")
    stdout = result.stdout or ""
    if result.stderr_bytes is None:
        stderr_display = "(stderr not separately captured; use stdout if mix_stderr=True)"
    else:
        stderr_display = result.stderr or ""
        if not stderr_display:
            stderr_display = "(empty)"
    lines.extend(
        (
            "--- stdout ---",
            stdout if stdout else "(empty)",
            "--- stderr ---",
            stderr_display,
        ),
    )
    return "\n".join(lines)


def cli_result_logged_job_failure_in_output(result, job_name) -> bool:
    return f"Failure in {job_name}" in cli_captured_text(result)


def any_issue_has_target_label(issues, target_label):
    return any(issue_has_label(issue, target_label) for issue in issues)


def issue_has_label(issue, target_label):
    return target_label in issue.fields.labels


def parse_jira_issue_keys_from_cli_command_stdout(result):
    issue_keys_from_stdout = set(
        re.findall(r"https?://[^\s]+/browse/([\w-]+)", cli_captured_text(result)),
    )
    return list(issue_keys_from_stdout)


def cli_command_completed_successfully(result) -> bool:
    return result.exit_code == 0


def run_report_cli_command(report_cli_command_args):
    runner = CliRunner(mix_stderr=False)
    return runner.invoke(cli=cli.main, args=("report", *report_cli_command_args))
