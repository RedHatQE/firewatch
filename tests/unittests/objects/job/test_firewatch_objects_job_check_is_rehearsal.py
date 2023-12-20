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


class TestCheckIsRehearsal(JobBaseTest):
    def test_rehearsal_job_true(self):
        job = Job("rehearse_job1", "job1_safe", "123", "bucket1", self.config)
        self.assertTrue(job.is_rehearsal)

    def test_rehearsal_job_false(self):
        job = Job("job1", "job1_safe", "123", "bucket1", self.config)
        self.assertFalse(job.is_rehearsal)
