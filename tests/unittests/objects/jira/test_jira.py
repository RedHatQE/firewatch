import json

import pytest
from jira import Issue
from unittest.mock import MagicMock, patch

from src.objects.jira_base import Jira
from tests.unittests.conftest import DEFAULT_JIRA_SERVER_URL


@pytest.fixture
def jira(patch_jira_api_requests, jira, caplog):
    jira.logger.handlers[0] = caplog.handler
    jira._caps = patch_jira_api_requests
    yield jira


@pytest.fixture
def fake_issue(fake_issue_id, jira) -> Issue:
    yield jira.get_issue_by_id_or_key(issue=fake_issue_id)


@pytest.fixture
def fake_attachment_path(tmp_path):
    path = tmp_path.joinpath("build_log.json")
    path.write_text("anything")
    yield path


class TestJiraApiRespondsWithSuccess:
    def test_get_issue_by_id_returns_jira_issue_from_jira_api_client_with_matching_issue_id(self, fake_issue_id, jira):
        issue = jira.get_issue_by_id_or_key(issue=fake_issue_id)
        assert isinstance(issue, Issue)
        assert issue.id == fake_issue_id


class TestJiraApiRespondsWithPermissionFailure:
    @pytest.fixture
    def fake_issue_add_attachment_response(self, mock_jira_api_response):
        yield mock_jira_api_response(
            _content=b'{"errorMessages": ["You do not have permission to create attachments for this issue."], "errors": {}}',
            _status_code=403,
        )

    def test_add_file_attachment_with_permission_failure_logs_failure_without_raising_exception(
        self, fake_issue, jira, fake_attachment_path, caplog
    ):
        jira.add_attachment_to_issue(
            issue=fake_issue,
            attachment_path=fake_attachment_path.as_posix(),
        )
        assert "You do not have permission to create attachments for this issue" in caplog.text


class TestCreateIssueEpicSearch:
    @pytest.fixture
    def mock_jira(self, monkeypatch):
        monkeypatch.setattr(Jira, "__init__", lambda self, jira_config_path=None: None)
        jira = Jira()
        jira.url = DEFAULT_JIRA_SERVER_URL
        jira.connection = MagicMock()

        created_issue = MagicMock()
        created_issue.key = "TEST-1"
        jira.connection.create_issue.return_value = created_issue

        return jira

    def test_epic_lookup_uses_unquoted_issue_key_for_cloud_compatibility(self, mock_jira):
        epic_issue = MagicMock()
        epic_issue.id = "20001"
        mock_jira.connection.search_issues.return_value = [epic_issue]

        mock_jira.create_issue(
            project="TEST",
            summary="Test issue",
            description="Description",
            issue_type="Bug",
            epic="INTEROP-1234",
        )

        mock_jira.connection.search_issues.assert_called_once_with(
            "issue=INTEROP-1234",
            maxResults=False,
        )
        mock_jira.connection.add_issues_to_epic.assert_called_once_with(
            epic_id="20001",
            issue_keys="TEST-1",
        )


class TestJiraInitAuth:
    @pytest.fixture
    def cloud_config(self, tmp_path):
        path = tmp_path / "cloud.json"
        path.write_text(
            json.dumps({
                "url": DEFAULT_JIRA_SERVER_URL,
                "token": "fake-token",
                "email": "user@redhat.com",
            })
        )
        return path

    @pytest.fixture
    def server_config(self, tmp_path):
        path = tmp_path / "server.json"
        path.write_text(
            json.dumps({
                "url": DEFAULT_JIRA_SERVER_URL,
                "token": "fake-token",
            })
        )
        return path

    @patch("src.objects.jira_base.JIRA")
    def test_uses_basic_auth_when_email_configured(self, mock_jira_class, cloud_config):
        Jira(jira_config_path=cloud_config.as_posix())

        call_kwargs = mock_jira_class.call_args.kwargs
        assert call_kwargs["basic_auth"] == ("user@redhat.com", "fake-token")
        assert "token_auth" not in call_kwargs

    @patch("src.objects.jira_base.JIRA")
    def test_uses_token_auth_when_email_not_configured(self, mock_jira_class, server_config):
        Jira(jira_config_path=server_config.as_posix())

        call_kwargs = mock_jira_class.call_args.kwargs
        assert call_kwargs["token_auth"] == "fake-token"
        assert "basic_auth" not in call_kwargs

    @patch("src.objects.jira_base.JIRA")
    def test_sets_rest_api_version_3(self, mock_jira_class, cloud_config):
        Jira(jira_config_path=cloud_config.as_posix())

        call_kwargs = mock_jira_class.call_args.kwargs
        assert call_kwargs["options"] == {"rest_api_version": "3"}
