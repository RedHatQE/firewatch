from jira import Issue


def test_get_issue_by_id_returns_jira_issue_from_jira_api_client_with_matching_issue_id(
    patch_jira_api_requests,
    jira,
    fake_issue_id,
):
    issue = jira.get_issue_by_id_or_key(issue=fake_issue_id)
    assert isinstance(issue, Issue)
    assert issue.id == fake_issue_id
