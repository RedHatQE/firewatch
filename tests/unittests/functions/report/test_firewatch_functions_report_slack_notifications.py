from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from src.objects.failure import Failure
from src.objects.failure_rule import FailureRule
from src.objects.job import Job
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


class TestRehearsalWebhookIntegration:
    """Tests that Report.__init__ actually calls _notify_failure_webhooks
    for rehearsal jobs with failures. This exercises the real code path
    that CI hits, not just the method in isolation."""

    @patch("src.report.report.SlackClient.post_webhook")
    @patch("src.report.report.shutil.rmtree")
    def test_rehearsal_with_failures_fires_webhook(self, mock_rmtree, mock_post_webhook):
        config = MagicMock()
        config.slack_webhook_url = "https://hooks.slack.com/test"
        config.slack_bot_token = None
        config.default_jira_project = "TEST"
        config.fail_with_test_failures = False
        config.fail_with_pod_failures = False
        config.failure_rules = [
            FailureRule({
                "step": "*",
                "failure_type": "all",
                "classification": "Test",
                "jira_project": "TEST",
            })
        ]

        job = MagicMock(spec=Job)
        job.is_rehearsal = True
        job.is_retriggered = False
        job.name = "rehearse-99999-pull-ci-test-job"
        job.build_id = "99999"
        job.download_path = "/tmp/99999"
        job.has_test_failures = False
        job.has_pod_failures = True
        job.failures = [Failure(failed_step="fail-step", failure_type="pod_failure")]

        with pytest.raises(SystemExit) as exc_info:
            Report(firewatch_config=config, job=job)

        assert exc_info.value.code == 0
        mock_post_webhook.assert_called_once()
        payload_text = mock_post_webhook.call_args[0][1]
        assert "fail-step" in payload_text
        assert "pod_failure" in payload_text

    @patch("src.report.report.SlackClient.post_webhook")
    @patch("src.report.report.shutil.rmtree")
    def test_rehearsal_without_webhook_url_skips_notification(self, mock_rmtree, mock_post_webhook):
        config = MagicMock()
        config.slack_webhook_url = None
        config.slack_bot_token = None
        config.default_jira_project = "TEST"
        config.fail_with_test_failures = False
        config.fail_with_pod_failures = False
        config.failure_rules = [
            FailureRule({
                "step": "*",
                "failure_type": "all",
                "classification": "Test",
                "jira_project": "TEST",
            })
        ]

        job = MagicMock(spec=Job)
        job.is_rehearsal = True
        job.is_retriggered = False
        job.name = "rehearse-99999-pull-ci-test-job"
        job.build_id = "99999"
        job.download_path = "/tmp/99999"
        job.has_test_failures = False
        job.has_pod_failures = True
        job.failures = [Failure(failed_step="fail-step", failure_type="pod_failure")]

        with pytest.raises(SystemExit):
            Report(firewatch_config=config, job=job)

        mock_post_webhook.assert_not_called()

    @patch("src.report.report.SlackClient.post_webhook")
    @patch("src.report.report.shutil.rmtree")
    def test_rehearsal_no_failures_skips_notification(self, mock_rmtree, mock_post_webhook):
        config = MagicMock()
        config.slack_webhook_url = "https://hooks.slack.com/test"
        config.slack_bot_token = None
        config.default_jira_project = "TEST"
        config.fail_with_test_failures = False
        config.fail_with_pod_failures = False

        job = MagicMock(spec=Job)
        job.is_rehearsal = True
        job.is_retriggered = False
        job.name = "rehearse-99999-pull-ci-test-job"
        job.build_id = "99999"
        job.download_path = "/tmp/99999"
        job.has_test_failures = False
        job.has_pod_failures = False
        job.failures = []

        with pytest.raises(SystemExit):
            Report(firewatch_config=config, job=job)

        mock_post_webhook.assert_not_called()


