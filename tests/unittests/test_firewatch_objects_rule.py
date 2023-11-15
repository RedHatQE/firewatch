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
from cli.objects.rule import Rule


class TestFirewatchObjectsRule:
    def test_rule(self) -> None:
        test_rule_dict = {
            "step": "test",
            "failure_type": "all",
            "classification": "test classification",
            "jira_project": "TEST",
            "jira_epic": "TEST-1234",
            "jira_component": ["test component"],
            "jira_affects_version": "test version",
            "jira_additional_labels": ["some-label-1", "some-label-2"],
            "jira_assignee": "some-email@redhat.com",
            "jira_priority": "blocker",
            "ignore": False,
        }

        rule = Rule(test_rule_dict)

        assert rule.step == test_rule_dict["step"]
        assert rule.failure_type == test_rule_dict["failure_type"]
        assert rule.classification == test_rule_dict["classification"]
        assert rule.jira_project == test_rule_dict["jira_project"]
        assert rule.jira_epic == test_rule_dict["jira_epic"]
        assert rule.jira_component == test_rule_dict["jira_component"]
        assert rule.jira_affects_version == test_rule_dict["jira_affects_version"]
        assert ("some-label-1" in rule.jira_additional_labels) and (
            "some-label-2" in rule.jira_additional_labels
        )
        assert rule.jira_assignee == "some-email@redhat.com"
        assert rule.jira_priority == "Blocker"
        assert not rule.ignore

    def test_get_step(self) -> None:
        test_rule_dict = {"step": "test-step-name"}
        step = Rule._get_step(self, test_rule_dict)
        assert step == "test-step-name"

    def test_get_failure_type(self) -> None:
        # Test value "all"
        test_rule_dict = {"failure_type": "all"}
        failure_type = Rule._get_failure_type(self, test_rule_dict)
        assert failure_type == "all"

        # Test value "pod_failure"
        test_rule_dict = {"failure_type": "pod_failure"}
        failure_type = Rule._get_failure_type(self, test_rule_dict)
        assert failure_type == "pod_failure"

        # Test value "test_failure"
        test_rule_dict = {"failure_type": "test_failure"}
        failure_type = Rule._get_failure_type(self, test_rule_dict)
        assert failure_type == "test_failure"

    def test_get_classification(self) -> None:
        test_rule_dict = {"classification": "Test classification"}
        classification = Rule._get_classification(self, test_rule_dict)
        assert classification == "Test classification"

    def test_get_jira_project(self) -> None:
        test_rule_dict = {"jira_project": "TEST"}
        jira_project = Rule._get_jira_project(self, test_rule_dict)
        assert jira_project == "TEST"

    def test_get_jira_epic(self) -> None:
        # Test when jira_epic is defined
        test_rule_dict = {"jira_epic": "TEST-1234"}
        jira_epic = Rule._get_jira_epic(self, test_rule_dict)
        assert jira_epic == "TEST-1234"

        # Test when jira_epic is not defined
        test_rule_dict = {"step": "test"}
        jira_epic = Rule._get_jira_epic(self, test_rule_dict)
        assert jira_epic is None

    def test_get_jira_component(self) -> None:
        test_rule_dict = {"jira_component": ["test component 1", "test component 2"]}
        jira_component = Rule._get_jira_component(self, test_rule_dict)
        assert isinstance(jira_component, list)
        assert ("test component 1" in jira_component) and (
            "test component 2" in jira_component
        )

        # Test when no components are defined
        test_rule_dict = {"step": "test"}
        jira_component = Rule._get_jira_component(self, test_rule_dict)
        assert jira_component is None

    def test_get_jira_affects_version(self) -> None:
        # Test when jira_affects_version is defined
        test_rule_dict = {"jira_affects_version": "test version"}
        jira_affects_version = Rule._get_jira_affects_version(self, test_rule_dict)
        assert jira_affects_version == "test version"

        # Test when jira_affects_version is not defined
        test_rule_dict = {"step": "test"}
        jira_affects_version = Rule._get_jira_affects_version(self, test_rule_dict)
        assert jira_affects_version is None

    def test_get_jira_additional_labels(self) -> None:
        # Test when jira_additional_labels is defined
        test_rule_dict = {"jira_additional_labels": ["some-label-1", "some-label-2"]}
        jira_additional_labels = Rule._get_jira_additional_labels(self, test_rule_dict)
        assert ("some-label-1" in jira_additional_labels) and (
            "some-label-2" in jira_additional_labels
        )

        # Test when jira_additional_labels is not defined
        test_rule_dict = {"step": "test"}
        jira_additional_labels = Rule._get_jira_additional_labels(self, test_rule_dict)
        assert jira_additional_labels is None

    def test_get_jira_assignee(self) -> None:
        # Test when jira_assignee is defined
        test_rule_dict = {"jira_assignee": "some-email@redhat.com"}
        jira_assignee = Rule._get_jira_assignee(self, test_rule_dict)
        assert jira_assignee == "some-email@redhat.com"

        # Test when jira_assignee is not defined
        test_rule_dict = {"step": "test"}
        jira_assignee = Rule._get_jira_assignee(self, test_rule_dict)
        assert jira_assignee is None

    def test_get_jira_priority(self) -> None:
        # Test when jira_priority is defined
        test_rule_dict = {"jira_priority": "major"}
        jira_priority = Rule._get_jira_priority(self, test_rule_dict)
        assert jira_priority == "Major"

        # Test when jira_priority is not defined
        test_rule_dict = {"step": "test"}
        jira_priority = Rule._get_jira_priority(self, test_rule_dict)
        assert jira_priority is None

    def test_get_ignore(self) -> None:
        # Test when defined as "true"
        test_rule_dict = {"ignore": "true"}
        ignore = Rule._get_ignore(self, test_rule_dict)
        assert ignore

        # Test when defined as True
        test_rule_dict = {"ignore": True}
        ignore = Rule._get_ignore(self, test_rule_dict)
        assert ignore

        # Test when defined as "false"
        test_rule_dict = {"ignore": "false"}
        ignore = Rule._get_ignore(self, test_rule_dict)
        assert not ignore

        # Test when defined as False
        test_rule_dict = {"ignore": False}
        ignore = Rule._get_ignore(self, test_rule_dict)
        assert not ignore

        # Test when not defined
        test_rule_dict = {"step": "test"}
        ignore = Rule._get_ignore(self, test_rule_dict)
        assert not ignore
