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
from tests.unittests.objects.job.job_base_test import JobBaseTest


class TestJob(JobBaseTest):
    def test_initialization_with_valid_parameters(self):
        job = Job("job1", "job1_safe", "123", "bucket1", self.config)
        self.assertEqual(job.name, "job1")
        self.assertEqual(job.name_safe, "job1_safe")
        self.assertEqual(job.build_id, "123")
        self.assertEqual(job.gcs_bucket, "bucket1")
