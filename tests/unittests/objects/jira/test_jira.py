import json

import pytest
import pyhelper_utils.general as pyhelper_general
from jira import Issue
from jira.exceptions import JIRAError
from unittest.mock import MagicMock, patch

from src.objects.jira_base import LOGGER, Jira
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


def _mock_error_response(status_code: int, text: str, url: str = "https://example/rest/api/3/issue/1"):
    resp = MagicMock()
    resp.ok = False
    resp.status_code = status_code
    resp.text = text
    resp.url = url
    return resp


@pytest.fixture
def mock_jira(monkeypatch):
    monkeypatch.setattr(Jira, "__init__", lambda self, jira_config_path=None: None)
    jira = Jira()
    jira.url = DEFAULT_JIRA_SERVER_URL
    jira.connection = MagicMock()
    jira.connection._session = MagicMock()

    post_response = MagicMock()
    post_response.ok = True
    post_response.json.return_value = {"key": "TEST-1", "id": "10001"}
    jira.connection._session.post.return_value = post_response

    created_issue = MagicMock()
    created_issue.key = "TEST-1"
    jira.connection.issue.return_value = created_issue

    return jira


class TestJiraApiRespondsWithSuccess:
    def test_get_issue_by_id_returns_jira_issue_from_jira_api_client_with_matching_issue_id(self, fake_issue_id, jira):
        issue = jira.get_issue_by_id_or_key(issue=fake_issue_id)
        assert isinstance(issue, Issue)
        assert issue.id == fake_issue_id

    def test_add_labels_to_issue_sends_content_type_json_for_cloud_compatibility(
        self, fake_issue_id, jira, patch_jira_api_requests
    ):
        """Adding labels uses PUT with Content-Type: application/json to avoid 415 from Jira Cloud."""
        labels = ["retrigger", "firewatch"]
        expected = {"update": {"labels": [{"add": "retrigger"}, {"add": "firewatch"}]}}
        issue, applied = jira.add_labels_to_issue(issue_id_or_key=fake_issue_id, labels=labels)
        assert issue is not None
        assert applied is True
        assert len(patch_jira_api_requests["put"]) == 1
        _url, (data, args, kwargs) = next(iter(patch_jira_api_requests["put"].items()))
        assert kwargs.get("headers", {}).get("Content-Type") == "application/json"
        assert kwargs.get("json") == expected
        assert data is None
        payload = kwargs["json"]
        assert "fields" not in payload
        assert payload == expected

    def test_remove_labels_from_issue_sends_content_type_json_for_cloud_compatibility(
        self, fake_issue_id, jira, patch_jira_api_requests
    ):
        labels = ["job_passed_since_ticket_created"]
        expected = {"update": {"labels": [{"remove": "job_passed_since_ticket_created"}]}}
        issue, applied = jira.remove_labels_from_issue(issue_id_or_key=fake_issue_id, labels=labels)
        assert issue is not None
        assert applied is True
        assert len(patch_jira_api_requests["put"]) == 1
        _url, (data, args, kwargs) = next(iter(patch_jira_api_requests["put"].items()))
        assert kwargs.get("headers", {}).get("Content-Type") == "application/json"
        assert kwargs.get("json") == expected
        assert data is None

    def test_create_issue_sends_content_type_json_for_cloud_compatibility(self, jira, patch_jira_api_requests):
        jira.create_issue(
            project="TEST",
            summary="S",
            description="D",
            issue_type="Bug",
        )
        create_urls = [u for u in patch_jira_api_requests["post"] if u.endswith("/rest/api/3/issue")]
        assert len(create_urls) == 1
        _args, kwargs = patch_jira_api_requests["post"][create_urls[0]]
        assert kwargs.get("headers", {}).get("Content-Type") == "application/json"
        payload = kwargs.get("json") or {}
        assert "fields" in payload
        fields = payload["fields"]
        assert fields["project"] == {"key": "TEST"}
        assert fields["summary"] == "S"
        assert fields["issuetype"] == {"name": "Bug"}
        assert fields["description"] == _minimal_adf_doc("D")


