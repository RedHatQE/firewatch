import pytest
from unittest.mock import MagicMock, patch
from logging import getLogger as get_logger, INFO, WARNING, ERROR
from jira import Issue as JiraIssueObject
from jira.exceptions import JIRAError


from src.report.report import Report
from src.objects.jira_base import Jira
from src.objects.job import Job


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


@pytest.fixture
def standard_transition_map():
    """Provides the standard project transition map."""
    return {"LPINTEROP": "PASS", "CSPIT": "PASS", "OCSQE": "DONE", "DEFAULT": "CLOSED"}


class TestReportClosePassingJobIssue:
    @pytest.mark.parametrize(
        "issue_project_key, expected_transition_name",
        [
            ("LPINTEROP", "PASS"),
            ("CSPIT", "PASS"),
            ("OCSQE", "DONE"),
            ("UNKNOWNPROJ", "CLOSED"),  # Should use DEFAULT from map
            ("anotherproj", "CLOSED"),
        ],
    )
    def test_close_success_uses_correct_transition(
        self,
        report_instance,
        mock_job,
        mock_jira_for_report,
        mock_jira_issue,
        standard_transition_map,
        issue_project_key,
        expected_transition_name,
        caplog,
    ):
        """Verify correct close transition from the standard map."""
        caplog.set_level(INFO)
        issue_id = f"{issue_project_key}-123"
        mock_jira_issue.fields.project.key = issue_project_key

        mock_jira_for_report.get_issue_by_id_or_key.return_value = mock_jira_issue
        mock_jira_for_report.transition_issue.return_value = True

        report_instance.close_passing_job_issue(
            job=mock_job,
            jira=mock_jira_for_report,
            issue_id=issue_id,
            project_transition_mapping=standard_transition_map,
        )

        mock_jira_for_report.get_issue_by_id_or_key.assert_called_once_with(issue_id)
        expected_comment = (
            f"Automatically transitioned to '{expected_transition_name}' by Firewatch: "
            f"Job {mock_job.name} #{mock_job.build_id} passed successfully after ticket creation."
        )
        mock_jira_for_report.transition_issue.assert_called_once_with(
            issue_id_or_key=issue_id, transition_name=expected_transition_name, comment=expected_comment
        )
        # Assertion to match Transition AND comment
        assert mock_jira_for_report.transition_issue.call_args[1]["transition_name"] == expected_transition_name
        assert mock_jira_for_report.transition_issue.call_args[1]["comment"] == expected_comment
        # Check log messages
        assert f"Attempting to auto-close issue {issue_id} (Project: {issue_project_key})" in caplog.text
        assert (
            f"Determined target transition: '{expected_transition_name}' for project {issue_project_key} using mapping."
            in caplog.text
        )
        assert f"Successfully auto-closed/transitioned issue {issue_id}." in caplog.text

    def test_close_map_missing_default_key_uses_hardcoded_fallback(
        self, report_instance, mock_job, mock_jira_for_report, mock_jira_issue, caplog
    ):
        """Verify hardcoded 'Closed' is used if 'DEFAULT' key is missing from the provided map."""
        caplog.set_level(INFO)
        issue_id = "ROX-789"
        mock_jira_issue.fields.project.key = "ROX"
        mock_jira_for_report.get_issue_by_id_or_key.return_value = mock_jira_issue
        mock_jira_for_report.transition_issue.return_value = True

        map_without_default = {"LPINTEROP": "PASS"}  # Map is missing 'DEFAULT'

        report_instance.close_passing_job_issue(
            job=mock_job, jira=mock_jira_for_report, issue_id=issue_id, project_transition_mapping=map_without_default
        )

        mock_jira_for_report.transition_issue.assert_called_once()
        # Assert call was made with the hardcoded default "Closed" from the function
        assert mock_jira_for_report.transition_issue.call_args[1]["transition_name"] == "Closed"

        # Assert both expected log messages
        assert "Transition map missing 'DEFAULT' key, using hardcoded 'Closed'." in caplog.text
        # *** THIS IS THE CORRECTED ASSERTION ***
        assert f"Determined target transition: 'Closed' for project ROX using mapping." in caplog.text
        assert f"Successfully auto-closed/transitioned issue {issue_id}." in caplog.text

    def test_close_transition_call_fails(
        self, report_instance, mock_job, mock_jira_for_report, mock_jira_issue, standard_transition_map, caplog
    ):
        """Verify logs warning when jira.transition_issue returns False."""
        caplog.set_level(INFO)
        issue_id = "LPINTEROP-001"
        mock_jira_issue.fields.project.key = "LPINTEROP"
        mock_jira_for_report.get_issue_by_id_or_key.return_value = mock_jira_issue
        mock_jira_for_report.transition_issue.return_value = False

        report_instance.close_passing_job_issue(
            job=mock_job,
            jira=mock_jira_for_report,
            issue_id=issue_id,
            project_transition_mapping=standard_transition_map,
        )

        mock_jira_for_report.get_issue_by_id_or_key.assert_called_once_with(issue_id)
        mock_jira_for_report.transition_issue.assert_called_once()
        assert f"Attempting to auto-close issue {issue_id} (Project: LPINTEROP)" in caplog.text
        assert "Determined target transition: 'PASS' for project LPINTEROP using mapping." in caplog.text
        assert (
            f"Attempt to auto-transition issue {issue_id} failed (check previous log from Jira layer)." in caplog.text
        )
        assert f"Successfully auto-closed/transitioned issue {issue_id}." not in caplog.text

    def test_close_get_issue_by_id_or_key_raises_jiraerror(
        self, report_instance, mock_job, mock_jira_for_report, standard_transition_map, caplog
    ):
        """Verify logs JIRAError and stops if get_issue_by_id_or_key raises JIRAError."""
        caplog.set_level(ERROR)
        issue_id = "NONEXISTENT-1"
        error_text = "Issue Does Not Exist"
        mock_jira_for_report.get_issue_by_id_or_key.side_effect = JIRAError(status_code=404, text=error_text)

        report_instance.close_passing_job_issue(
            job=mock_job,
            jira=mock_jira_for_report,
            issue_id=issue_id,
            project_transition_mapping=standard_transition_map,
        )

        mock_jira_for_report.get_issue_by_id_or_key.assert_called_once_with(issue_id)
        mock_jira_for_report.transition_issue.assert_not_called()
        assert f"JIRAError preventing auto-closure of {issue_id}: {error_text}" in caplog.text
        assert "Successfully auto-closed/transitioned issue" not in caplog.text

    def test_close_unexpected_error_during_transition(
        self, report_instance, mock_job, mock_jira_for_report, mock_jira_issue, standard_transition_map, caplog
    ):
        """Verify logs generic Exception if transition_issue raises it."""
        caplog.set_level(ERROR)
        issue_id = "PROJ-UNEXP"
        mock_jira_issue.fields.project.key = "PROJ"  # This will use "DEFAULT" from map for transition name
        error_message = "Network connection totally failed"
        mock_jira_for_report.get_issue_by_id_or_key.return_value = mock_jira_issue
        mock_jira_for_report.transition_issue.side_effect = Exception(error_message)

        report_instance.close_passing_job_issue(
            job=mock_job,
            jira=mock_jira_for_report,
            issue_id=issue_id,
            project_transition_mapping=standard_transition_map,
        )

        mock_jira_for_report.get_issue_by_id_or_key.assert_called_once_with(issue_id)
        mock_jira_for_report.transition_issue.assert_called_once()
        assert f"Unexpected error during auto-closure attempt for issue {issue_id}: {error_message}" in caplog.text
        assert "Successfully auto-closed/transitioned issue" not in caplog.text