class TestNotifyFailureWebhooks:
    def _make_config(self, webhook_url="https://hooks.slack.com/test", failure_rules=None):
        config = MagicMock()
        config.slack_webhook_url = webhook_url
        config.slack_bot_token = None
        config.default_jira_project = "TEST"
        config.failure_rules = failure_rules
        return config

    def _make_failure(self, step="fail-step", failure_type="pod_failure"):
        return Failure(failed_step=step, failure_type=failure_type)

    def _make_rule(self, step="*", failure_type="all", classification="Test", jira_project="TEST"):
        return FailureRule({
            "step": step,
            "failure_type": failure_type,
            "classification": classification,
            "jira_project": jira_project,
        })

    def test_fires_webhook_for_matched_failures(self, report_instance):
        rule = self._make_rule()
        config = self._make_config(failure_rules=[rule])
        failure = self._make_failure()
        job = MagicMock(spec=Job)
        job.name = "rehearse-12345-test-job"
        job.build_id = "99999"

        with patch.object(report_instance, "_notify_slack") as mock_notify:
            report_instance._notify_failure_webhooks([failure], config, job)

        mock_notify.assert_called_once()
        text = mock_notify.call_args[0][1]
        assert "fail-step" in text
        assert "pod_failure" in text
        assert job.name in text

    def test_skips_webhook_when_no_webhook_url(self, report_instance):
        rule = self._make_rule()
        config = self._make_config(webhook_url=None, failure_rules=[rule])
        failure = self._make_failure()
        job = MagicMock(spec=Job)
        job.name = "test-job"
        job.build_id = "1"

        with patch.object(report_instance, "_notify_slack") as mock_notify:
            report_instance._notify_failure_webhooks([failure], config, job)

        mock_notify.assert_not_called()

    def test_skips_ignored_rules(self, report_instance):
        rule = FailureRule({
            "step": "fail-step",
            "failure_type": "all",
            "classification": "Ignore",
            "jira_project": "TEST",
            "ignore": True,
        })
        config = self._make_config(failure_rules=[rule])
        failure = self._make_failure()
        job = MagicMock(spec=Job)
        job.name = "test-job"
        job.build_id = "1"

        with patch.object(report_instance, "_notify_slack") as mock_notify:
            report_instance._notify_failure_webhooks([failure], config, job)

        mock_notify.assert_not_called()

    def test_fires_once_per_failure_rule_pair(self, report_instance):
        rule_a = self._make_rule(step="fail-*", jira_project="A")
        rule_b = self._make_rule(step="other-*", jira_project="B")
        config = self._make_config(failure_rules=[rule_a, rule_b])
        failures = [
            self._make_failure(step="fail-step"),
            self._make_failure(step="other-step"),
        ]
        job = MagicMock(spec=Job)
        job.name = "test-job"
        job.build_id = "1"

        with patch.object(report_instance, "_notify_slack") as mock_notify:
            report_instance._notify_failure_webhooks(failures, config, job)

        assert mock_notify.call_count == 2


def test_notify_slack_calls_post_webhook_when_webhook_url_set(report_instance):
    config = MagicMock()
    config.slack_webhook_url = "https://hooks.slack.com/services/XXX"
    config.slack_bot_token = "xoxb-unused"
    with patch("src.report.report.SlackClient.post_webhook") as mock_post:
        report_instance._notify_slack("#chan", "hello", config)
    mock_post.assert_called_once_with("https://hooks.slack.com/services/XXX", "hello")


def test_notify_slack_creates_client_and_send_notification_when_only_bot_token(report_instance):
    config = MagicMock()
    config.slack_webhook_url = None
    config.slack_bot_token = "xoxb-abc"
    mock_client = MagicMock()
    with patch("src.report.report.SlackClient", return_value=mock_client) as mock_cls:
        report_instance._notify_slack("#my-channel", "body text", config)
    mock_cls.assert_called_once_with(token="xoxb-abc")
    mock_client.send_notification.assert_called_once_with(
        channel="#my-channel",
        text="body text",
    )


def test_notify_slack_does_nothing_when_no_webhook_or_token(report_instance):
    config = MagicMock()
    config.slack_webhook_url = None
    config.slack_bot_token = None
    with (
        patch("src.report.report.SlackClient.post_webhook") as mock_post,
        patch("src.report.report.SlackClient") as mock_cls,
    ):
        report_instance._notify_slack("#c", "t", config)
    mock_post.assert_not_called()
    mock_cls.assert_not_called()


def test_notify_slack_logs_warning_without_propagating_when_slack_raises(report_instance):
    config = MagicMock()
    config.slack_webhook_url = "https://hooks.example/hook"
    config.slack_bot_token = None
    with patch(
        "src.report.report.SlackClient.post_webhook",
        side_effect=RuntimeError("network down"),
    ):
        report_instance._notify_slack("#c", "t", config)
    report_instance.logger.warning.assert_called_once()
    fmt, exc = report_instance.logger.warning.call_args[0]
    assert fmt == "Slack notification failed: %s"
    assert isinstance(exc, RuntimeError)
    assert str(exc) == "network down"


