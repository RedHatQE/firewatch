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


def test_add_labels_to_issue_with_no_existing_labels(
    patch_jira_api_requests,
    jira,
    fake_issue_id,
):
    label_to_add = "fake_label_987"
    issue = jira.get_issue_by_id_or_key(issue_id_or_key=fake_issue_id)
    assert not issue.fields.labels
    issue = jira.add_labels_to_issue(
        issue_id_or_key=fake_issue_id,
        labels=[label_to_add],
    )
    assert label_to_add in issue.fields.labels


def test_add_labels_to_issue_with_existing_labels_does_not_remove_existing_labels(
    patch_jira_api_requests,
    fake_issue_with_labels_json,
    jira,
    fake_issue_id,
):
    label_to_add = "fake_label_987"
    issue = jira.get_issue_by_id_or_key(issue_id_or_key=fake_issue_id)
    existing_labels = issue.fields.labels
    assert len(existing_labels)
    issue = jira.add_labels_to_issue(
        issue_id_or_key=fake_issue_id,
        labels=[label_to_add],
    )
    assert label_to_add in issue.fields.labels
    for label in existing_labels:
        assert label in issue.fields.labels
