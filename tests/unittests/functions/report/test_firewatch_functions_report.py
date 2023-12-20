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
from cli.objects.job import Job
from cli.report import Report
from tests.unittests.functions.report.report_base_test import ReportBaseTest


class TestReport(ReportBaseTest):
    def test_report_initialization_with_job_rehearsal(self):
        job = Job("rehearse_job1", "job1_safe", "123", "bucket1", self.config)
        with self.assertRaises(SystemExit):
            Report(self.config, job)
