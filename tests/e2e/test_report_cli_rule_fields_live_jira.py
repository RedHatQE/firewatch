#
# Copyright (C) 2026 Red Hat, Inc.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
"""Live Jira e2e: ``report`` CLI + stubbed downloads + minimal pod failure layout.

Requires ``JIRA_TOKEN`` and ``JIRA_SERVER_URL`` (same as other e2e tests).
Uses unique synthetic ``job_name`` / ``build_id`` to limit duplicate matching noise.
Optional ``JIRA_EMAIL``: asserts watchers and additional assignees when set.
"""

import json
import os
import uuid

import pytest
import simple_logger.logger

from src.objects.jira_base import Jira
from src.objects.job import Job
from tests.e2e.test_add_jira_label_to_open_bugs_with_passing_job_run import (
    format_cli_result_for_debug,
    run_report_cli_command,
)

logger = simple_logger.logger.get_logger(__name__)

BAREBONES_STEP = "barebones-step"


@pytest.fixture
def build_id():
    yield f"e2e-rule-{uuid.uuid4().hex[:16]}"


@pytest.fixture
def job_name(build_id):
    yield f"periodic-ci-firewatch-e2e-barebones-{build_id}"


@pytest.fixture
def job_name_safe(build_id):
    yield f"firewatch-e2e-barebones-{build_id}"


@pytest.fixture
def firewatch_config_path(tmp_path, jira_email):
    path = tmp_path.joinpath("firewatch_config.json")
    rule: dict = {
        "step": BAREBONES_STEP,
        "failure_type": "pod_failure",
        "classification": "Firewatch e2e rule-derived Jira fields",
        "slack_channel": "#firewatch-e2e-stub",
        "slack_user": "firewatch-tool@redhat.com",
    }
    if jira_email:
        rule["jira_watchers"] = [jira_email]
        rule["jira_additional_assignees"] = [jira_email]
    path.write_text(json.dumps({"failure_rules": [rule]}))
    logger.info(f"wrote barebones firewatch config to {path.as_uri()}")
    yield path


@pytest.fixture
def report_cli_command_args(
    jira_config_path,
    firewatch_config_path,
    build_id,
    job_name,
    job_name_safe,
):
    yield (
        f"--build-id={build_id}",
        f"--job-name-safe={job_name_safe}",
        f"--job-name={job_name}",
        f"--jira-config-path={jira_config_path.as_posix()}",
        f"--firewatch-config-path={firewatch_config_path.as_posix()}",
    )


@pytest.fixture
def stub_pod_failure_layout(job_dir):
    job_dir.mkdir(parents=True, exist_ok=True)
    step_dir = job_dir / "logs" / BAREBONES_STEP
    step_dir.mkdir(parents=True)
    (step_dir / "finished.json").write_text('{"passed": false}')
    (job_dir / "artifacts").mkdir(parents=True)
    yield job_dir / "logs", job_dir / "artifacts"


def test_report_cli_applies_rule_fields_on_created_issue(
    monkeypatch,
    jira,
    register_jira_issues_for_e2e_cleanup,
    report_cli_command_args,
    stub_pod_failure_layout,
):
    keys_created: list[str] = []
    real_create_issue = Jira.create_issue

    def capture_create_issue(self, *args, **kwargs):
        issue = real_create_issue(self, *args, **kwargs)
        keys_created.append(issue.key)
        register_jira_issues_for_e2e_cleanup(issue.key)
        return issue

    monkeypatch.setattr(Jira, "create_issue", capture_create_issue)

    logs_dir, artifacts_dir = stub_pod_failure_layout
    monkeypatch.setattr(Job, "_get_steps", lambda *a, **k: [BAREBONES_STEP])
    monkeypatch.setattr(Job, "_download_logs", lambda *x, **y: logs_dir.as_posix())
    monkeypatch.setattr(Job, "_download_junit", lambda *x, **y: artifacts_dir.as_posix())

    result = run_report_cli_command(report_cli_command_args)
    assert result.exit_code == 0, format_cli_result_for_debug(result)

    assert keys_created, format_cli_result_for_debug(result)

    issue_key = keys_created[-1]
    issue = jira.get_issue_by_id_or_key(issue_key)
    labels = issue.fields.labels
    assert "slack-channel:firewatch-e2e-stub" in labels
    assert "slack-user:firewatch-tool" in labels

    email = os.getenv("JIRA_EMAIL")
    if email:
        watchers = jira.connection.watchers(issue_key)
        watcher_emails = [w.emailAddress for w in watchers.watchers]
        assert email in watcher_emails

        try:
            extra = issue.fields.customfield_10465
        except AttributeError:
            extra = None
        if extra:
            assignee_emails = [u.emailAddress for u in extra]
            assert email in assignee_emails
