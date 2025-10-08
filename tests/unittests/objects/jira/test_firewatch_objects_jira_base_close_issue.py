import pytest
from unittest.mock import MagicMock
from jira.exceptions import JIRAError
from pytest import MonkeyPatch
from src.objects.jira_base import Jira


@pytest.fixture
def mock_jira(monkeypatch: MonkeyPatch):
    """
    Provides a Jira instance with a mocked __init__ and mocked dependencies
    for testing instance methods in isolation.
    """
    # Patch Jira.__init__ to avoid file access and network connections
    monkeypatch.setattr(Jira, "__init__", lambda self, jira_config_path=None: None)

    # Create the instance and attach mock objects
    jira = Jira()
    jira.logger = MagicMock()
    jira.get_issue_by_id_or_key = MagicMock()
    jira.connection = MagicMock()
    return jira


def test_close_issue_success(mock_jira: Jira):
    """
    Tests the successful execution path of close_issue.
    """
    issue_id = "TEST-123"
    mock_issue = MagicMock()
    mock_issue.key = issue_id
    mock_jira.get_issue_by_id_or_key.return_value = mock_issue

    # Call the method
    mock_jira.close_issue(issue_id)

    # Assert
    # 1. Verify the method calls
    mock_jira.get_issue_by_id_or_key.assert_called_once_with(issue_id)
    mock_jira.connection.transition_issue.assert_called_once_with(
        issue=issue_id,
        transition="closed",
        comment="Closed by [firewatch|https://github.com/CSPI-QE/firewatch].",
    )

    # 2. Verify ALL expected logs were made
    mock_jira.logger.info.assert_any_call("Closing issue %s with transition 'closed'...", issue_id)
    mock_jira.logger.info.assert_any_call("Issue %s has been successfully closed.", issue_id)

    # 3. Verify no errors were logged
    mock_jira.logger.error.assert_not_called()


def test_close_issue_jira_error(mock_jira: Jira):
    """
    Tests that a JIRAError is caught and logged correctly.
    """
    issue_id = "TEST-123"
    error_text = "Transition not allowed"
    mock_issue = MagicMock()
    mock_issue.key = issue_id
    mock_jira.get_issue_by_id_or_key.return_value = mock_issue

    error = JIRAError(status_code=400, text=error_text)
    mock_jira.connection.transition_issue.side_effect = error

    # Call method
    mock_jira.close_issue(issue_id)

    # Assert
    # Use assert_called_once_with for a stricter check than assert_any_call
    mock_jira.logger.error.assert_called_once_with("Failed to close issue %s. Jira error: %s", issue_id, error_text)


def test_close_issue_unexpected_exception(mock_jira: Jira):
    """
    Tests that a generic Exception is caught and logged correctly.
    """
    # Arrange
    issue_id = "TEST-123"
    mock_issue = MagicMock()
    mock_issue.key = issue_id
    mock_jira.get_issue_by_id_or_key.return_value = mock_issue

    # The actual exception object is what gets logged
    exception_object = Exception("Unexpected failure")
    mock_jira.connection.transition_issue.side_effect = exception_object

    # Call method
    mock_jira.close_issue(issue_id)

    # Assert
    # Assert that the error was logged exactly once, with the exception object itself
    mock_jira.logger.error.assert_called_once_with(
        "Unexpected error while closing issue %s: %s", issue_id, exception_object
    )
