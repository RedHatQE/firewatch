import pytest

from unittest.mock import MagicMock, patch
from logging import getLogger as get_logger
from jira.exceptions import JIRAError
from src.objects.jira_base import Jira


@pytest.fixture
def mock_jira_connection():
    """Provides a MagicMock for the Jira connection."""
    return MagicMock()


@pytest.fixture
def mock_jira(mock_jira_connection):
    """
    Provides the Jira instance with a mocked connection and logger,
    bypassing __init__.
    """
    with patch.object(Jira, "__init__", lambda s, jira_config_path: None):
        instance = Jira(jira_config_path="dummy/path/ignored")
        instance.connection = mock_jira_connection
        instance.logger = get_logger("mock_jira_logger_for_test")
        instance.url = "http://mock-jira.test"
    return instance


class TestJiraTransitionIssue:
    def test_transition_success(self, mock_jira, mock_jira_connection):
        """Verify successful transition logs correctly and makes the call."""

        # Call the function - should return True & not raise error
        result = mock_jira.transition_issue(
            issue_id_or_key="INTEROP-123",
            transition_name="Done",
            comment="Transitioning to Done.",
        )

        mock_jira_connection.transition_issue.assert_called_once_with(
            issue="INTEROP-123", transition="Done", comment="Transitioning to Done."
        )
        assert result is True

    def test_transition_jira_error_returns_false(self, mock_jira, mock_jira_connection, caplog):
        """Verify JIRAError returns False."""

        # Simulate a Jira Exception, method should return False
        error_text = "You do not have permission to transition this issue."
        mock_jira_connection.transition_issue.side_effect = JIRAError(status_code=401, text=error_text)

        # Call the function - Should return False
        result = mock_jira.transition_issue(
            issue_id_or_key="INTEROP-123",
            transition_name="Done",
            comment="Attempting transition.",
        )

        mock_jira_connection.transition_issue.assert_called_once()
        # Assert method returns False on caught JIRAError
        assert result is False
        assert f"Failed to transition issue INTEROP-123 to 'Done'. Status Code: 401. Error: {error_text}" in caplog.text
        assert "Successfully transitioned issue" not in caplog.text

    def test_transition_unexpected_error(self, mock_jira, mock_jira_connection, caplog):
        """
        Verify generic Exception is caught internally, returns False & logs error.
        """
        error_message = "Network timeout"
        # Simulate an unexpected general exception
        mock_jira_connection.transition_issue.side_effect = Exception(error_message)

        # Call the function. If it raises an exception, the test will fail here.
        result = mock_jira.transition_issue(
            issue_id_or_key="INTEROP-123",
            transition_name="Done",
        )

        # Check the underlying connection method was called
        mock_jira_connection.transition_issue.assert_called_once()

        # Assert the method returned False because a generic exception was caught
        assert result is False, "Expected False return value when internal exception occurs"

        # Assert that the correct error log message was generated
        assert f"An unexpected error occurred while transitioning INTEROP-123: {error_message}" in caplog.text
        assert "Successfully transitioned issue" not in caplog.text
