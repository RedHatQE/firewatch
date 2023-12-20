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
from cli.objects.failure import Failure
from cli.report import Report
from tests.unittests.functions.report.report_base_test import ReportBaseTest


class TestFileJiraIssues(ReportBaseTest):
    def test_file_jira_issues_with_no_failures(self):
        report = Report(self.config, self.job)
        result = report.file_jira_issues([], self.config, self.job)
        self.assertEqual(result, [])

    def test_file_jira_issues_with_failures(self):
        failures = [Failure(failed_step="step1", failure_type="pod_failure")]

        report = Report(self.config, self.job)
        result = report.file_jira_issues(failures, self.config, self.job)
        self.assertNotEqual(result, [])