class TestJiraCreateIssueHttpError:
    def test_create_issue_raises_jira_error_when_post_returns_non_ok(self, jira, monkeypatch):
        monkeypatch.setattr(pyhelper_general, "sleep", lambda _: None)
        err_text = '{"detail":"Method \'GET\' is not supported."}'
        resp = _mock_error_response(405, err_text, url="https://example/rest/api/3/issue")

        with patch.object(jira.connection._session, "post", return_value=resp):
            with pytest.raises(JIRAError) as exc_info:
                jira.create_issue(
                    project="TEST",
                    summary="S",
                    description="D",
                    issue_type="Bug",
                )

        assert exc_info.value.text == err_text
        assert exc_info.value.status_code == 405
        assert exc_info.value.url == resp.url


class TestJiraAddLabelsHttpError:
    @pytest.mark.parametrize(
        "status_code,err_text",
        [
            (400, "Field 'labels' cannot be set. It is not on the appropriate screen, or unknown."),
            (403, "You do not have permission to edit this issue."),
        ],
    )
    def test_add_labels_to_issue_returns_false_on_recoverable_http_error(
        self,
        fake_issue_id,
        jira,
        caplog,
        status_code,
        err_text,
    ):
        resp = _mock_error_response(status_code, err_text)
        with patch.object(jira.connection._session, "put", return_value=resp):
            issue, applied = jira.add_labels_to_issue(issue_id_or_key=fake_issue_id, labels=["x"])
        assert applied is False
        assert issue.id == fake_issue_id
        assert "Failed to add labels" in caplog.text
        assert "project configuration, missing permissions, or the Jira user" in caplog.text


class TestJiraRemoveLabelsHttpError:
    @pytest.mark.parametrize(
        "status_code,err_text",
        [
            (400, "Field 'labels' cannot be set. It is not on the appropriate screen, or unknown."),
            (403, "You do not have permission to edit this issue."),
        ],
    )
    def test_remove_labels_from_issue_returns_false_on_recoverable_http_error(
        self,
        fake_issue_id,
        jira,
        caplog,
        status_code,
        err_text,
    ):
        resp = _mock_error_response(status_code, err_text)
        with patch.object(jira.connection._session, "put", return_value=resp):
            issue, applied = jira.remove_labels_from_issue(issue_id_or_key=fake_issue_id, labels=["x"])
        assert applied is False
        assert issue.id == fake_issue_id
        assert "Failed to remove labels" in caplog.text
        assert "project configuration, missing permissions, or the Jira user" in caplog.text


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


def _minimal_adf_doc(plain_text: str) -> dict:
    return {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "paragraph",
                "content": [{"type": "text", "text": plain_text}],
            }
        ],
    }


class TestCreateIssueAdfDescription:
    def test_create_issue_passes_adf_description_for_jira_cloud_rest_v3(self, mock_jira):
        plain = "Line one\nLine two"
        mock_jira.create_issue(
            project="TEST",
            summary="Summary",
            description=plain,
            issue_type="Bug",
        )
        mock_jira.connection._session.post.assert_called_once()
        call_kwargs = mock_jira.connection._session.post.call_args.kwargs
        assert call_kwargs["headers"]["Content-Type"] == "application/json"
        fields = call_kwargs["json"]["fields"]
        assert fields["description"] == _minimal_adf_doc(plain)

    def test_create_issue_sanitizes_empty_description_text_node(self, mock_jira):
        mock_jira.create_issue(
            project="TEST",
            summary="Summary",
            description="",
            issue_type="Bug",
        )
        call_kwargs = mock_jira.connection._session.post.call_args.kwargs
        fields = call_kwargs["json"]["fields"]
        assert fields["description"]["content"][0]["content"][0]["text"] == " "

    def test_create_issue_accepts_adf_dict_directly(self, mock_jira):
        from src.objects.jira_adf import adf_doc, paragraph, inline_text

        adf = adf_doc(
            paragraph(inline_text("hello", bold=True)),
        )
        mock_jira.create_issue(
            project="TEST",
            summary="Summary",
            description=adf,
            issue_type="Bug",
        )
        call_kwargs = mock_jira.connection._session.post.call_args.kwargs
        fields = call_kwargs["json"]["fields"]
        desc = fields["description"]
        assert desc["type"] == "doc"
        assert desc["version"] == 1
        assert desc["content"][0]["type"] == "paragraph"
        assert desc["content"][0]["content"][0]["text"] == "hello"
        assert {"type": "strong"} in desc["content"][0]["content"][0]["marks"]


