from tests.unittests import helpers
from tests.unittests.functions.report.report_base_test import ReportBaseTest


class TestGetIssueLabels(ReportBaseTest):
    def test_get_issue_labels_no_additional_labels(self):
        labels = self.report._get_issue_labels(
            job_name=self.job.name,
            step_name="test-step-name",
            type="test_failure",
            jira_additional_labels=[],
        )

        assert len(labels) == 4
        assert self.job.name in labels
        assert "test-step-name" in labels
        assert "test_failure" in labels
        assert "firewatch" in labels

    def test_get_issue_labels_with_additional_labels(self):
        labels = self.report._get_issue_labels(
            job_name=self.job.name,
            step_name="test-step-name",
            type="test_failure",
            jira_additional_labels=["additional-label-1", "additional-label-2"],
        )

        assert len(labels) == 6
        assert self.job.name in labels
        assert "test-step-name" in labels
        assert "test_failure" in labels
        assert "firewatch" in labels
        assert "additional-label-1" and "additional-label-2" in labels

    def test_get_issue_labels_with_additional_labels_file(self):
        labels = self.report._get_issue_labels(
            job_name=self.job.name,
            step_name="test-step-name",
            type="test_failure",
            jira_additional_labels=[],
            jira_additional_labels_filepath=helpers._get_additional_labels_filepath(),
        )
        assert "test-1" and "test-1" in labels

    def test_get_issue_labels_with_failed_test_name(self):
        labels = self.report._get_issue_labels(
            job_name=self.job.name,
            step_name="test-step-name",
            type="test_failure",
            failed_test_name="test-name",
            jira_additional_labels=[],
        )

        assert len(labels) == 5
        assert self.job.name in labels
        assert "test-step-name" in labels
        assert "test_failure" in labels
        assert "firewatch" in labels
        assert "test-name" in labels

    def test_get_issue_labels_with_duplicate_labels(self):
        labels = self.report._get_issue_labels(
            job_name=self.job.name,
            step_name="test-step-name",
            type="test_failure",
            jira_additional_labels=["test-step-name", "test_failure"],
        )

        assert len(labels) == 4
        assert self.job.name in labels
        assert "test-step-name" in labels
        assert "test_failure" in labels
        assert "firewatch" in labels
