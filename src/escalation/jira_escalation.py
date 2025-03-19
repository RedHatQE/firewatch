import datetime
from pathlib import Path
from typing import Optional

# import click
# from jinja2 import Environment
# from jinja2 import FileSystemLoader
from simple_logger.logger import get_logger

# from src.escalation.send_slack_notification import send_slack_notification
from src.objects.jira_base import Jira
from src.objects.slack_base import SlackClient

from simple_logger.logger import get_logger

LOGGER = get_logger(name=__name__)

class Jira_Escalation:
    """
    """
    def __init__(self,
                 jira: Jira,
                 slack_client: SlackClient,
                 slack_channel: str,
                 default_labels: list[str],
                 additional_labels: list[str],
                 default_jira_project: str):
        

        self.default_labels = default_labels
        self.additional_labels = additional_labels
        self.default_project = default_jira_project
        self.slack_client = slack_client
        self.jira = jira

        #build query and process ocp lp firewatch tickets in NOACK and ACK status
        jira_query = ""
        for status in ["NO ACK", "ACK"]:
            if default_jira_project:
                jira_query = self.build_jql(status)
            jira_query = self.build_jql(status)
            
            LOGGER.info(f" jira-query: {jira_query}")         
        
            self.process_issues(jira_query,slack_channel)

        #process PQE tickets
        pqe_jira_query = f"Project != {default_jira_project} AND status not in('Resolved','Blocked','Closed','Backlog','Done')"
        
        if self.additional_labels:
            formatted_additional_labels = '","'.join(self.additional_labels)
            LOGGER.info(f" add labels {formatted_additional_labels}")
            pqe_jira_query += f' AND (labels IN("{formatted_additional_labels}"))'

        if self.default_labels:
          default_condition = ' AND'.join([f'labels = "{label}"' for label in self.default_labels])
          pqe_jira_query += f' AND ({default_condition})'
        
        LOGGER.info(f" jira query PQE tickets: {pqe_jira_query}")
        self.process_issues(pqe_jira_query,slack_channel)


    def process_issues(self,jira_query: str,slack_channel:str)-> None:
        """
        """


        issues_list = self.jira.search_issues(jql_query=jira_query)
        LOGGER.info(f" Jira issues: {issues_list}")
        # LOGGER.info(f"-------------------------Jira Issues----------------------------")
        # test_email = ""
        for issue in issues_list:

            jira_issue = self.jira.get_issue_by_id_or_key_with_changelog(issue)
            
            # LOGGER.info(f" ---------------jira issue: {jira_issue.key}--- Status : {jira_issue.fields.status.name}  ---------------")

            if jira_issue.fields.assignee is None:
                LOGGER.info(f" No assignee found for this jira issue : {jira_issue.key}") #to do : send notification in slack to mpiit team for followup
                message = f"No assignee found for this jira issue : {jira_issue.key}, please provide an update"
                # self.send_slack_notification(self.slack_client,test_email,slack_channel,message) uncomment this for testing
                self.send_slack_notification(self.slack_client,assignee_email,slack_channel,message) #comment this for testing

                continue

            status_changed_date = None

            if jira_issue.fields.status.name == "ACK":
                change_log = jira_issue.changelog
                status_changed_date = None
                for history in change_log.histories:
                    for item in history.items:
                        # LOGGER.info(f" item: {item.field}")
                        if item.field == "status":
                            status_changed_date = datetime.datetime.strptime(history.created, '%Y-%m-%dT%H:%M:%S.%f%z')
                            # LOGGER.info(f"status_changed_date: {status_changed_date}")
                        break
                    if status_changed_date:
                        break
            
            comments = jira_issue.fields.comment.comments
           
            updated_date = datetime.datetime.strptime(jira_issue.fields.updated, '%Y-%m-%dT%H:%M:%S.%f%z')


            assignee = jira_issue.fields.assignee
            assignee_email = assignee.emailAddress
            assignee_comment_created_date = None
            last_updated_time = None

            # check if issue is updated within escalation threshold

            for comment in comments:
                if comment.author.emailAddress == assignee.emailAddress:
                    assignee_comment_created_date = datetime.datetime.strptime(comment.created,'%Y-%m-%dT%H:%M:%S.%f%z')

            if assignee_comment_created_date:
                last_updated_time = assignee_comment_created_date
            elif status_changed_date:
                last_updated_time = status_changed_date
            else:
                last_updated_time = updated_date    

            LOGGER.info(f" last update: {last_updated_time}")

            if last_updated_time <= self.escalation_threshold(3) :
                            
                LOGGER.info(f" 3 or more days since last comment")
                message = f"3 or more days since last comment, please provide an update on issue : https://issues.stage.redhat.com/browse/{jira_issue.key}"
                
                # self.send_slack_notification(self.slack_client,test_email,slack_channel,message) uncomment this for testing
                self.send_slack_notification(self.slack_client,assignee_email,slack_channel,message) #comment this for testing

            elif  last_updated_time <= self.escalation_threshold(2):
                LOGGER.info(f" 2 or more days since last comment")
                LOGGER.info(f"send slack message")
                message = f"2 or more days since last comment,please provide an update on issue {jira_issue.key}"
                # self.send_slack_notification(self.slack_client,test_email,slack_channel,message) uncomment this for testing
                self.send_slack_notification(self.slack_client,assignee_email,slack_channel,message) #comment this for testing
                            

            elif last_updated_time <= self.escalation_threshold(1):
                LOGGER.info(f" 1 or more days since last comment,add comment on the issue: {jira_issue.key}")
                comment = f"[~{jira_issue.fields.assignee.name}], please provide update for this issue(test comment please ignore) ."
                LOGGER.info(f"{comment}")
                self.jira.comment(jira_issue,comment)


    def build_jql(
            self,
            status: str,
            )-> str:
        """
        Build JQL query string
        Args:
            status (str): status of the issues
            project (str): Jira project
            default_labels (list(str)): labels to filter jira tickets
            additional_labels (list(str)) additional labels
        
        Returns:
            jql_query (str): jira query string
        """
        

        if self.default_project is not None:
            jql_query = f'Project = {self.default_project} AND status in("{status}") ' 
        else:

            jql_query = f'status in("{status}") '
        
        LOGGER.info(f" jql querry : {jql_query}")
        

        if self.additional_labels:
            formatted_additional_labels = '","'.join(self.additional_labels)
            LOGGER.info(f" add labels {formatted_additional_labels}")
            jql_query += f' AND (labels IN("{formatted_additional_labels}"))'

        if self.default_labels:
            formatted_default_labels = '","'.join(self.default_labels)
            default_condition = ' AND'.join([f'labels = "{label}"' for label in self.default_labels])
            jql_query += f' AND ({default_condition})'

        
        return jql_query  

    def escalation_threshold(self,days: int) -> datetime.datetime:
        """
        function to calculate escalation period based on days provide from current date
        
        Args:
            days (int): number of days

        Returns:
            escalation_date (datetime.datetime): threshold datetime value
            
        """

        escalation_date = datetime.datetime.now().astimezone() - datetime.timedelta(days=days)
        # LOGGER.info(f" calculate escalation threshold {days}: {escalation_date} ")
        return escalation_date
    
    def send_slack_notification(self,slack_client: SlackClient, email: str,slack_channel: str, message: str)-> None:
        """
        """
        user_display_name = slack_client.get_slack_username(email)
        message = f"<@{user_display_name}> \n {message} \n cc: {user_display_name}"
        slack_client.send_notification(channel=slack_channel,text=message)