def test_slack_new_issue_calls_notify_when_channel_set(report_instance, sample_job):
    rule = MagicMock()
    rule.slack_channel = "#alerts"
    config = MagicMock()
    with patch.object(report_instance, "_notify_slack") as mock_notify:
        report_instance._slack_new_issue("ABC-1", "summary line", sample_job, rule, config)
    expected_url = (
        f"https://prow.ci.openshift.org/view/gs/test-platform-results/logs/{sample_job.name}/{sample_job.build_id}"
    )
    mock_notify.assert_called_once_with(
        "#alerts",
        f"[ABC-1] summary line\n{expected_url}",
        config,
    )


def test_slack_new_issue_skips_when_no_channel_and_no_webhook(report_instance, sample_job):
    rule = MagicMock()
    rule.slack_channel = None
    rule.slack_user = None
    config = MagicMock()
    config.slack_webhook_url = None
    with patch.object(report_instance, "_notify_slack") as mock_notify:
        report_instance._slack_new_issue("ABC-1", "s", sample_job, rule, config)
    mock_notify.assert_not_called()


def test_slack_new_issue_fires_when_no_channel_but_webhook_set(report_instance, sample_job):
    rule = MagicMock()
    rule.slack_channel = None
    rule.slack_user = None
    config = MagicMock()
    config.slack_webhook_url = "https://hooks.slack.com/services/XXX"
    expected_url = (
        f"https://prow.ci.openshift.org/view/gs/test-platform-results/logs/{sample_job.name}/{sample_job.build_id}"
    )
    with patch.object(report_instance, "_notify_slack") as mock_notify:
        report_instance._slack_new_issue("ABC-1", "summary", sample_job, rule, config)
    mock_notify.assert_called_once_with(
        "",
        f"[ABC-1] summary\n{expected_url}",
        config,
    )


def test_slack_new_issue_passes_channel_when_both_channel_and_webhook_set(report_instance, sample_job):
    rule = MagicMock()
    rule.slack_channel = "#alerts"
    config = MagicMock()
    config.slack_webhook_url = "https://hooks.slack.com/services/XXX"
    with patch.object(report_instance, "_notify_slack") as mock_notify:
        report_instance._slack_new_issue("ABC-1", "summary", sample_job, rule, config)
    assert mock_notify.call_args[0][0] == "#alerts"


def test_slack_duplicate_calls_notify_when_channel_set(report_instance, sample_job):
    rule = MagicMock()
    rule.slack_channel = "#dup"
    config = MagicMock()
    expected_url = (
        f"https://prow.ci.openshift.org/view/gs/test-platform-results/logs/{sample_job.name}/{sample_job.build_id}"
    )
    expected_text = (
        f"Duplicate failure detected on ROX-99\nJob: {sample_job.name} | Build: {sample_job.build_id}\n{expected_url}"
    )
    with patch.object(report_instance, "_notify_slack") as mock_notify:
        report_instance._slack_duplicate("ROX-99", sample_job, rule, config)
    mock_notify.assert_called_once_with("#dup", expected_text, config)


def test_slack_duplicate_skips_when_no_channel_and_no_webhook(report_instance, sample_job):
    rule = MagicMock()
    rule.slack_channel = None
    rule.slack_user = None
    config = MagicMock()
    config.slack_webhook_url = None
    with patch.object(report_instance, "_notify_slack") as mock_notify:
        report_instance._slack_duplicate("ROX-99", sample_job, rule, config)
    mock_notify.assert_not_called()


def test_slack_duplicate_fires_when_no_channel_but_webhook_set(report_instance, sample_job):
    rule = MagicMock()
    rule.slack_channel = None
    rule.slack_user = None
    config = MagicMock()
    config.slack_webhook_url = "https://hooks.slack.com/services/XXX"
    expected_url = (
        f"https://prow.ci.openshift.org/view/gs/test-platform-results/logs/{sample_job.name}/{sample_job.build_id}"
    )
    expected_text = (
        f"Duplicate failure detected on ROX-99\nJob: {sample_job.name} | Build: {sample_job.build_id}\n{expected_url}"
    )
    with patch.object(report_instance, "_notify_slack") as mock_notify:
        report_instance._slack_duplicate("ROX-99", sample_job, rule, config)
    mock_notify.assert_called_once_with("", expected_text, config)


def test_slack_duplicate_passes_channel_when_both_channel_and_webhook_set(report_instance, sample_job):
    rule = MagicMock()
    rule.slack_channel = "#dup"
    config = MagicMock()
    config.slack_webhook_url = "https://hooks.slack.com/services/XXX"
    with patch.object(report_instance, "_notify_slack") as mock_notify:
        report_instance._slack_duplicate("ROX-99", sample_job, rule, config)
    assert mock_notify.call_args[0][0] == "#dup"


