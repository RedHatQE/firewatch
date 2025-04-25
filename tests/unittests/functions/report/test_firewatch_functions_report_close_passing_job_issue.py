import pytest
from unittest.mock import MagicMock, patch
from logging import getLogger as get_logger, INFO
from jira import Issue as JiraIssueObject
from jira.exceptions import JIRAError


from src.report.report import Report
from src.objects.jira_base import Jira
from src.objects.job import Job
from src.report.constants import LPINTEROP_BOARD_NAME


@pytest.fixture
def mock_jira_for_report():
    """Provides a MagicMock Jira object."""
    mock = MagicMock(spec=Jira)
    mock.get_issue_by_id_or_key = MagicMock()
    mock.transition_issue = MagicMock()
    return mock


@pytest.fixture
def mock_job():
    """Provides a simple mock Job object with necessary attributes."""
    job = MagicMock(spec=Job)
    job.name = "openshift-pipelines-interop-aws"
    job.build_id = "1899828911936638976"
    return job


@pytest.fixture
def mock_jira_issue():
    """Provides a MagicMock representing a Jira Issue object."""
    issue = MagicMock(spec=JiraIssueObject)
    issue.key = "LPINTEROP-5358"
    issue.id = "5358"
    issue.fields = MagicMock()
    issue.fields.project = MagicMock()
    issue.fields.project.key = "LPINTEROP"
    return issue


@pytest.fixture
def report_instance(mock_job):
    """Provides a Report instance, bypassing __init__ for isolation."""
    with patch.object(Report, "__init__", lambda s, firewatch_config, job: None):
        instance = Report(firewatch_config=None, job=mock_job)  # Args ignored by patched init
        instance.logger = get_logger("mock_report_logger_for_test")
        instance.logger.propagate = True  # For caplog
    return instance


class TestReportClosePassingJobIssue:
    def test_close_success_lpinterop(self, report_instance, mock_job, mock_jira_for_report, mock_jira_issue, caplog):
        """Verify successful close for LPINTEROP project uses 'PASS' transition."""
        caplog.set_level(INFO)
        issue_id = f"{LPINTEROP_BOARD_NAME}-123"
        mock_jira_issue.fields.project.key = LPINTEROP_BOARD_NAME
        mock_jira_for_report.get_issue_by_id_or_key.return_value = mock_jira_issue
        mock_jira_for_report.transition_issue.return_value = True  # Simulate successful transition

        report_instance.close_passing_job_issue(job=mock_job, jira=mock_jira_for_report, issue_id=issue_id)

        mock_jira_for_report.get_issue_by_id_or_key.assert_called_once_with(issue_id)
        expected_comment = (
            f"Automatically transitioned to 'PASS' by Firewatch: "
            f"Job {mock_job.name} #{mock_job.build_id} passed successfully after ticket creation."
        )
        mock_jira_for_report.transition_issue.assert_called_once_with(
            issue_id_or_key=issue_id, transition_name="PASS", comment=expected_comment
        )
        # Assertion to match actual log
        assert f"Successfully auto-closed/transitioned issue {issue_id}." in caplog.text

    def test_close_success_other_project(
        self, report_instance, mock_job, mock_jira_for_report, mock_jira_issue, caplog
    ):
        """Verify successful close for other projects uses 'Closed' transition."""
        caplog.set_level(INFO)
        project_key = "TRACING"
        issue_id = f"{project_key}-456"
        mock_jira_issue.fields.project.key = project_key
        mock_jira_for_report.get_issue_by_id_or_key.return_value = mock_jira_issue
        mock_jira_for_report.transition_issue.return_value = True

        report_instance.close_passing_job_issue(job=mock_job, jira=mock_jira_for_report, issue_id=issue_id)

        mock_jira_for_report.get_issue_by_id_or_key.assert_called_once_with(issue_id)
        expected_comment = (
            f"Automatically transitioned to 'Closed' by Firewatch: "
            f"Job {mock_job.name} #{mock_job.build_id} passed successfully after ticket creation."
        )
        mock_jira_for_report.transition_issue.assert_called_once_with(
            issue_id_or_key=issue_id, transition_name="Closed", comment=expected_comment
        )
        assert f"Successfully auto-closed/transitioned issue {issue_id}." in caplog.text

    def test_close_transition_fails_returns_false(
        self, report_instance, mock_job, mock_jira_for_report, mock_jira_issue, caplog
    ):
        """Verify logs warning when jira.transition_issue returns False."""
        caplog.set_level(INFO)
        project_key = "PROJ"
        issue_id = f"{project_key}-789"
        mock_jira_issue.fields.project.key = project_key
        mock_jira_for_report.get_issue_by_id_or_key.return_value = mock_jira_issue
        mock_jira_for_report.transition_issue.return_value = False  # Simulate transition failure

        report_instance.close_passing_job_issue(job=mock_job, jira=mock_jira_for_report, issue_id=issue_id)

        mock_jira_for_report.get_issue_by_id_or_key.assert_called_once_with(issue_id)
        mock_jira_for_report.transition_issue.assert_called_once()
        # Updated assertion to match actual log warning
        assert (
            f"Attempt to auto-transition issue {issue_id} failed (check previous log from Jira layer)." in caplog.text
        )
        assert f"Successfully auto-closed/transitioned issue {issue_id}." not in caplog.text

    def test_close_get_issue_fails(self, report_instance, mock_job, mock_jira_for_report, caplog):
        """Verify logs error and stops if get_issue_by_id_or_key fails."""
        caplog.set_level(INFO)
        issue_id = "NONEXIST-1"
        error_text = "Issue Does Not Exist"
        mock_jira_for_report.get_issue_by_id_or_key.side_effect = JIRAError(status_code=404, text=error_text)

        report_instance.close_passing_job_issue(job=mock_job, jira=mock_jira_for_report, issue_id=issue_id)

        mock_jira_for_report.get_issue_by_id_or_key.assert_called_once_with(issue_id)
        mock_jira_for_report.transition_issue.assert_not_called()  # Transition should not be attempted
        assert f"JIRAError preventing auto-closure of {issue_id}: {error_text}" in caplog.text
        assert "Successfully auto-closed/transitioned issue" not in caplog.text

    def test_close_unexpected_error(self, report_instance, mock_job, mock_jira_for_report, mock_jira_issue, caplog):
        """Verify logs error if an unexpected exception occurs."""
        caplog.set_level(INFO)
        issue_id = "PROJ-UNEXP"
        error_message = "Something else went wrong"
        mock_jira_issue.fields.project.key = "PROJ"
        mock_jira_for_report.get_issue_by_id_or_key.return_value = mock_jira_issue
        # Simulate error during transition call
        mock_jira_for_report.transition_issue.side_effect = Exception(error_message)

        report_instance.close_passing_job_issue(job=mock_job, jira=mock_jira_for_report, issue_id=issue_id)

        mock_jira_for_report.get_issue_by_id_or_key.assert_called_once_with(issue_id)
        mock_jira_for_report.transition_issue.assert_called_once()  # Transition was attempted
        # Updated assertion to match actual log error
        assert f"Failed to auto-transition issue {issue_id}: {error_message}" in caplog.text
        assert "Successfully auto-closed/transitioned issue" not in caplog.text
