from src.objects.job import Job
from src.report.report import Report
from tests.unittests.functions.report.report_base_test import ReportBaseTest


class TestReport(ReportBaseTest):
    def test_report_initialization_with_job_rehearsal(self):
        job = Job("rehearse-1234-job1", "job1_safe", "123", "bucket1", self.config)
        with self.assertRaises(SystemExit) as rc:
            Report(self.config, job)
        error = rc.exception
        self.assertEqual(error.code, 0)

    def test_report_initialization_with_job_rehearsal_flag_false_test_failures(self):
        job = Job("rehearse-1234-job1", "job1_safe", "123", "bucket1", self.config)
        job.has_test_failures = True
        with self.assertRaises(SystemExit) as rc:
            Report(self.config, job)
        error = rc.exception
        self.assertEqual(error.code, 0)

    def test_report_initialization_with_job_rehearsal_flag_true_no_failures(self):
        self.config.fail_with_test_failures = True
        job = Job("rehearse-1234-job1", "job1_safe", "123", "bucket1", self.config)
        with self.assertRaises(SystemExit) as rc:
            Report(self.config, job)
        error = rc.exception
        self.assertEqual(error.code, 0)

    def test_report_initialization_with_job_rehearsal_flag_true_test_failures(self):
        self.config.fail_with_test_failures = True
        job = Job("rehearse-1234-job1", "job1_safe", "123", "bucket1", self.config)
        job.has_test_failures = True
        with self.assertRaises(SystemExit) as rc:
            Report(self.config, job)
        error = rc.exception
        self.assertEqual(error.code, 1)

    def test_report_initialization_fail_with_pod_failures_true(self):
        self.config.fail_with_pod_failures = True
        job = Job("rehearse-1234-job1", "job1_safe", "123", "bucket1", self.config)
        job.has_pod_failures = True
        with self.assertRaises(SystemExit) as rc:
            Report(self.config, job)
        error = rc.exception
        self.assertEqual(error.code, 1)