class TestCreateIssueEpicSearch:
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


def _post_request_json(kwargs: dict) -> dict:
    raw = kwargs.get("data")
    if raw is None:
        return kwargs.get("json") or {}
    if isinstance(raw, (bytes, bytearray)):
        raw = raw.decode()
    return json.loads(raw) if isinstance(raw, str) else raw


def _assert_adf_doc(value: object) -> None:
    assert isinstance(value, dict), f"expected ADF doc dict, got {type(value).__name__}"
    assert value.get("type") == "doc"
    assert value.get("version") == 1


class TestJiraCommentPostAdfPayload:
    def test_comment_post_json_uses_adf_doc_body_not_string(self, patch_jira_api_requests, fake_issue_key, jira):
        text = "hello from test"
        jira.comment(fake_issue_key, text)
        comment_urls = [u for u in patch_jira_api_requests["post"] if u.endswith("/comment")]
        assert len(comment_urls) == 1
        _args, kwargs = patch_jira_api_requests["post"][comment_urls[0]]
        payload = _post_request_json(kwargs)
        assert "body" in payload
        assert not isinstance(payload["body"], str), (
            "Jira Cloud REST v3 expects comment body as ADF, not a plain string"
        )
        _assert_adf_doc(payload["body"])
        assert payload["body"]["content"][0]["content"][0]["text"] == text

    def test_comment_post_sanitizes_empty_text_in_adf_dict(self, patch_jira_api_requests, fake_issue_key, jira):
        raw = {
            "type": "doc",
            "version": 1,
            "content": [
                {"type": "paragraph", "content": [{"type": "text", "text": ""}]},
            ],
        }
        jira.comment(fake_issue_key, raw)
        comment_urls = [u for u in patch_jira_api_requests["post"] if u.endswith("/comment")]
        assert len(comment_urls) == 1
        _args, kwargs = patch_jira_api_requests["post"][comment_urls[0]]
        payload = _post_request_json(kwargs)
        assert payload["body"]["content"][0]["content"][0]["text"] == " "


class TestResolveAccountId:
    def test_resolve_account_id_found(self, mock_jira):
        fake_user = MagicMock()
        fake_user.accountId = "abc-123"
        mock_jira.connection.search_users.return_value = [fake_user]

        result = mock_jira._resolve_account_id("user@example.com")
        assert result == "abc-123"
        mock_jira.connection.search_users.assert_called_once_with(query="user@example.com", maxResults=1)

    def test_resolve_account_id_not_found(self, mock_jira, caplog):
        mock_jira.logger = LOGGER
        mock_jira.connection.search_users.return_value = []

        result = mock_jira._resolve_account_id("nobody@example.com")
        assert result is None

    def test_resolve_account_id_jira_error(self, mock_jira, caplog):
        mock_jira.logger = LOGGER
        mock_jira.connection.search_users.side_effect = JIRAError("fail")

        result = mock_jira._resolve_account_id("error@example.com")
        assert result is None


class TestAddWatchersToIssue:
    def test_add_watchers_happy_path(self, mock_jira):
        mock_jira.logger = LOGGER
        user1 = MagicMock()
        user1.accountId = "id-1"
        user2 = MagicMock()
        user2.accountId = "id-2"
        mock_jira.connection.search_users.side_effect = [[user1], [user2]]

        mock_jira.add_watchers_to_issue("TEST-1", ["a@b.com", "c@d.com"])

        assert mock_jira.connection.add_watcher.call_count == 2
        mock_jira.connection.add_watcher.assert_any_call("TEST-1", "id-1")
        mock_jira.connection.add_watcher.assert_any_call("TEST-1", "id-2")

    def test_add_watchers_partial_failure(self, mock_jira):
        mock_jira.logger = LOGGER
        user1 = MagicMock()
        user1.accountId = "id-1"
        mock_jira.connection.search_users.side_effect = [[user1], []]

        mock_jira.add_watchers_to_issue("TEST-1", ["a@b.com", "nobody@b.com"])

        assert mock_jira.connection.add_watcher.call_count == 1
        mock_jira.connection.add_watcher.assert_called_once_with("TEST-1", "id-1")


