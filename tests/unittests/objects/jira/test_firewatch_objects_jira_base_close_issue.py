import logging

import pytest
from unittest.mock import MagicMock
from jira.exceptions import JIRAError
from pytest import MonkeyPatch
from src.objects.jira_base import Jira

from tests.unittests.objects.jira.test_jira import _assert_adf_doc
from tests.unittests.objects.jira.test_jira import _post_request_json


@pytest.fixture
def jira(patch_jira_api_requests, jira, caplog):
    jira.logger.handlers[0] = caplog.handler
    yield jira


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


def test_close_issue_success(patch_jira_api_requests, fake_issue_key, jira: Jira, caplog):
    with caplog.at_level(logging.INFO, logger="src.objects.jira_base"):
        jira.close_issue(fake_issue_key)
    transition_urls = [u for u in patch_jira_api_requests["post"] if "/transitions" in u]
    assert len(transition_urls) == 1
    _args, kwargs = patch_jira_api_requests["post"][transition_urls[0]]
    payload = _post_request_json(kwargs)
    assert "update" in payload
    comment_body = payload["update"]["comment"][0]["add"]["body"]
    assert not isinstance(comment_body, str), (
        "Jira Cloud REST v3 expects transition comment body as ADF, not a plain string"
    )
    _assert_adf_doc(comment_body)
    assert "Closing issue" in caplog.text
    assert "successfully closed" in caplog.text


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
    mock_jira.connection.find_transitionid_by_name.return_value = 5
    mock_jira.connection._session.post.side_effect = error

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
    mock_jira.connection.find_transitionid_by_name.return_value = 5
    mock_jira.connection._session.post.side_effect = exception_object

    # Call method
    mock_jira.close_issue(issue_id)

    # Assert
    # Assert that the error was logged exactly once, with the exception object itself
    mock_jira.logger.error.assert_called_once_with(
        "Unexpected error while closing issue %s: %s", issue_id, exception_object
    )