def test_slack_success_calls_notify_when_channel_set(report_instance, sample_job):
    rule = MagicMock()
    rule.slack_channel = "#win"
    config = MagicMock()
    mock_now = MagicMock()
    mock_now.strftime.return_value = "04-14-2026"
    with (
        patch("src.report.report.datetime") as mock_dt,
        patch.object(report_instance, "_notify_slack") as mock_notify,
    ):
        mock_dt.now.return_value = mock_now
        report_instance._slack_success("XYZ-9", sample_job, rule, config)
    mock_notify.assert_called_once_with(
        "#win",
        f"[XYZ-9] Job {sample_job.name} passed - 04-14-2026",
        config,
    )
    mock_now.strftime.assert_called_once_with("%m-%d-%Y")


def test_slack_success_skips_when_no_channel_and_no_webhook(report_instance, sample_job):
    rule = MagicMock()
    rule.slack_channel = None
    rule.slack_user = None
    config = MagicMock()
    config.slack_webhook_url = None
    with patch.object(report_instance, "_notify_slack") as mock_notify:
        report_instance._slack_success("XYZ-9", sample_job, rule, config)
    mock_notify.assert_not_called()


def test_slack_success_fires_when_no_channel_but_webhook_set(report_instance, sample_job):
    rule = MagicMock()
    rule.slack_channel = None
    rule.slack_user = None
    config = MagicMock()
    config.slack_webhook_url = "https://hooks.slack.com/services/XXX"
    mock_now = MagicMock()
    mock_now.strftime.return_value = "04-30-2026"
    with (
        patch("src.report.report.datetime") as mock_dt,
        patch.object(report_instance, "_notify_slack") as mock_notify,
    ):
        mock_dt.now.return_value = mock_now
        report_instance._slack_success("XYZ-9", sample_job, rule, config)
    mock_notify.assert_called_once_with(
        "",
        f"[XYZ-9] Job {sample_job.name} passed - 04-30-2026",
        config,
    )


def test_slack_success_passes_channel_when_both_channel_and_webhook_set(report_instance, sample_job):
    rule = MagicMock()
    rule.slack_channel = "#win"
    config = MagicMock()
    config.slack_webhook_url = "https://hooks.slack.com/services/XXX"
    with (
        patch("src.report.report.datetime"),
        patch.object(report_instance, "_notify_slack") as mock_notify,
    ):
        report_instance._slack_success("XYZ-9", sample_job, rule, config)
    assert mock_notify.call_args[0][0] == "#win"


class TestShouldNotifySlack:
    def test_returns_true_when_channel_set(self, report_instance):
        rule = MagicMock()
        rule.slack_channel = "#alerts"
        config = MagicMock()
        config.slack_webhook_url = None
        assert report_instance._should_notify_slack(rule, config) is True

    def test_returns_true_when_webhook_set(self, report_instance):
        rule = MagicMock()
        rule.slack_channel = None
        config = MagicMock()
        config.slack_webhook_url = "https://hooks.slack.com/services/XXX"
        assert report_instance._should_notify_slack(rule, config) is True

    def test_returns_true_when_both_set(self, report_instance):
        rule = MagicMock()
        rule.slack_channel = "#alerts"
        config = MagicMock()
        config.slack_webhook_url = "https://hooks.slack.com/services/XXX"
        assert report_instance._should_notify_slack(rule, config) is True

    def test_returns_false_when_neither_set(self, report_instance):
        rule = MagicMock()
        rule.slack_channel = None
        rule.slack_user = None
        config = MagicMock()
        config.slack_webhook_url = None
        assert report_instance._should_notify_slack(rule, config) is False

    def test_returns_false_when_channel_is_empty_string(self, report_instance):
        rule = MagicMock()
        rule.slack_channel = ""
        rule.slack_user = None
        config = MagicMock()
        config.slack_webhook_url = None
        assert report_instance._should_notify_slack(rule, config) is False

    def test_returns_false_when_webhook_is_empty_string(self, report_instance):
        rule = MagicMock()
        rule.slack_channel = None
        rule.slack_user = None
        config = MagicMock()
        config.slack_webhook_url = ""
        assert report_instance._should_notify_slack(rule, config) is False

    def test_returns_true_when_slack_user_set(self, report_instance):
        rule = MagicMock()
        rule.slack_channel = None
        rule.slack_user = "user@redhat.com"
        config = MagicMock()
        config.slack_webhook_url = None
        assert report_instance._should_notify_slack(rule, config) is True

    def test_returns_false_when_slack_user_is_none(self, report_instance):
        rule = MagicMock()
        rule.slack_channel = None
        rule.slack_user = None
        config = MagicMock()
        config.slack_webhook_url = None
        assert report_instance._should_notify_slack(rule, config) is False
