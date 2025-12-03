import pytest

from unittest.mock import MagicMock, patch
from src.escalation.jira_escalation import Jira_Escalation
from datetime import datetime, timedelta, timezone

from simple_logger.logger import get_logger


LOGGER = get_logger(name=__name__)


FIXED_NOW = datetime(2025, 5, 1, tzinfo=timezone.utc)


@pytest.fixture
def fake_current_date():
    with patch("src.escalation.jira_escalation.datetime") as mock_datetime:
        mock_datetime.now.return_value = FIXED_NOW
        mock_datetime.strptime = datetime.strptime
        yield mock_datetime


@pytest.fixture
def escalation_setup():
    mock_jira = MagicMock()
    mock_slack = MagicMock()
    return mock_jira, mock_slack


@pytest.fixture
def setup_jira_escalation(escalation_setup, fake_current_date):
    """fixture to setup jira escalation instance"""
    mock_jira_client, mock_slack_client = escalation_setup

    jira_escalation = Jira_Escalation(
        jira=mock_jira_client,
        slack_client=mock_slack_client,
        slack_channel="test-channel",
        default_labels=["test-lp"],
        additional_labels=["test-labbel-a", "test-label-b"],
        default_jira_project="test-project",
        team_slack_handle="team-user-group",
        team_manager_email="test-email-1@exmaple.com",
        reporter_email="watcher@example.com",
        base_issue_url="https://issues.stage.test.com",
    )
    jira_escalation.send_slack_notification = MagicMock()
    return jira_escalation, mock_jira_client, mock_slack_client


