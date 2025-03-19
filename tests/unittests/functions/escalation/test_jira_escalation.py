import pytest

from unittest.mock import MagicMock, patch
from src.escalation.jira_escalation import Jira_Escalation
from datetime import datetime, timedelta, timezone

from simple_logger.logger import get_logger


LOGGER = get_logger(name=__name__)


@pytest.fixture
def fake_current_date():
    fake_time = datetime(2025, 4, 25, tzinfo=timezone.utc)

    patcher = patch("src.escalation.jira_escalation.datetime")
    mock_datetime = patcher.start()
    mock_datetime.now.return_value = fake_time
    mock_datetime.strptime = datetime.strptime
    mock_datetime.timedelta = timedelta
    mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
    yield fake_time
    patcher.stop()


@pytest.fixture
def setup_jira_escalation(fake_current_date):
    """fixture to setup jira escalation instance"""
    mock_jira_client = MagicMock()
    mock_slack_client = MagicMock()

    jira_escalation = Jira_Escalation(
        jira=mock_jira_client,
        slack_client=mock_slack_client,
        slack_channel="test-channel",
        default_labels=["test-lp"],
        additional_labels=["test-labbel-a", "test-label-b"],
        default_jira_project="test-project",
        team_slack_handle="team-user-group",
        mpiit_escalation_contact="test-email-1@exmaple.com",
        watcher_email="watcher@example.com",
    )
    jira_escalation.send_slack_notification = MagicMock()
    return jira_escalation, mock_jira_client, mock_slack_client


def create_mock_issue(
    fake_current_date,
    key="JIRA-123",
    assignee_email="jira_user@example.com",
    updated_days_ago=5,
    comment_days_ago=None,
    status_change_days_ago=None,
):
    """Helper to create mock jira issue"""

    fake_jira_issue = MagicMock()
    fake_jira_issue.key = key

    if assignee_email:
        assignee = MagicMock()
        assignee.name = assignee_email.split("@")[0]
        assignee.emailAddress = assignee_email
        fake_jira_issue.fields.assignee = assignee
    else:
        fake_jira_issue.fields.assignee = None

    fake_jira_issue.fields.updated = (fake_current_date - timedelta(days=updated_days_ago)).strftime(
        "%Y-%m-%dT%H:%M:%S.%f%z"
    )

    fake_jira_issue.fields.description = (
        "Prow Job link : [periodic-ci-test-job-openshift-fips|https://prow.ci.openshift.org/view/gs/some-log-path ]"
    )

    comments_obj = MagicMock()
    mock_comment = []
    if comment_days_ago is not None:
        comment = MagicMock()
        comment.author.emailAddress = assignee_email
        comment.updated = (fake_current_date - timedelta(days=comment_days_ago)).strftime("%Y-%m-%dT%H:%M:%S.%f%z")
        mock_comment.append(comment)
    comments_obj.comments = mock_comment
    fake_jira_issue.fields.comment = comments_obj

    mock_changelog = MagicMock()
    if status_change_days_ago is not None:
        history = MagicMock()
        history.created = (fake_current_date - timedelta(days=status_change_days_ago)).strftime(
            "%Y-%m-%dT%H:%M:%S.%f%z"
        )
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


@pytest.mark.parametrize(
    "assignee_email, comment_days_ago, status_changed_days_ago, expect_cc_user, expect_add_jira_comment",
    [
        (None, None, None, False, False),
        ("user@example.com", 5, None, True, False),
        ("user@example.com", 3, None, False, False),
        ("user@example.com", 2, None, False, True),
        ("user@example.com", None, 5, True, False),
    ],
)
def test_process_issues(
    fake_current_date,
    setup_jira_escalation,
    assignee_email,
    comment_days_ago,
    status_changed_days_ago,
    expect_cc_user,
    expect_add_jira_comment,
):
    fake_jira_issue = create_mock_issue(
        fake_current_date=fake_current_date,
        assignee_email=assignee_email,
        comment_days_ago=comment_days_ago,
        status_change_days_ago=status_changed_days_ago,
    )
    escalation, mock_jira, _ = setup_jira_escalation

    mock_jira.search_issues.return_value = [MagicMock(key="JIRA-123")]
    mock_jira.get_issue_by_id_or_key_with_changelog.return_value = fake_jira_issue
    escalation.process_issues(jira_query="project = test-project")

    if assignee_email is None:
        escalation.send_slack_notification.assert_called_once()
        args, kwargs = escalation.send_slack_notification.call_args
        assert "No assignee" in kwargs["message"]

    elif expect_cc_user:
        escalation.send_slack_notification.assert_called_once()
        args, kwargs = escalation.send_slack_notification.call_args
        assert "test-email-1@exmaple.com" in kwargs["cc_user_email"]

    elif expect_add_jira_comment:
        mock_jira.comment.assert_called_once()
        args, kwargs = mock_jira.comment.call_args
        assert "user" in args[1]

    else:
        escalation.send_slack_notification.assert_called_once()
        args, kwargs = escalation.send_slack_notification.call_args
        assert "cc_user_email" not in kwargs or kwargs.get("cc_user_email")


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
