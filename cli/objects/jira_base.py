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
import json
from typing import Any
from typing import Optional

from jira import Issue
from jira import JIRA
from jira.exceptions import JIRAError
from simple_logger.logger import get_logger


class Jira:
    def __init__(self, jira_config_path: str) -> None:
        """
        Constructs the Jira object used for authenticating and interacting with a Jira server.

        Args:
            jira_config_path (str): The path to the configuration file that hold authentication credentials.
        """
        self.logger = get_logger(__name__)
        self.proxies: dict[str, str] = {}

        with open(jira_config_path) as jira_config_file:
            jira_config = json.load(jira_config_file)

        self.url = jira_config.get("url")
        self.token = jira_config.get("token")

        if "proxies" in jira_config:
            self.proxies = jira_config.get("proxies")
            self.connection = JIRA(
                server=self.url,
                token_auth=self.token,
                proxies=self.proxies,
            )
        else:
            self.connection = JIRA(
                server=self.url,
                token_auth=self.token,
            )

        self.logger.info("Jira authentication successful...")

    def create_issue(
        self,
        project: str,
        summary: str,
        description: str,
        issue_type: str,
        component: Optional[list[str]] = None,
        epic: Optional[str] = None,
        file_attachments: Optional[list[str]] = None,
        labels: list[Optional[str]] = [],
        affects_version: Optional[str] = None,
        assignee: Optional[str] = None,
        priority: Optional[str] = None,
        security_level: Optional[str] = None,
        close_issue: Optional[bool] = False,
    ) -> Issue:
        """
        Used to create a Jira issue and attach any given files to that issue.

        Args:
            project (str): The Jira project the issue should be filed under.
            summary (str): Title or summary of the issue.
            description (str): Description of the issue.
            issue_type (str): Issue type (Bug, Task, etc.).
            component (Optional[list[str]]): The component or components you'd like the bug to be associated with. Must be a comma deliminated string to specify multiple components. If not supplied, the bug will not have a component.
            epic (Optional[str]): The epic ID (PROJECT-8) the new issue should be a part of. If not supplied, the issue will not be associated with an epic.
            file_attachments (Optional[list[str]]): An optional list of file paths. Each file in the list will be attached to the issue.
            labels (list[Optional[str]]): An optional list of labels to add to the issue.
            affects_version (Optional[str]): Value for version affected. Bugs created using this will populate the "Affects Version/s" field in Jira.
            assignee (Optional[str]): An optional string for the assignee of an issue. Should be the email address of the user.
            priority (Optional[str]): An optional string representing the desired priority of the issue being created.
            security_level (Optional[str]): An optional string representing the desired security level of the issue being created.
            close_issue (Optional[bool]): Close issue if set to True

        Returns:
            Issue: A Jira Issue object.
        """
        issue_dict = {
            "project": {"key": project},
            "summary": summary,
            "description": description,
            "issuetype": {"name": issue_type},
        }

        if labels:
            # MyPy spits out an odd error here unless ignored.
            issue_dict.update({"labels": labels})  # type: ignore

        if component:
            components = []
            for comp in component:
                components.append({"name": comp})
            # MyPy spits out an odd error here unless ignored.
            issue_dict.update({"components": components})  # type: ignore

        if affects_version:
            issue_dict.update({"versions": [{"name": affects_version}]})  # type: ignore

        if priority:
            issue_dict.update({"priority": {"name": priority}})

        if security_level:
            security_id = self._get_security_level_id(
                security_level=security_level,
                project_key=project,
            )
            if security_id:
                issue_dict.update({"security": {"id": security_id}})

        self.logger.info(
            f"A Jira issue will be reported.",
        )
        issue = self.connection.create_issue(issue_dict)
        self.logger.info(
            f"{issue} has been reported to Jira: {self.url}/browse/{issue}",
        )

        if file_attachments is not None:
            for file_path in file_attachments:
                self.connection.add_attachment(issue=issue.key, attachment=file_path)
                self.logger.info(f"Attachment {file_path} has been uploaded to {issue}")

        if epic is not None:
            epic_search = self.connection.search_issues(f'issue="{epic}"')
            if len(epic_search) == 1:
                epic_id = epic_search[0].id
                self.connection.add_issues_to_epic(
                    epic_id=epic_id,
                    issue_keys=issue.key,
                )
            else:
                self.logger.error(f"Error finding Jira ID of epic {epic}")

        if assignee is not None:
            self.assign_issue(user_email=assignee, issue=issue.key)
            self.logger.info(f"Issue {issue} has been assigned to user {assignee}")

        if close_issue:
            self.connection.transition_issue(
                issue=issue.key,
                transition="closed",
                comment="Closed by [firewatch|https://github.com/CSPI-QE/firewatch].",
            )

        return issue

    def search(self, jql_query: str) -> list[Any]:
        """
        Performs a Jira JQL query using the Jira connection and returns a list of issues, including all fields.

        Args:
            jql_query (str): JQL query to run.

        Returns:
            list[Any]: List of issues that are returned from the query.
        """
        return self.connection.search_issues(jql_query, validate_query=True)

    def search_issues(self, jql_query: str) -> list[str]:
        """
        Performs a Jira JQL query using the Jira connection and returns a list of strings representing issue keys.

        Args:
            jql_query (str): JQL query to run.

        Returns:
            list[str]: List of issues that are returned from the query.
        """
        issues = []
        results = self.search(jql_query)

        for issue in results:
            issues.append(issue.key)

        return issues

    def comment(self, issue_id: str, comment: str) -> None:
        """
        Comments on the issue_id.

        Args:
            issue_id (str): Issue to comment on.
            comment (str): Comment to add to issue.
        """
        self.connection.add_comment(issue_id, comment)

    def relate_issues(self, inward_issue: str, outward_issue: str) -> bool:
        """
        Used to relate two issues in Jira.

        Args:
            inward_issue (str): The first issue you'd like to relate to the second issue.
            outward_issue (str): The second issue you'd like to relate to the first issue.

        Returns:
            bool: True if issues related successfully, False otherwise.
        """
        try:
            self.connection.create_issue_link(
                type="relates to",
                inwardIssue=inward_issue,
                outwardIssue=outward_issue,
            )
            self.logger.info(
                f"Issue {inward_issue} and issue {outward_issue} related successfully",
            )
            return True
        except Exception as ex:
            self.logger.error(f"Failure relating {inward_issue} with {outward_issue}")
            self.logger.error(ex)
            return False

    def project_exists(self, project_key: str) -> bool:
        """
        Used to validate that the "project_key" exists in the Jira server.

        Args:
            project_key (str): Jira project key you'd like to check.

        Returns:
            bool: True if project exists, False otherwise.
        """
        try:
            project = self.connection.project(project_key)

            if project:
                self.logger.debug(f"Jira project {project_key} exists...")
                return True
            else:
                self.logger.error(
                    f"Jira project {project_key} does not exist on {self.url}...",
                )
                return False

        except JIRAError as e:
            if e.status_code == 404:
                self.logger.error(
                    f"Jira project {project_key} does not exist on {self.url}...",
                )
                return False
            else:
                self.logger.error(f"Error: {e.text}")
                return False

    def assign_issue(self, user_email: str, issue: str) -> bool:
        """
        Assigns a given issue to the user specified.

        Args:
            user_email (str): A string value representing the email address of use the issue should be assigned to.
            issue (str): A string value representing the issue that should be assigned.

        Returns:
            bool: True if the issue has been assigned successfully, False otherwise.
        """
        # Assign the issue
        try:
            return self.connection.assign_issue(issue=issue, assignee=user_email)
        except Exception as ex:
            self.logger.error(f"Unable to assign issue {issue} to user {user_email}.")
            self.logger.error(ex)
            return False

    def _get_security_level_id(
        self,
        security_level: str,
        project_key: str,
    ) -> Optional[str]:
        """
        Used to get the security level ID for a given security level.

        Args:
            security_level (str): The security level you'd like to get the ID for.
            project_key (str): The project key the security level is associated with.

        Returns:
            Optional[str]: The security level ID.
        """

        project = self.connection.project(project_key)
        security_levels = self.connection.project_issue_security_level_scheme(
            project.id,
        ).levels

        for level in security_levels:
            if level.name.lower() == security_level.lower():
                return level.id

        self.logger.error(
            f"Security level {security_level} not found in {project_key}, no security level will be applied.",
        )
        return None

    def get_issue_by_id_or_key(self, issue: str) -> Issue:
        """
        Get a Jira Issue object from the given issue id or key field value.

        Args:
            issue (str): The ID or key field value of the Jira Issue object to return.

        Returns:
            Issue: A Jira Issue object.
        """
        return self.connection.issue(id=issue)

    def add_labels_to_issue(self, issue_id_or_key: str, labels: list[str]) -> Issue:
        """
        Append the given labels to a Jira issue, as identified by the issue's key or ID field value.
        If the label already exists on the issue, it is not duplicated.
        Returns the value of the modified issue.

        Args:
            issue_id_or_key (str): The ID or key field value of the Jira Issue object to return.
            labels: list[str]: The list of labels to add to the Jira issue.
        Returns:
            Issue: A Jira Issue object.
        """
        issue = self.get_issue_by_id_or_key(issue_id_or_key)
        issue.update(update={"labels": [{"add": label} for label in labels]})
        return issue
