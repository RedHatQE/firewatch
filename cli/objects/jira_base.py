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
import logging
from typing import Optional

from jira import Issue
from jira import JIRA
from jira.exceptions import JIRAError


class Jira:
    def __init__(self, jira_config_path: str) -> None:
        """
        Constructs the Jira object used for authenticating and interacting with a Jira server

        :param jira_config_path: The path to the configuration file that hold authentication credentials
        """
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(
            __name__,
        )
        self.proxies: dict[str, str] = {}

        with open(jira_config_path) as jira_config_file:
            jira_config = json.load(jira_config_file)

        self.url = jira_config["url"]
        self.token = jira_config["token"]
        self.proxies = jira_config["proxies"]

        self.connection = JIRA(
            server=self.url,
            token_auth=self.token,
            proxies=self.proxies,
        )
        self.logger.info("Jira authentication successful...")

    def create_issue(
        self,
        project: str,
        summary: str,
        description: str,
        issue_type: str,
        file_attachments: Optional[list[str]] = None,
    ) -> Issue:
        """
        Used to create a Jira issue and attach any given files to that issue.

        :param project: The Jira project the issue should be filed under
        :param summary: Title or summary of the issue
        :param description: Description of the issue
        :param issue_type: Issue type (Bug, Task, etc.)
        :param file_attachments: An optional list of file paths. Each file in the list will be attached to the issue

        :returns: A Jira Issue object
        """

        issue_dict = {
            "project": {"key": project},
            "summary": summary,
            "description": description,
            "issuetype": {"name": issue_type},
        }

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

        return issue

    def relate_issues(self, inward_issue: str, outward_issue: str) -> bool:
        """
        Used to relate two issues in Jira

        :param inward_issue: The first issue you'd like to relate to the second issue
        :param outward_issue: The second issue you'd like to relate to the first issue

        :returns: A boolean value. True = Issues related successfully, False = Issues not related successfully
        """
        try:
            self.connection.create_issue_link(
                type="Relates",
                inwardIssue=inward_issue,
                outwardIssue=outward_issue,
            )
            self.logger.info(
                f"Issue {inward_issue} and issue {outward_issue} related successfully",
            )
            return True
        except Exception as e:
            self.logger.error(f"Failure relating {inward_issue} with {outward_issue}")
            return False

    def project_exists(self, project_key: str) -> bool:
        """
        Used to validate that the "project_key" exists in the Jira server

        :param project_key: Jira project key you'd like to check

        :returns: A boolean value. True = project exists, False = project does not exist
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
