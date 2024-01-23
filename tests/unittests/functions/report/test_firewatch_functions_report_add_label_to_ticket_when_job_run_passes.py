import pytest
import simple_logger.logger
from jira import Issue

from cli.report import Report
from cli.report.report import JOB_PASSED_SINCE_TICKET_CREATED_LABEL

_logger = simple_logger.logger.get_logger(__name__)


@pytest.fixture
def job(patch_job_junit_dir, patch_job_log_dir, default_jira_project, job):
    yield job


@pytest.fixture
def firewatch_config(firewatch_config_json, default_jira_project, firewatch_config):
    yield firewatch_config


@pytest.fixture
def report(firewatch_config, job):
    yield Report(firewatch_config=firewatch_config, job=job)


@pytest.fixture
def fake_job_has_open_bugs(monkeypatch, fake_issue_key):
    def _get_open_bugs(*args, **kwargs):
        _logger.info("Patching Report._get_open_bugs")
        return [fake_issue_key]

    monkeypatch.setattr(Report, "_get_open_bugs", _get_open_bugs)


def test_fixtures_fake_jira_issue_exists(
    patch_jira_api_requests,
    jira,
    fake_issue_id,
    fake_issue_key,
):
    issue = jira.get_issue_by_id_or_key(fake_issue_id)
    assert isinstance(issue, Issue)
    assert issue.id == fake_issue_id
    assert issue.key == fake_issue_key


def test_fixtures_fake_job_has_open_bugs(
    patch_jira_api_requests,
    fake_job_has_open_bugs,
    report,
    job,
    jira,
    fake_issue_key,
):
    resp = report._get_open_bugs(job_name=job.name, jira=jira)
    assert resp
    assert fake_issue_key in resp


def test_report_adds_passing_label_to_newly_passing_job_with_open_bugs(
    patch_jira_api_requests,
    firewatch_config,
    job,
    fake_issue_key,
    fake_issue_id,
):
    Report(firewatch_config=firewatch_config, job=job)
    put_request_data_to_issue_endpoint = [
        v[0]
        for k, v in patch_jira_api_requests["put"].items()
        if k.endswith(f"/issue/{fake_issue_id}")
        or k.endswith(f"/issue/{fake_issue_key}")
    ]
    exp = '"fields": {"labels": ["' + JOB_PASSED_SINCE_TICKET_CREATED_LABEL + '"]}'
    assert any([exp in _ for _ in put_request_data_to_issue_endpoint])
