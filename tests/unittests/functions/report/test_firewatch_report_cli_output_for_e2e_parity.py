"""Covers CLI log capture and Jira URL parsing used by the passing-job e2e test.

Report must not run the open-bug passing path when ``job.failures`` is non-empty; see
``test_report_does_not_run_passing_job_path_when_failures_exist_but_none_filed``.
"""

from click.testing import CliRunner
from click.testing import Result

from tests.e2e.test_add_jira_label_to_open_bugs_with_passing_job_run import (
    cli_captured_text,
    parse_jira_issue_keys_from_cli_command_stdout,
)


def _make_result(
    runner: CliRunner,
    *,
    stdout: bytes,
    stderr: bytes | None,
) -> Result:
    return Result(
        runner=runner,
        stdout_bytes=stdout,
        stderr_bytes=stderr,
        return_value=None,
        exit_code=0,
        exception=None,
    )


def test_cli_captured_text_uses_stdout_when_stderr_not_captured():
    runner = CliRunner(mix_stderr=True)
    r = _make_result(runner, stdout=b"combined\n", stderr=None)
    assert cli_captured_text(r) == "combined\n"


def test_cli_captured_text_appends_stderr_when_streams_are_separate():
    runner = CliRunner(mix_stderr=False)
    r = _make_result(runner, stdout=b"out\n", stderr=b"err\n")
    assert cli_captured_text(r) == "out\nerr\n"


def test_parse_jira_issue_keys_reads_browse_urls_from_stderr():
    runner = CliRunner(mix_stderr=False)
    r = _make_result(
        runner,
        stdout=b"",
        stderr=b" INFO https://redhat.atlassian.net/browse/LPINTEROP-999\n",
    )
    assert parse_jira_issue_keys_from_cli_command_stdout(r) == ["LPINTEROP-999"]


def test_parse_jira_issue_keys_finds_multiple_keys():
    runner = CliRunner(mix_stderr=False)
    r = _make_result(
        runner,
        stdout=b"",
        stderr=(b"see https://x.atlassian.net/browse/ABC-1 and https://y.atlassian.net/browse/DEF-2\n"),
    )
    keys = sorted(parse_jira_issue_keys_from_cli_command_stdout(r))
    assert keys == ["ABC-1", "DEF-2"]
