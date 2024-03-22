from src.objects.failure import Failure
from src.report.report import Report
from tests.unittests.functions.report.report_base_test import ReportBaseTest


class TestFileJiraIssues(ReportBaseTest):
    def test_file_jira_issues_with_no_failures(self):
        report = Report(self.config, self.job)
        result, bugs_updated = report.file_jira_issues([], self.config, self.job)
        self.assertEqual(result, [])
        self.assertEqual(bugs_updated, [])

    def test_file_jira_issues_with_failures(self):
        failures = [Failure(failed_step="step1", failure_type="pod_failure")]

        report = Report(self.config, self.job)
        result, bugs_updated = report.file_jira_issues(failures, self.config, self.job)
        self.assertNotEqual(result, [])
        self.assertEqual(bugs_updated, [])