def create_mock_issue(
    key: str,
    assignee_email: str = None,
    updated_days_ago: int = None,
    comment_days_ago: int = None,
    status_change_days_ago: int = None,
    now: datetime = FIXED_NOW,
):
    """Helper to create mock jira issue"""

    def days_ago(days) -> str:
        days = (now - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%S.%f%z")
        return days

    fake_jira_issue = MagicMock()
    fake_jira_issue.key = key
    fake_jira_issue.fields = MagicMock()

    # Generate a unique accountId based on email (simulates Jira Cloud behavior)
    assignee_account_id = f"accountId:{assignee_email}" if assignee_email else None

    # if assignee value is provided then update the mock field with actual value
    if assignee_email:
        assignee = MagicMock()
        assignee.name = assignee_email.split("@")[0]
        assignee.emailAddress = assignee_email
        assignee.accountId = assignee_account_id
        fake_jira_issue.fields.assignee = assignee
    else:
        fake_jira_issue.fields.assignee = None

    fake_jira_issue.fields.updated = days_ago(updated_days_ago)

    # Update the issue content with the tested job link
    fake_jira_issue.fields.description = (
        "Prow Job link : [periodic-ci-test-job-openshift-fips|https://prow.ci.openshift.org/view/gs/some-log-path ]"
    )

    # Decides whether issue comments will be set or empty
    comments_obj = MagicMock()
    mock_comment = []
    if comment_days_ago is not None:
        comment = MagicMock()
        comment.author.emailAddress = assignee_email
        comment.author.accountId = assignee_account_id
        comment.updated = days_ago(comment_days_ago)
        mock_comment.append(comment)
    comments_obj.comments = mock_comment
    fake_jira_issue.fields.comment = comments_obj

    # If issue supposed to be acknowledged by the assignee, update related fields
    mock_changelog = MagicMock()
    if status_change_days_ago is not None:
        history = MagicMock()
        history.created = days_ago(status_change_days_ago)
        item = MagicMock()
        item.field = "status"
        item.toString = "ACK"
        history.items = [item]
        mock_changelog.histories = [history]
    else:
        mock_changelog.histories = []
    fake_jira_issue.changelog = mock_changelog

    return fake_jira_issue


def test_add_labels_to_jira_query(setup_jira_escalation):
    escalation, _, _ = setup_jira_escalation
    jira_query = 'Project = test-project AND status in("ACK") '
    query = escalation.add_labels_to_jira_query(jira_query)
    expected_query = 'Project = test-project AND status in("ACK")  AND (labels IN("test-labbel-a","test-label-b")) AND (labels = "test-lp")'
    assert query == expected_query


class TestGetUserAccountId:
    """Tests for get_user_account_id static method."""

    def test_returns_account_id_when_present(self):
        user = MagicMock()
        user.accountId = "5b10ac8d82e05b22cc7d4ef5"  # pragma: allowlist secret
        assert Jira_Escalation.get_user_account_id(user) == "5b10ac8d82e05b22cc7d4ef5"  # pragma: allowlist secret

    def test_returns_none_when_user_is_none(self):
        assert Jira_Escalation.get_user_account_id(None) is None

    def test_returns_none_when_account_id_missing(self):
        user = MagicMock(spec=[])  # Empty spec means no attributes
        assert Jira_Escalation.get_user_account_id(user) is None


class TestGetUserEmail:
    """Tests for get_user_email static method."""

    def test_returns_email_when_present(self):
        user = MagicMock()
        user.emailAddress = "user@example.com"
        assert Jira_Escalation.get_user_email(user) == "user@example.com"

    def test_returns_none_when_user_is_none(self):
        assert Jira_Escalation.get_user_email(None) is None

    def test_returns_none_when_email_missing(self):
        user = MagicMock(spec=[])  # Empty spec means no attributes
        assert Jira_Escalation.get_user_email(user) is None

    def test_returns_none_when_email_is_none(self):
        """Jira Cloud may return None for emailAddress due to privacy settings."""
        user = MagicMock()
        user.emailAddress = None
        assert Jira_Escalation.get_user_email(user) is None


@pytest.mark.parametrize(
    "assignee_email, comment_days_ago, status_changed_days_ago, updated_days_ago, expect_cc_user, expect_add_jira_comment, expect_notify_assignee_in_slack",
    [
        ("user@example.com", None, None, 1, False, False, False),
        ("user@example.com", 5, None, 5, True, False, False),
        ("user@example.com", 5, 5, 5, True, False, False),
        ("user@example.com", 3, 3, 3, False, False, True),
        ("user@example.com", 3, None, 3, False, False, True),
        ("user@example.com", 3, None, 0, False, False, True),
        ("user@example.com", 2, None, 2, False, True, False),
        ("user@example.com", None, 5, 2, False, True, False),
        ("user@example.com", 3, 1, 5, False, False, True),
        ("user@example.com", 3, 5, 4, False, False, True),
        ("user@example.com", 1, 1, 1, False, False, False),
        (None, None, None, 1, False, False, False),
    ],
)
def test_process_issues(
    setup_jira_escalation,
    assignee_email,
    comment_days_ago,
    status_changed_days_ago,
    updated_days_ago,
    expect_cc_user,
    expect_add_jira_comment,
    expect_notify_assignee_in_slack,
):
    """
    Covers scenarios where assignee is present, and combination of when was the last time assignees
    commented, status was changed, or when was the jira issue updated.
    All jira issues will have `updated_days_ago` value, but that doesn't ensure if that update is due
    to assignee comment or status change. The `process_issues` functionality prioritizes the assignee's comment,
    followed by the status change and the last update date.
    """
    fake_jira_issue = create_mock_issue(
        key="Issue-1",
        assignee_email=assignee_email,
        comment_days_ago=comment_days_ago,
        status_change_days_ago=status_changed_days_ago,
        updated_days_ago=updated_days_ago,
    )
    escalation, mock_jira, _ = setup_jira_escalation

    mock_jira.search_issues.return_value = [MagicMock(key="Issue-1")]
    mock_jira.get_issue_by_id_or_key_with_changelog.return_value = fake_jira_issue
    escalation.process_issues(jira_query="project = test-project")

    if assignee_email is None:
        escalation.send_slack_notification.assert_not_called()

    if expect_cc_user:
        escalation.send_slack_notification.assert_called_once()
        args, kwargs = escalation.send_slack_notification.call_args
        assert "test-email-1@exmaple.com" in kwargs["cc_user_email"]

    elif expect_add_jira_comment:
        mock_jira.comment.assert_called_once()
        args, kwargs = mock_jira.comment.call_args
        # Comment should use accountId mention format for Jira Cloud compatibility
        assert "[~accountId:" in args[1]

    elif expect_notify_assignee_in_slack:
        escalation.send_slack_notification.assert_called_once()
        args, kwargs = escalation.send_slack_notification.call_args
        assert assignee_email in kwargs or kwargs.get("email")
        assert "cc_user_email" not in kwargs
    else:
        escalation.send_slack_notification.assert_not_called()


@pytest.mark.parametrize(
    "description, expected_job_name",
    [
        (
            "* Prow Job Link *: [periodic-ci-test-job-name #11234567|https://prow.ci.openshift.org/some/log/path]",
            "periodic-ci-test-job-name #11234567",
        ),
        ("Random description without job name", None),
    ],
)
def test_extract_job_name(description, expected_job_name, setup_jira_escalation):
    escalation_instance, _, _ = setup_jira_escalation

    job_name = escalation_instance.extract_prow_job_name(description)
    assert job_name == expected_job_name


@pytest.mark.parametrize(
    "description, expected_job_url",
    [
        (
            "* Prow Job Link *: [periodic-ci-test-job-name #11234567|https://prow.ci.openshift.org/some/log/path]",
            "https://prow.ci.openshift.org/some/log/path",
        ),
        ("Random description without job name", None),
    ],
)
def test_extract_prow_job_url(description, expected_job_url, setup_jira_escalation):
    escalation_instance, _, _ = setup_jira_escalation

    job_name = escalation_instance.extract_prow_job_link(description)
    assert job_name == expected_job_url


@pytest.mark.parametrize(
    "query1_issues, query2_issues,query3_issues, assignees, updated_days_ago, expected_keys, expect_notifcation",
    [
        (["ISSUE-1"], ["ISSUE-2"], ["ISSUE-3"], [None, None, None], 0, ["ISSUE-1", "ISSUE-2", "ISSUE-3"], True),
        (["ISSUE-1"], ["ISSUE-2"], ["ISSUE-3"], [None, None, None], 0, ["ISSUE-1", "ISSUE-2", "ISSUE-3"], True),
        (["ISSUE-1"], ["ISSUE-2"], [], [None, None], 2, ["ISSUE-1", "ISSUE-2"], True),
        (["ISSUE-1"], [], [], [None, None, None], 1, ["ISSUE-1"], True),
        ([], [], [], [], 5, [], False),
    ],
)
def test_issues_with_no_assignee(
    query1_issues,
    query2_issues,
    query3_issues,
    assignees,
    updated_days_ago,
    expected_keys,
    expect_notifcation,
    escalation_setup,
):
    mock_jira_client, mock_slack_client = escalation_setup

    all_keys = query1_issues + query2_issues + query3_issues
    issues_by_key = {}

    for key, assignee in zip(all_keys, assignees):
        issue = create_mock_issue(
            key=key,
            assignee_email=assignee if assignee else None,
            comment_days_ago=None,
            status_change_days_ago=None,
            updated_days_ago=updated_days_ago,
        )
        issues_by_key[key] = issue

    mock_jira_client.search_issues.side_effect = [
        [k for k in query1_issues],
        [k for k in query2_issues],
        [k for k in query3_issues],
    ]

    def get_issue_by_id_or_key_with_changelog(key, expand=None):
        return issues_by_key[key]

    mock_jira_client.get_issue_by_id_or_key_with_changelog.side_effect = get_issue_by_id_or_key_with_changelog

    # Validate message content, it must contain "No assignee", jira issue ids (`expected_keys`), and issue url for all the issues
    with patch.object(Jira_Escalation, "send_slack_notification") as mock_notify:
        Jira_Escalation(
            jira=mock_jira_client,
            slack_client=mock_slack_client,
            slack_channel="test-channel",
            default_labels=["test-lp"],
            additional_labels=["test-labbel-a", "test-label-b"],
            default_jira_project="test-project",
            team_slack_handle="team-user-group",
            team_manager_email="test-email-1@exmaple.com",
            reporter_email="watcher@example.com",
            base_issue_url="https://issues.stage.test.com",
        )

        if expect_notifcation:
            mock_notify.assert_called_once()
            args, kwargs = mock_notify.call_args
            message = args[1] if args else kwargs.get("", "message")

            assert "No assignee" in message
            for key in expected_keys:
                assert f"https://issues.stage.test.com/browse/{key}" in message
        else:
            mock_notify.send_slack_notification.assert_not_called()
