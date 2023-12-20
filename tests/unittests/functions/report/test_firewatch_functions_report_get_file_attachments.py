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
import os
import tempfile

from tests.unittests import helpers
from tests.unittests.functions.report.report_base_test import ReportBaseTest


class TestGetFileAttachments(ReportBaseTest):
    def test_get_file_attachments(self):
        with tempfile.TemporaryDirectory() as tmp_path:
            logs_dir = helpers._get_tmp_logs_dir(tmp_path=tmp_path)
            junit_dir = helpers._get_tmp_junit_dir(tmp_path=tmp_path)
            helpers._create_failed_step_junit(junit_dir=junit_dir)
            helpers._create_failed_step_pod(logs_dir=logs_dir)

            file_attachments = self.report._get_file_attachments(
                step_name="failed-step",
                logs_dir=logs_dir,
                junit_dir=junit_dir,
            )
            assert len(file_attachments) > 0
            for file in file_attachments:
                assert os.path.exists(file)
