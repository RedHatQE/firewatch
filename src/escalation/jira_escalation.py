from datetime import timezone, datetime
import re
from typing import Optional
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
        mpiit_escalation_contact: str,
        watcher_email: str,
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
            mpiit_escalation_contact (str): email string used for copying lead contact
            watcher_email (str): email string to notify wwatcher
        """
        self.default_labels = default_labels
        self.additional_labels = additional_labels
        self.default_project = default_jira_project
        self.slack_client = slack_client
        self.jira = jira
        self.team_slack_handle = team_slack_handle
        self.mpiit_escalation_contact = mpiit_escalation_contact
        self.watcher_email = watcher_email
        self.slack_channel = slack_channel

        # build query and process ocp lp firewatch tickets in NOACK and ACK status
        jira_query = ""
        for status in ["NO ACK", "ACK"]:
            jira_query = f'Project = {self.default_project} AND status in("{status}") '

            LOGGER.info(f" jql querry : {jira_query}")
            jira_query = self.add_labels_to_jira_query(jira_query)

            LOGGER.info(f" Jira query for issues in {status}: {jira_query}")

            self.process_issues(jira_query)

        # process PQE tickets
        pqe_jira_query = (
            f"Project != {default_jira_project} AND status not in('Resolved','Blocked','Closed','Backlog','Done')"
        )

        pqe_jira_query = self.add_labels_to_jira_query(pqe_jira_query)
        self.process_issues(pqe_jira_query)

    def process_issues(self, jira_query: str) -> None:
        """
        Process jira issues for escalation based on escaltion criteria
        Args:
          jira_query (string): JQL query string to get the issues
        """

        issues_list = self.jira.search_issues(jql_query=jira_query)
        LOGGER.info(f" Jira issues : {issues_list}")
        issues_with_no_assignee = []
        for issue in issues_list:
            jira_issue = self.jira.get_issue_by_id_or_key_with_changelog(issue)

            if jira_issue.fields.assignee is None:
                LOGGER.info(f" No assignee found for this jira issue : {jira_issue.key}")

                issues_with_no_assignee.append(jira_issue)

                continue

            status_changed_date = None

            if jira_issue.fields.status.name == "ACK":
                change_log = jira_issue.changelog
                status_changed_date = None
                for history in change_log.histories:
                    for item in history.items:
                        if item.field == "status":
                            status_changed_date = datetime.strptime(history.created, "%Y-%m-%dT%H:%M:%S.%f%z")
                        break
                    if status_changed_date:
                        break

            comments = jira_issue.fields.comment.comments
            assignee = jira_issue.fields.assignee
            assignee_email = assignee.emailAddress

            assignee_comments = [c for c in comments if c.author.emailAddress == assignee.emailAddress]
            assignee_comment_created_date = None
            if assignee_comments:
                latest_comment = max(
                    assignee_comments, key=lambda c: datetime.strptime(c.updated, "%Y-%m-%dT%H:%M:%S.%f%z")
                )
                assignee_comment_created_date = datetime.strptime(latest_comment.updated, "%Y-%m-%dT%H:%M:%S.%f%z")

            updated_date = datetime.strptime(jira_issue.fields.updated, "%Y-%m-%dT%H:%M:%S.%f%z")

            last_updated_time = assignee_comment_created_date or status_changed_date or updated_date

            current_time = datetime.now(timezone.utc)

            days_since_update = (current_time - last_updated_time).days

            # check if issue is updated within escalation threshold

            LOGGER.info(f" last update: {last_updated_time}")

            prow_job_name = self.extract_prow_job_name(jira_issue.fields.description)
            prow_job_url = self.extract_prow_job_link(jira_issue.fields.description)

            if days_since_update > 4:
                issue_url = f"<https://issues.stage.redhat.com/browse/{jira_issue.key}|{jira_issue.key}>"

                message = f"3 or more days since last comment from assignee, please provide an update on issue : {issue_url} \n Prow Job Link : <{prow_job_url}|{prow_job_name}>"
                self.send_slack_notification(
                    self.slack_channel, message, email=assignee_email, cc_user_email=self.mpiit_escalation_contact
                )

            elif 2 < days_since_update <= 4:
                issue_url = f"<https://issues.stage.redhat.com/browse/{jira_issue.key}|{jira_issue.key}>"
                message = f" 2 or more days since last comment from assignee,please provide an update on issue : {issue_url} \n Prow Job Link : <{prow_job_url}|{prow_job_name}>"
                self.send_slack_notification(self.slack_channel, message, email=assignee_email)

            elif 1 < days_since_update <= 2:
                LOGGER.info(f" 1 or more days since last comment,add comment on the issue: {jira_issue.key}")
                comment = f"[~{jira_issue.fields.assignee.name}], please provide update for this issue."
                LOGGER.info(f"escalation comment: {comment}")
                self.jira.comment(jira_issue, comment)

        message_to_watcher = ""
        for issue in issues_with_no_assignee:
            issue_url = f"<https://issues.stage.redhat.com/browse/{issue.key}|{issue.key}>"
            prow_job_name = self.extract_prow_job_name(issue.fields.description)
            prow_job_url = self.extract_prow_job_link(issue.fields.description)
            message_to_watcher += f"No assignee found for this jira issue :  {issue_url} \n Prow Job Link : <{prow_job_url}|{prow_job_name}>"

        if len(issues_with_no_assignee) > 0:
            message_to_watcher += "Please provide an update for above issues \n"
            self.send_slack_notification(
                self.slack_channel, message=message_to_watcher, email=self.watcher_email
            )  # comment this for testing

    def send_slack_notification(
        self, slack_channel: str, message: str, email: Optional[str] = None, cc_user_email: Optional[str] = None
    ) -> None:
        """
        Args:
           slack_channel (str): name string for slack channel to post message
           message (str): message string for posting mesdage to slack channel
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
            LOGGER.info(f" add labels {formatted_additional_labels}")
            jira_query += f' AND (labels IN("{formatted_additional_labels}"))'

        if self.default_labels:
            # formatted_default_labels = '","'.join(self.default_labels)
            default_condition = " AND".join([f'labels = "{label}"' for label in self.default_labels])
            jira_query += f" AND ({default_condition})"

        return jira_query

    def extract_prow_job_link(self, jira_description_text: str) -> Optional[str]:
        """
        get the prow job url from jira issue description field
        Args:
          jira_description_text (str): text string from jira description field

        Returns:
          url (Optional[str]): prow job url extracted if found else None
        """

        LOGGER.info(f" text : \n {jira_description_text}")

        url_pattern = r"https://prow\.ci\.openshift\.org/\S+"
        match = re.search(url_pattern, jira_description_text)

        if match:
            url = match.group(0).rstrip("]")
            LOGGER.info(f"match : {url}")
            return url
        return None

    def extract_prow_job_name(self, jira_description_text: str) -> Optional[str]:
        """
        Get the prow job name from jira issue description field
        Args:
          jira_description_text (str): text string from jira description field

        Returns:
          job_name (Optional[str]): prow job name extracted if found else None
        """

        LOGGER.info(f" text : \n {jira_description_text}")

        pattern = r"periodic-ci-[^\|]+"
        match = re.search(pattern, jira_description_text)

        if match:
            LOGGER.info(f"match  job name : {match.group()}")
            job_name = match.group()
            return job_name
        return None
