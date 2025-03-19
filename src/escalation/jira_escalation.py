import datetime
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

        # build query and process ocp lp firewatch tickets in NOACK and ACK status
        jira_query = ""
        for status in ["NO ACK", "ACK"]:
            if self.default_project is not None:
                jira_query = f'Project = {self.default_project} AND status in("{status}") '
            else:
                jira_query = f'status in("{status}") '

            LOGGER.info(f" jql querry : {jira_query}")
            jira_query = self.add_labels_to_jira_query(jira_query)

            LOGGER.info(f" Jira query for issues in {status}: {jira_query}")

            self.process_issues(jira_query, slack_channel)

        # process PQE tickets
        pqe_jira_query = (
            f"Project != {default_jira_project} AND status not in('Resolved','Blocked','Closed','Backlog','Done')"
        )

        pqe_jira_query = self.add_labels_to_jira_query(pqe_jira_query)
        self.process_issues(pqe_jira_query, slack_channel)

    def process_issues(self, jira_query: str, slack_channel: str) -> None:
        """
        Process jira issues for escalation based on escaltion criteria
        Args:
          jira_query (string): JQL query string to get the issues
          slack_channel (str): slack channel name to send notifications
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
                            status_changed_date = datetime.datetime.strptime(history.created, "%Y-%m-%dT%H:%M:%S.%f%z")
                        break
                    if status_changed_date:
                        break

            comments = jira_issue.fields.comment.comments

            updated_date = datetime.datetime.strptime(jira_issue.fields.updated, "%Y-%m-%dT%H:%M:%S.%f%z")
            assignee_comment_created_date = None
            last_updated_time = None

            assignee = jira_issue.fields.assignee
            assignee_email = assignee.emailAddress

            # check if issue is updated within escalation threshold

            for comment in comments:
                if comment.author.emailAddress == assignee.emailAddress:
                    assignee_comment_created_date = datetime.datetime.strptime(
                        comment.created, "%Y-%m-%dT%H:%M:%S.%f%z"
                    )

            if assignee_comment_created_date:
                last_updated_time = assignee_comment_created_date
            elif status_changed_date:
                last_updated_time = status_changed_date
            else:
                last_updated_time = updated_date

            LOGGER.info(f" last update: {last_updated_time}")

            if last_updated_time <= self.escalation_threshold(3):
                issue_url = f"<https://issues.stage.redhat.com/browse/{jira_issue.key}|{jira_issue.key}>"
                message = (
                    f"3 or more days since last comment from assignee, please provide an update on issue : {issue_url}"
                )
                self.send_slack_notification(
                    slack_channel, message, email=assignee_email, cc_user_email=self.mpiit_escalation_contact
                )

            elif last_updated_time <= self.escalation_threshold(2):
                issue_url = f"<https://issues.stage.redhat.com/browse/{jira_issue.key}|{jira_issue.key}>"
                message = (
                    f" 2 or more days since last comment from assignee,please provide an update on issue : {issue_url}"
                )
                self.send_slack_notification(slack_channel, message, email=assignee_email)

            elif last_updated_time <= self.escalation_threshold(1):
                LOGGER.info(f" 1 or more days since last comment,add comment on the issue: {jira_issue.key}")
                comment = f"[~{jira_issue.fields.assignee.name}], please provide update for this issue."
                LOGGER.info(f"escalation comment: {comment}")
                self.jira.comment(jira_issue, comment)

        message_to_watcher = ""
        for issue in issues_with_no_assignee:
            issue_url = f"<https://issues.stage.redhat.com/browse/{issue.key}|{issue.key}>"
            message_to_watcher += f"No assignee found for this jira issue :  {issue_url} \n"

        if len(issues_with_no_assignee) > 0:
            message_to_watcher += "Please provide an update for above issues \n"
            self.send_slack_notification(
                slack_channel, message=message_to_watcher, email=self.watcher_email
            )  # comment this for testing

    def escalation_threshold(self, days: int) -> datetime.datetime:
        """
        function to calculate escalation period based on days provide from current date

        Args:
            days (int): number of days

        Returns:
            escalation_date (datetime.datetime): threshold datetime value

        """

        escalation_date = datetime.datetime.now().astimezone() - datetime.timedelta(days=days)
        LOGGER.info(f" calculate escalation threshold {days}: {escalation_date} ")
        return escalation_date

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
