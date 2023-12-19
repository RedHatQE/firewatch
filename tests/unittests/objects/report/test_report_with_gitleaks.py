#
# Copyright (C) 2023 Red Hat, Inc.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
from pathlib import Path

import pytest
from simple_logger.logger import get_logger

from cli.objects.gitleaks_detection import GitleaksDetectionsFailureRule
from cli.objects.gitleaks_detection import GitleaksDetectionsJobFailure
from cli.report.report import Report

_logger = get_logger(
    __name__,
)


@pytest.fixture(autouse=True)
def setup_test_environment(
    assert_jira_token_in_env,
    assert_jira_config_file_exists,
    assert_default_jira_project_in_env,
    assert_firewatch_config_in_env,
    patch_job_junit_dir,
    patch_job_log_dir,
    patch_jira,
    assert_build_id_in_env,
    assert_artifact_dir_exists,
    assert_artifact_dir_in_env,
    patch_gitleaks_config_job_dir,
    assert_job_dir_exists,
    assert_job_log_artifacts_exist,
    assert_job_junit_artifacts_exist,
    assert_patterns_server_token_file_exists,
    patch_gitleaks_config_patterns_server_token_path,
):
    ...


def test_init_report_object_with_gitleaks_enabled(
    firewatch_config,
    job,
) -> None:
    res = Report(firewatch_config=firewatch_config, job=job, gitleaks=True)
    assert isinstance(res, Report)


def test_find_zero_detections_in_report_with_no_gitleaks_report_file(
    report_with_gitleaks_no_leaks,
):
    report_with_gitleaks_no_leaks.gitleaks_config.gitleaks_report_path.unlink(
        missing_ok=True,
    )
    failures = report_with_gitleaks_no_leaks._find_gitleaks_detections()
    assert not failures


def test_find_at_least_two_detections_from_gitleaks_report_with_two_injected_leaks(
    report_with_gitleaks_with_leaks,
):
    detections = report_with_gitleaks_with_leaks._find_gitleaks_detections()
    assert len(detections) >= 2


def test_report_with_gitleaks_detection_has_job_with_gitleaks_detections_failure(
    report_with_gitleaks_with_leaks,
):
    last_failure = report_with_gitleaks_with_leaks._job.failures.pop()
    assert isinstance(last_failure, GitleaksDetectionsJobFailure)


def test_report_with_gitleaks_with_no_detections_has_no_bugs_filed(
    report_with_gitleaks_no_leaks,
):
    assert len(report_with_gitleaks_no_leaks._bugs_filed) is 0


def test_report_with_gitleaks_detections_has_either_bugs_filed_or_duplicate_bugs_found(
    report_with_gitleaks_with_leaks,
):
    bugs_filed = report_with_gitleaks_with_leaks._bugs_filed
    duplicate_bugs = report_with_gitleaks_with_leaks._duplicate_bugs_commented
    assert bugs_filed or duplicate_bugs


def test_report_with_gitleaks_detections_matches_gitleaks_failure_to_gitleaks_rule(
    report_with_gitleaks_with_leaks,
):
    detections = report_with_gitleaks_with_leaks._find_gitleaks_detections()
    rule = detections.to_failure_rule()
    failure = detections.to_job_failure()
    matches = report_with_gitleaks_with_leaks.failure_matches_rule(
        failure=failure,
        rules=[rule],
        default_jira_project="TEST",
    )
    assert len(matches)
    assert any(isinstance(m, GitleaksDetectionsFailureRule) for m in matches)


def test_report_with_gitleaks_detections_has_expected_rule_failure_pair(
    report_with_gitleaks_with_leaks,
):
    (
        rule,
        failure,
    ) = report_with_gitleaks_with_leaks._rule_failure_pairs.pop().values()
    assert isinstance(rule, GitleaksDetectionsFailureRule)
    assert isinstance(failure, GitleaksDetectionsJobFailure)


def test_report_with_gitleaks_detections_found_has_gitleaks_report_and_attachments_for_each_unique_file_in_report(
    report_with_gitleaks_with_leaks,
):
    report = report_with_gitleaks_with_leaks
    (
        rule,
        failure,
    ) = report._rule_failure_pairs.pop().values()
    gitleaks_failure_file_attachments = report._get_file_attachments(
        step_name=failure.step,
        logs_dir=report._job.logs_dir,
        junit_dir=report._job.junit_dir,
        is_gitleaks_failure=True,
    )
    attachment_paths = {Path(p) for p in gitleaks_failure_file_attachments}
    assert len(attachment_paths)
    unique_file_names_in_gitleaks_report = {f.file for f in report._gitleaks_detections}
    assert report.gitleaks_config.gitleaks_report_path in attachment_paths
    exp = len(unique_file_names_in_gitleaks_report) + 1
    assert exp == len(gitleaks_failure_file_attachments)


def test_report_with_gitleaks_detections_found_creates_jira_issue_with_security_level_red_hat_employee(
    cap_jira,
    force_report_has_no_duplicates,
    report_with_gitleaks_with_leaks,
):
    kw = cap_jira.create_jira_issue.pop().kwargs
    assert "security_level" in kw.keys()
    assert kw["security_level"] == "Red Hat Employee"
