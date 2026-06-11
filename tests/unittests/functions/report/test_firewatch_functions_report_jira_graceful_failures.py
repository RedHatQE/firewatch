from unittest.mock import MagicMock

import pytest
from jira.exceptions import JIRAError

from src.objects.job import Job
from src.objects.rule import Rule
from src.report.report import Report


@pytest.fixture
def report_instance():
    report = Report.__new__(Report)
    report.logger = MagicMock()
    yield report


@pytest.fixture
def sample_job():
    job = MagicMock(spec=Job)
    job.name = "periodic-ci-example"
    job.build_id = "12345"
    return job


def test_add_retrigger_job_label_does_not_comment_when_labels_applied(
    report_instance,
    sample_job,
):
    jira = MagicMock()
    jira.add_labels_to_issue.return_value = (MagicMock(), True)

    report_instance.add_retrigger_job_label(
        jira=jira,
        issue_id="ROX-1",
        job=sample_job,
    )

    jira.add_labels_to_issue.assert_called_once()
    jira.comment.assert_not_called()


def test_add_retrigger_job_label_posts_fallback_comment_when_labels_not_applied(
    report_instance,
    sample_job,
):
    jira = MagicMock()
    jira.add_labels_to_issue.return_value = (MagicMock(), False)

    report_instance.add_retrigger_job_label(
        jira=jira,
        issue_id="ROX-1",
        job=sample_job,
    )

    jira.add_labels_to_issue.assert_called_once()
    jira.comment.assert_called_once()
    body = jira.comment.call_args.kwargs["comment"]
    assert jira.comment.call_args.kwargs["issue_id"] == "ROX-1"
    assert "retrigger" in body.lower()
    assert sample_job.name in body
    assert sample_job.build_id in body
    report_instance.logger.warning.assert_any_call(
        "Adding fallback comment on %s because the retrigger label could not be applied.",
        "ROX-1",
    )


def test_add_retrigger_job_label_attempts_fallback_comment_when_add_labels_raises_jira_error(
    report_instance,
    sample_job,
):
    jira = MagicMock()
    jira.add_labels_to_issue.side_effect = JIRAError("Internal server error", 500, "https://jira/x")

    report_instance.add_retrigger_job_label(
        jira=jira,
        issue_id="ROX-1",
        job=sample_job,
    )

    jira.add_labels_to_issue.assert_called_once()
    jira.comment.assert_called_once()
    assert jira.comment.call_args.kwargs["issue_id"] == "ROX-1"
    body = jira.comment.call_args.kwargs["comment"]
    assert "retrigger" in body.lower()
    assert sample_job.name in body
    report_instance.logger.warning.assert_any_call(
        "Could not add retrigger label to %s: %s",
        "ROX-1",
        "Internal server error",
    )
    report_instance.logger.warning.assert_any_call(
        "Adding fallback comment on %s because the retrigger label could not be applied.",
        "ROX-1",
    )


def test_add_retrigger_job_label_swallows_fallback_comment_jira_error(
    report_instance,
    sample_job,
):
    jira = MagicMock()
    jira.add_labels_to_issue.return_value = (MagicMock(), False)
    jira.comment.side_effect = JIRAError("bad", 400, "https://jira/x")

    report_instance.add_retrigger_job_label(
        jira=jira,
        issue_id="ROX-1",
        job=sample_job,
    )

    jira.comment.assert_called_once()
    report_instance.logger.warning.assert_any_call(
        "Adding fallback comment on %s because the retrigger label could not be applied.",
        "ROX-1",
    )
    report_instance.logger.warning.assert_any_call(
        "Could not add %s to %s: %s",
        "fallback retrigger comment",
        "ROX-1",
        "bad",
    )


def test_add_passing_job_comment_logs_warning_on_jira_error(report_instance, sample_job):
    jira = MagicMock()
    jira.comment.side_effect = JIRAError("Comment body is not valid!", 400, "https://jira/x")

    report_instance.add_passing_job_comment(
        job=sample_job,
        jira=jira,
        issue_id="ROX-1",
    )

    jira.comment.assert_called_once()
    report_instance.logger.warning.assert_called_once_with(
        "Could not add %s to %s: %s",
        "passing-job comment",
        "ROX-1",
        "Comment body is not valid!",
    )


def test_add_passing_job_label_logs_warning_when_labels_not_applied(report_instance):
    jira = MagicMock()
    jira.add_labels_to_issue.return_value = (MagicMock(), False)

    report_instance.add_passing_job_label(jira=jira, issue_id="ROX-1")

    jira.add_labels_to_issue.assert_called_once()
    report_instance.logger.warning.assert_called()


def test_add_passing_job_label_logs_warning_on_jira_error(report_instance):
    jira = MagicMock()
    jira.add_labels_to_issue.side_effect = JIRAError("no", 403, "https://jira/x")

    report_instance.add_passing_job_label(jira=jira, issue_id="ROX-1")

    report_instance.logger.warning.assert_called()


def test_report_success_logs_warning_when_create_issue_raises_jira_error(
    report_instance,
    sample_job,
    monkeypatch,
):
    rule = Rule(rule_dict={"jira_project": "LPTOCPCI"})
    config = MagicMock()
    config.success_rules = [rule]
    config.additional_labels_file = None
    jira = MagicMock()
    jira.create_issue.side_effect = JIRAError(
        "Method Not Allowed",
        405,
        "https://redhat.atlassian.net/rest/api/3/issue",
    )
    config.jira = jira
    monkeypatch.setattr(report_instance, "_get_issue_labels", lambda **k: ["x"])
    monkeypatch.setattr(report_instance, "_get_issue_description", lambda **k: "desc")

    report_instance.report_success(sample_job, config)

    jira.create_issue.assert_called_once()
    report_instance.logger.warning.assert_called_once_with(
        "Could not create success issue in %s: %s",
        "LPTOCPCI",
        "Method Not Allowed",
    )


def test_report_success_continues_next_rule_after_create_issue_failure(
    report_instance,
    sample_job,
    monkeypatch,
):
    rule_a = Rule(rule_dict={"jira_project": "PROJA"})
    rule_b = Rule(rule_dict={"jira_project": "PROJB"})
    config = MagicMock()
    config.success_rules = [rule_a, rule_b]
    config.additional_labels_file = None
    jira = MagicMock()
    jira.create_issue.side_effect = [
        JIRAError("fail", 405, "https://example/rest/api/3/issue"),
        MagicMock(),
    ]
    config.jira = jira
    monkeypatch.setattr(report_instance, "_get_issue_labels", lambda **k: ["x"])
    monkeypatch.setattr(report_instance, "_get_issue_description", lambda **k: "desc")

    report_instance.report_success(sample_job, config)

    assert jira.create_issue.call_count == 2
    report_instance.logger.warning.assert_called_once_with(
        "Could not create success issue in %s: %s",
        "PROJA",
        "fail",
    )
