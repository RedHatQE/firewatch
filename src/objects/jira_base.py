import json
from typing import Any
from typing import Optional

from jira import Issue
from jira import JIRA
from jira.exceptions import JIRAError
from pyhelper_utils.general import ignore_exceptions
from simple_logger.logger import get_logger

from src.objects.jira_adf import closed_by_firewatch_adf
from src.objects.jira_adf import plain_text_to_adf_doc
from src.objects.jira_adf import sanitize_jira_adf_doc

LOGGER = get_logger(name=__name__)


class Jira:
    def __init__(self, jira_config_path: str) -> None:
        """
        Constructs the Jira object used for authenticating and interacting with a Jira server.

        Args:
            jira_config_path (str): The path to the configuration file that hold authentication credentials.
        """
        self.logger = LOGGER
        self.proxies: dict[str, str] = {}

        with open(jira_config_path) as jira_config_file:
            jira_config = json.load(jira_config_file)

        self.url = jira_config.get("url")
        self.token = jira_config.get("token")
        self.email = jira_config.get("email")

        jira_kwargs: dict[str, Any] = {
            "server": self.url,
            "options": {"rest_api_version": "3"},
        }

        if self.email:
            jira_kwargs["basic_auth"] = (self.email, self.token)
        else:
            jira_kwargs["token_auth"] = self.token

        if "proxies" in jira_config:
            self.proxies = jira_config.get("proxies")
            jira_kwargs["proxies"] = self.proxies

        self.connection = JIRA(**jira_kwargs)

        LOGGER.info("Jira authentication successful...")

    @ignore_exceptions(retry=3, retry_interval=1, raise_final_exception=True, logger=LOGGER)
    def create_issue(
        self,
        project: str,
        summary: str,
        description: str,
        issue_type: str,
        component: Optional[list[str]] = None,
        epic: Optional[str] = None,
        file_attachments: Optional[list[str]] = None,
        labels: Optional[list[Optional[str]]] = None,
        affects_version: Optional[str] = None,
        assignee: Optional[str] = None,
        priority: Optional[str] = None,
        security_level: Optional[str] = None,
        watchers: Optional[list[str]] = None,
        additional_assignees: Optional[list[str]] = None,
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
            "description": sanitize_jira_adf_doc(plain_text_to_adf_doc(description)),
            "issuetype": {"name": issue_type},
        }

        labels = [] if not labels else labels

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

        LOGGER.info(
            "A Jira issue will be reported.",
        )
        response = self._jira_request("post", f"{self.url}/rest/api/3/issue", {"fields": issue_dict})
        issue = self.connection.issue(response.json()["key"])
        LOGGER.info(
            f"{issue} has been reported to Jira: {self.url}/browse/{issue}",
        )

        if file_attachments is not None:
            for file_path in file_attachments:
                self.add_attachment_to_issue(issue=issue, attachment_path=file_path)

        if epic is not None:
            epic_search = self.connection.search_issues(f"issue={epic}", maxResults=False)
            if len(epic_search) == 1:
                epic_id = epic_search[0].id
                self.connection.add_issues_to_epic(
                    epic_id=epic_id,
                    issue_keys=issue.key,
                )
            else:
                LOGGER.error(f"Error finding Jira ID of epic {epic}")

        if assignee is not None:
            self.assign_issue(user_email=assignee, issue=issue.key)
            LOGGER.info(f"Issue {issue} has been assigned to user {assignee}")

        if watchers:
            self.add_watchers_to_issue(issue_key=issue.key, watcher_emails=watchers)

        if additional_assignees:
            self._set_additional_assignees(issue_key=issue.key, assignee_emails=additional_assignees)

        if close_issue:
            self._transition_issue_with_adf_comment(
                issue_key=issue.key,
                transition_name="closed",
                adf_body=closed_by_firewatch_adf(),
            )

        return issue

    @ignore_exceptions(retry=3, retry_interval=1, raise_final_exception=True, logger=LOGGER)
    def add_attachment_to_issue(self, issue: Issue, attachment_path: str) -> None:
        """
        Add and upload the attachment from attachment_path to the Jira Issue object provided.

        Args:
            issue (Issue): The Jira issue the attachment should be added to.
            attachment_path (str): The path of the file to upload as an attachment to the issue.

        Returns:
            None
        """
        try:
            self.connection.add_attachment(issue=issue.key, attachment=attachment_path)
            LOGGER.info(f"Attachment {attachment_path} has been uploaded to {issue}")
        except JIRAError as e:
            LOGGER.exception(
                msg=f"""
            exception caught while attempting to upload attachment to Jira issue:
                {e=}
                {issue=}
                {attachment_path=}
            """
            )

    @ignore_exceptions(retry=3, retry_interval=1, raise_final_exception=True, logger=LOGGER)
    def search(self, jql_query: str) -> list[Any]:
        """
        Performs a Jira JQL query using the Jira connection and returns a list of issues, including all fields.

        Args:
            jql_query (str): JQL query to run.

        Returns:
            list[Any]: List of issues that are returned from the query.
        """
        return self.connection.search_issues(jql_query, maxResults=False)

    @ignore_exceptions(retry=3, retry_interval=1, raise_final_exception=True, logger=LOGGER)
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

    def _jira_request(self, method: str, url: str, payload: dict[str, Any]) -> Any:
        fn = getattr(self.connection._session, method)
        response = fn(url, json=payload, headers={"Content-Type": "application/json"})
        if not response.ok:
            raise JIRAError(response.text, response.status_code, response.url)
        return response

    def _post_issue_comment_adf(self, issue_key: str, adf_body: dict[str, Any]) -> None:
        url = self.connection._get_url(f"issue/{issue_key}/comment")
        self._jira_request("post", url, {"body": sanitize_jira_adf_doc(adf_body)})

    def _transition_issue_with_adf_comment(
        self,
        issue_key: str,
        transition_name: str,
        adf_body: dict[str, Any],
    ) -> None:
        transition_id = self.connection.find_transitionid_by_name(issue_key, transition_name)
        if transition_id is None:
            raise JIRAError(
                text=f"Invalid transition name. {transition_name}",
                status_code=400,
                url="",
            )
        payload: dict[str, Any] = {
            "transition": {"id": transition_id},
            "update": {"comment": [{"add": {"body": sanitize_jira_adf_doc(adf_body)}}]},
        }
        url = self.connection._get_url(f"issue/{issue_key}/transitions")
        self._jira_request("post", url, payload)

    @ignore_exceptions(retry=3, retry_interval=1, raise_final_exception=True, logger=LOGGER)
    def comment(self, issue_id: str, comment: str | dict[str, Any]) -> None:
        """
        Comments on the issue_id.

        Args:
            issue_id (str): Issue to comment on.
            comment (str | dict): Plain text (stored as minimal ADF) or an ADF doc dict for the body.
        """
        body = plain_text_to_adf_doc(comment) if isinstance(comment, str) else comment
        self._post_issue_comment_adf(issue_id, body)

    @ignore_exceptions(retry=3, retry_interval=1, raise_final_exception=True, logger=LOGGER)
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
            LOGGER.info(
                f"Issue {inward_issue} and issue {outward_issue} related successfully",
            )
            return True
        except Exception as ex:
            LOGGER.error(f"Failure relating {inward_issue} with {outward_issue}")
            LOGGER.error(ex)
            return False

    @ignore_exceptions(retry=3, retry_interval=1, raise_final_exception=True, logger=LOGGER)
    def close_issue(self, issue_id: str) -> None:
        """
        Closes a Jira issue by transitioning it to the "closed" state with a standard comment.

        Args:
            issue_id (str): The ID or key of the issue to close.
        """
        try:
            issue = self.get_issue_by_id_or_key(issue_id)
            self.logger.info("Closing issue %s with transition 'closed'...", issue_id)

            self._transition_issue_with_adf_comment(
                issue_key=issue.key,
                transition_name="closed",
                adf_body=closed_by_firewatch_adf(),
            )

            self.logger.info("Issue %s has been successfully closed.", issue_id)
        except JIRAError as e:
            self.logger.error("Failed to close issue %s. Jira error: %s", issue_id, e.text)
        except Exception as ex:
            self.logger.error("Unexpected error while closing issue %s: %s", issue_id, ex)

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
                LOGGER.debug(f"Jira project {project_key} exists...")
                return True
            else:
                LOGGER.error(
                    f"Jira project {project_key} does not exist on {self.url}...",
                )
                return False

        except JIRAError as e:
            if e.status_code == 404:
                LOGGER.error(
                    f"Jira project {project_key} does not exist on {self.url}...",
                )
                return False
            else:
                LOGGER.error(f"Error: {e.text}")
                return False

    @ignore_exceptions(retry=3, retry_interval=1, raise_final_exception=True, logger=LOGGER)
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
            LOGGER.error(f"Unable to assign issue {issue} to user {user_email}.")
            LOGGER.error(ex)
            return False

    @ignore_exceptions(retry=3, retry_interval=1, raise_final_exception=True, logger=LOGGER)
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

        LOGGER.error(
            f"Security level {security_level} not found in {project_key}, no security level will be applied.",
        )
        return None

    @ignore_exceptions(retry=3, retry_interval=1, raise_final_exception=True, logger=LOGGER)
    def get_issue_by_id_or_key(self, issue: str) -> Issue:
        """
        Get a Jira Issue object from the given issue id or key field value.

        Args:
            issue (str): The ID or key field value of the Jira Issue object to return.

        Returns:
            Issue: A Jira Issue object.
        """
        return self.connection.issue(id=issue)

    @ignore_exceptions(retry=3, retry_interval=1, raise_final_exception=True, logger=LOGGER)
    def _update_issue_labels(
        self,
        issue_id_or_key: str,
        labels: list[str],
        operation: str,
    ) -> tuple[Issue, bool]:
        issue = self.get_issue_by_id_or_key(issue_id_or_key)
        payload = {"update": {"labels": [{operation: label} for label in labels]}}
        try:
            self._jira_request("put", issue.self, payload)
        except JIRAError as error:
            LOGGER.error(
                "Failed to %s labels %s on issue %s. Error: %s",
                operation,
                labels,
                issue_id_or_key,
                error.text,
            )
            if error.status_code in (400, 403):
                LOGGER.info(
                    "This may be caused by project configuration, missing permissions, or the Jira user."
                    ' Please see the "Jira User Permissions" section in the README for more information.',
                )
                return issue, False
            raise
        return issue, True

    def add_labels_to_issue(self, issue_id_or_key: str, labels: list[str]) -> tuple[Issue, bool]:
        return self._update_issue_labels(issue_id_or_key, labels, "add")

    def remove_labels_from_issue(self, issue_id_or_key: str, labels: list[str]) -> tuple[Issue, bool]:
        return self._update_issue_labels(issue_id_or_key, labels, "remove")

    def add_watchers_to_issue(self, issue_key: str, watcher_emails: list[str]) -> None:
        for email in watcher_emails:
            account_id = self._resolve_account_id(email)
            if account_id is None:
                continue
            try:
                self.connection.add_watcher(issue_key, account_id)
                LOGGER.info(f"Added watcher {email} to issue {issue_key}")
            except JIRAError as e:
                LOGGER.warning(f"Failed to add watcher {email} to {issue_key}: {e.text}")

    def _set_additional_assignees(self, issue_key: str, assignee_emails: list[str]) -> None:
        account_ids = []
        for email in assignee_emails:
            account_id = self._resolve_account_id(email)
            if account_id is not None:
                account_ids.append({"accountId": account_id})

        if not account_ids:
            LOGGER.warning(f"No valid account IDs resolved for additional assignees on {issue_key}")
            return

        issue = self.get_issue_by_id_or_key(issue_key)
        payload = {"fields": {"customfield_10465": account_ids}}
        try:
            self._jira_request("put", issue.self, payload)
            LOGGER.info(f"Set additional assignees on issue {issue_key}")
        except JIRAError as e:
            LOGGER.warning(f"Failed to set additional assignees on {issue_key}: {e.text}")

    def _resolve_account_id(self, email: str) -> Optional[str]:
        try:
            users = self.connection.search_users(query=email, maxResults=1)
            if users:
                return users[0].accountId
            self.logger.warning(f"No Jira user found for email {email}")
            return None
        except JIRAError as e:
            self.logger.warning(f"Failed to resolve Jira account ID for {email}: {e.text}")
            return None

    @ignore_exceptions(retry=3, retry_interval=1, raise_final_exception=True, logger=LOGGER)
    def get_issue_by_id_or_key_with_changelog(self, issue: str) -> Issue:
        """
        Get a Jira Issue object from the given issue id or key field value.

        Args:
            issue (str): The ID or key field value of the Jira Issue object to return.

        Returns:
            Issue: A Jira Issue object.
        """
        return self.connection.issue(id=issue, expand="changelog")