class TestSetAdditionalAssignees:
    def test_set_additional_assignees_happy_path(self, mock_jira):
        mock_jira.logger = LOGGER
        user1 = MagicMock()
        user1.accountId = "id-1"
        user2 = MagicMock()
        user2.accountId = "id-2"
        mock_jira.connection.search_users.side_effect = [[user1], [user2]]

        issue = MagicMock()
        issue.self = f"{DEFAULT_JIRA_SERVER_URL}/rest/api/3/issue/10001"
        mock_jira.get_issue_by_id_or_key = MagicMock(return_value=issue)

        put_response = MagicMock()
        put_response.ok = True
        mock_jira.connection._session.put.return_value = put_response

        mock_jira._set_additional_assignees("TEST-1", ["a@b.com", "c@d.com"])

        mock_jira.connection._session.put.assert_called_once()
        call_kwargs = mock_jira.connection._session.put.call_args.kwargs
        payload = call_kwargs.get("json") or {}
        expected_users = [{"accountId": "id-1"}, {"accountId": "id-2"}]
        assert payload["fields"]["customfield_10465"] == expected_users

    def test_set_additional_assignees_skip_unresolved(self, mock_jira):
        mock_jira.logger = LOGGER
        user1 = MagicMock()
        user1.accountId = "id-1"
        mock_jira.connection.search_users.side_effect = [[user1], []]

        issue = MagicMock()
        issue.self = f"{DEFAULT_JIRA_SERVER_URL}/rest/api/3/issue/10001"
        mock_jira.get_issue_by_id_or_key = MagicMock(return_value=issue)

        put_response = MagicMock()
        put_response.ok = True
        mock_jira.connection._session.put.return_value = put_response

        mock_jira._set_additional_assignees("TEST-1", ["a@b.com", "nobody@b.com"])

        call_kwargs = mock_jira.connection._session.put.call_args.kwargs
        payload = call_kwargs.get("json") or {}
        assert payload["fields"]["customfield_10465"] == [{"accountId": "id-1"}]


class TestCreateIssueWatchersAndAssigneesWiring:
    def test_create_issue_calls_add_watchers_when_provided(self, mock_jira):
        mock_jira.logger = LOGGER
        mock_jira.add_watchers_to_issue = MagicMock()

        mock_jira.create_issue(
            project="TEST",
            summary="S",
            description="D",
            issue_type="Bug",
            watchers=["a@b.com"],
        )

        mock_jira.add_watchers_to_issue.assert_called_once_with(
            issue_key="TEST-1",
            watcher_emails=["a@b.com"],
        )

    def test_create_issue_calls_set_additional_assignees_when_provided(self, mock_jira):
        mock_jira.logger = LOGGER
        mock_jira._set_additional_assignees = MagicMock()

        mock_jira.create_issue(
            project="TEST",
            summary="S",
            description="D",
            issue_type="Bug",
            additional_assignees=["c@d.com"],
        )

        mock_jira._set_additional_assignees.assert_called_once_with(
            issue_key="TEST-1",
            assignee_emails=["c@d.com"],
        )

    def test_create_issue_skips_watchers_when_none(self, mock_jira):
        mock_jira.logger = LOGGER
        mock_jira.add_watchers_to_issue = MagicMock()
        mock_jira._set_additional_assignees = MagicMock()

        mock_jira.create_issue(
            project="TEST",
            summary="S",
            description="D",
            issue_type="Bug",
        )

        mock_jira.add_watchers_to_issue.assert_not_called()
        mock_jira._set_additional_assignees.assert_not_called()
