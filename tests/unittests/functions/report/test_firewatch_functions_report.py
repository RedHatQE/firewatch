from cli.objects.job import Job
from cli.report import Report
from tests.unittests.functions.report.report_base_test import ReportBaseTest


class TestReport(ReportBaseTest):
    def test_report_initialization_with_job_rehearsal(self):
        job = Job("rehearse_job1", "job1_safe", "123", "bucket1", self.config)
        with self.assertRaises(SystemExit):
            Report(self.config, job)
