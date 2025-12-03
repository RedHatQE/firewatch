from datetime import timezone, datetime
import re
from typing import Optional
from jira import Issue
from src.objects.jira_base import Jira
from src.objects.slack_base import SlackClient
from simple_logger.logger import get_logger


LOGGER = get_logger(name=__name__)


class Jira_Escalation:
    def __init__(
        self,
        jira: Jira,
        slack_client: SlackClient,
        slack_channel: str,
        default_labels: list[str],
        additional_labels: list[str],
        default_jira_project: str,
        team_slack_handle: str,
        team_manager_email: str,
        reporter_email: str,
        base_issue_url: str,
    ):
        """
        builds Jira Escalation object, used to escalate issues with relevant escalation action
        Args:
            jira (Jira): a jira object to authenticate with jira
            slack_client (Slack_client): slack object to authenticate with slack
            slack_channel (str): slack channel name string
            default_labels (list[str]): list of default labels to filter out jira search query
            additional_labels (list[str]): list of additional labels to add additional filters
            default_jira_project (str): jira project to search issues
            team_slack_handle (str): slack handle for the user group
            team_manager_email (str): email string used for copying lead contact
            reporter_email (Optional[str]): email string to notify reporter
            base_issue_url (str): jira server url
        """
        self.default_labels = default_labels
        self.additional_labels = additional_labels
        self.default_project = default_jira_project
        self.slack_client = slack_client
        self.jira = jira
        self.team_slack_handle = team_slack_handle
        self.team_manager_email = team_manager_email
        self.reporter_email = reporter_email if reporter_email else None
        self.slack_channel = slack_channel
        self.base_issue_url = base_issue_url

        issues_with_no_assignee = []

        # build query and process ocp lp firewatch tickets in NOACK and ACK status
        jira_query = ""
        for status in ["NO ACK", "ACK"]:
            jira_query = f'Project = {self.default_project} AND status in("{status}") '

            jira_query = self.add_labels_to_jira_query(jira_query)

            LOGGER.info(f"Jira query for issues in {status}:\n{jira_query}")

            issues_with_no_assignee += self.process_issues(jira_query)

        # process PQE tickets
        pqe_jira_query = (
            f"Project != {self.default_project} AND status not in('Resolved','Blocked','Closed','Backlog','Done')"
        )

        pqe_jira_query = self.add_labels_to_jira_query(pqe_jira_query)
        LOGGER.info(f"Jira query for PQE issues:\n{pqe_jira_query}")
        issues_with_no_assignee += self.process_issues(pqe_jira_query)

        # Escalation module summarizes all the issues with no assignee in one message.
        message = "No assignee found for these issues , please do the necessary follow up  : \n "
        count = 0
        for issue in issues_with_no_assignee:
            LOGGER.info(f" item in issue : {issue}")
            count = count + 1

            issue_url = f"<{self.base_issue_url}/browse/{issue}|{issue}>"
            message += f"\n {count}. {issue_url} \n"
        LOGGER.info(f"message to reporter : {message}")
        if len(issues_with_no_assignee) > 0:
            self.send_slack_notification(self.slack_channel, message)

    def process_issues(self, jira_query: str) -> list[str]:
        """
        Process jira issues for escalation based on escalation criteria
        Args:
          jira_query (string): JQL query string to get the issues

        Returns:
          list : issues with no assignee
        """

        issues_list = self.jira.search_issues(jql_query=jira_query)
        LOGGER.info(f"Matching Jira issues : {issues_list}")
        issues_with_no_assignee = []
        for issue_id in issues_list:
            jira_issue = self.jira.get_issue_by_id_or_key_with_changelog(issue_id)
            LOGGER.info(f"Starting to process Jira issue: {jira_issue.key}")

            if jira_issue.fields.assignee is None:
                LOGGER.info(f" No assignee found for this jira issue : {jira_issue.key}")
                issues_with_no_assignee.append(jira_issue.key)
                continue

            # store required jira field values
            comments = jira_issue.fields.comment.comments
            assignee = jira_issue.fields.assignee
            assignee_account_id = self.get_user_account_id(assignee)
            assignee_email = self.get_user_email(assignee)

            current_time = datetime.now(timezone.utc)

            # check if there's a record for status change, if yes then assign that date
            status_changed_date = None
            if jira_issue.fields.status.name == "ACK":
                status_changed_date = self.get_latest_status_change_date(jira_issue=jira_issue)

            # get the date of assignee's latest comment (compare by accountId for Cloud compatibility)
            assignee_comments = [c for c in comments if self.get_user_account_id(c.author) == assignee_account_id]
            assignee_comment_created_date = None
            if assignee_comments:
                latest_comment = max(assignee_comments, key=lambda c: self.parse_jira_datetime(c.updated))
                assignee_comment_created_date = self.parse_jira_datetime(latest_comment.updated)

            if assignee_comment_created_date:
                last_updated_time = assignee_comment_created_date
                LOGGER.info(f"assignee comment date: {last_updated_time}")
            elif status_changed_date:
                last_updated_time = status_changed_date
                LOGGER.info(f"status change date: {last_updated_time}")
            else:
                last_updated_time = self.parse_jira_datetime(jira_issue.fields.updated)
                LOGGER.info(f"last updated change date: {last_updated_time}")

            days_since_update = (current_time - last_updated_time).days
            prow_job_name = self.extract_prow_job_name(jira_issue.fields.description)
            prow_job_url = self.extract_prow_job_link(jira_issue.fields.description)
            issue_url = f"<{self.base_issue_url}/browse/{jira_issue.key}|{jira_issue.key}>"

            # check if issue is updated within corresponding escalation periods and send relevant notifications
            LOGGER.info(f" last update: {days_since_update}")
            self.escalate_issues(
                prow_job_name=prow_job_name,
                prow_job_url=prow_job_url,
                days_since_update=days_since_update,
                jira_issue=jira_issue,
                issue_url=issue_url,
                assignee_email=assignee_email,
            )

        return issues_with_no_assignee

    def send_slack_notification(
        self, slack_channel: str, message: str, email: Optional[str] = None, cc_user_email: Optional[str] = None
    ) -> None:
        """
        Sends slack notification to provided slack channel or email
        Args:
           slack_channel (str): name string for slack channel to post message
           message (str): message string for posting message to slack channel
           email (Optional[str]): email to tag user on slack
           cc_user_email (Optional[str]): email to copy a user in slack message
        """
        prefix_text = ""
        append_text = ""
        if email:
            user_display_name = self.slack_client.get_slack_username(email)
            prefix_text += f"Hi <@{user_display_name}>, \n"

        if cc_user_email:
            cc_user_display_name = self.slack_client.get_slack_username(cc_user_email)
            append_text += f"\n cc: <@{cc_user_display_name}> \n"

        if not email and not cc_user_email:
            usergroup_id = self.slack_client.get_slack_usergroup(self.team_slack_handle)
            if usergroup_id:
                message = f"<!subteam^{usergroup_id}> \n {message}"

        if prefix_text:
            message = prefix_text + message
        if append_text:
            message = message + append_text
        self.slack_client.send_notification(channel=slack_channel, text=message)

    def add_labels_to_jira_query(self, jira_query: str) -> str:
        """
        Build JQL query string based on labels
        Args:
            jira_query (str): query string without any labels

        Returns:
            jira_query (str): processed jira query string after addinng conditions to the labels
        """

        if self.additional_labels:
            formatted_additional_labels = '","'.join(self.additional_labels)
            LOGGER.info(f"Using additional labels: {formatted_additional_labels}")
            jira_query += f' AND (labels IN("{formatted_additional_labels}"))'

        if self.default_labels:
            default_condition = " AND".join([f'labels = "{label}"' for label in self.default_labels])
            jira_query += f" AND ({default_condition})"

        return jira_query

    @staticmethod
    def extract_prow_job_link(jira_description_text: str) -> Optional[str]:
        """
         Get the prow job url from jira issue description field
        Args:
          jira_description_text (str): text string from jira description field

        Returns:
          Optional[str]: prow job url string extracted if found else None
        """
        try:
            url_pattern = r"https://prow\.ci\.openshift\.org/\S+"
            match = re.search(url_pattern, jira_description_text)
            return match.group(0).rstrip("]") if match else None
        except Exception:
            return None

    @staticmethod
    def extract_prow_job_name(jira_description_text: str) -> Optional[str]:
        """
        Get the prow job name from jira issue description field
        Args:
          jira_description_text (str): text string from jira description field

        Returns:
          Optional[str]: prow job name string extracted if found else None
        """

        try:
            pattern = r"periodic-ci-[^\|]+"
            match = re.search(pattern, jira_description_text)
            return match.group(0) if match else None
        except Exception:
            return None

    @staticmethod
    def parse_jira_datetime(jira_timestamp_str: str) -> datetime:
        parsed = datetime.strptime(jira_timestamp_str, "%Y-%m-%dT%H:%M:%S.%f%z")

        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)

    def get_latest_status_change_date(self, jira_issue: Issue) -> Optional[datetime]:
        """
        Get the prow job name from jira issue description field
        Args:
          jira_issue (Issue): jira_issue with chagelog

        Returns:
          datetime: datetime value containing status change date
        """
        changed_date = None
        change_log = jira_issue.changelog

        status_changes = []
        for history in change_log.histories:
            for item in history.items:
                if item.field.lower() == "status":
                    changed_date = self.parse_jira_datetime(history.created)
                    status_changes.append(changed_date)

        LOGGER.info(f"Jira status changed recently on {max(status_changes)}")
        return max(status_changes) if status_changes else None

    @staticmethod
    def get_user_account_id(user: Optional[object]) -> Optional[str]:
        """
        Extract accountId from a Jira user object.

        In Jira Cloud, users are identified by accountId rather than username.
        This method safely extracts the accountId, falling back to None if unavailable.

        Args:
            user: A Jira user object (e.g., issue.fields.assignee, comment.author)

        Returns:
            The user's accountId if available, None otherwise.
        """
        if user is None:
            return None
        return getattr(user, "accountId", None)

    @staticmethod
    def get_user_email(user: Optional[object]) -> Optional[str]:
        """
        Extract emailAddress from a Jira user object.

        In Jira Cloud, email visibility may be restricted by privacy settings.
        This method safely extracts the email, returning None if unavailable.

        Args:
            user: A Jira user object (e.g., issue.fields.assignee, comment.author)

        Returns:
            The user's email address if available, None otherwise.
        """
        if user is None:
            return None
        return getattr(user, "emailAddress", None)

    def escalate_issues(
        self,
        jira_issue: Issue,
        prow_job_name: Optional[str],
        prow_job_url: Optional[str],
        days_since_update: int,
        issue_url: str,
        assignee_email: Optional[str],
    ) -> None:
        """
        Performs escalation check and sends relevant notification.

        Args:
            jira_issue (Issue): jira issue to escalate
            prow_job_name (str): job name used to build escalation message
            prow_job_url (str): job url used to build escalation message
            days_since_update (datetime): days passed between current date and jira issue update date
            issue_url (str): url used to build escalation message
            assignee_email (Optional[str]): Email for assignee to send escalation message.
                May be None in Jira Cloud due to privacy settings.
        """
        base_message = (
            f"please provide an update on issue : {issue_url} \n Prow Job Link : <{prow_job_url}|{prow_job_name}>"
        )

        if days_since_update > 4:
            message = f"\n 4 or more days since last update, {base_message} "
            LOGGER.info(f" escalation slack message : {message}")
            self.send_slack_notification(
                self.slack_channel, message, email=assignee_email, cc_user_email=self.team_manager_email
            )

        elif 2 < days_since_update <= 4:
            message = f"\n 2 or more days since last update, {base_message}"
            LOGGER.info(f" escalation slack message : {message}")
            self.send_slack_notification(self.slack_channel, message, email=assignee_email)

        elif 1 < days_since_update <= 2:
            LOGGER.info(
                f"\n 1 or more days since last comment, please add comment if there is any updates on the issue: {jira_issue.key}"
            )
            assignee_account_id = self.get_user_account_id(jira_issue.fields.assignee)
            comment = f"[~accountId:{assignee_account_id}], please provide update for this issue."
            LOGGER.info(f"escalation comment: {comment}")
            self.jira.comment(jira_issue, comment)
