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
from jira import Issue


def test_get_issue_by_id_returns_jira_issue_from_jira_api_client_with_matching_issue_id(
    patch_jira_api_requests,
    jira,
    fake_issue_id,
):
    issue = jira.get_issue_by_id_or_key(issue_id_or_key=fake_issue_id)
    assert isinstance(issue, Issue)
    assert issue.id == fake_issue_id
