import pytest
from jira import Issue


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

    def test_add_file_attachment_with_success_and_log(self, fake_issue, jira, fake_attachment_path, caplog):
        jira.add_attachment_to_issue(
            issue=fake_issue,
            attachment_path=fake_attachment_path.as_posix(),
        )
        assert f"Attachment {fake_attachment_path} has been uploaded to {fake_issue.key}" in caplog.text


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
