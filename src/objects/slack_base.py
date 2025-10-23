import os
from typing import Optional
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from simple_logger.logger import get_logger

LOGGER = get_logger(name=__name__)


class SlackClient:
    """
    A client for interacting with the Slack API.
    Attributes:
        client (WebClient): An instance of the Slack WebClient initialized with the slack bot token
    """

    def __init__(self, token: str) -> None:
        """
        Constructs the slack object  with the provided slack bot token

        Args:
            token (str. optional): slack bot token , if not provided it defaults to SLACK_BOT_TOKEN environment variable.
        """
        self.logger = LOGGER

        self.token = os.getenv("SLACK_BOT_TOKEN") if token is None else token

        if self.token is None:
            raise ValueError("A bot token must be provided or set in the 'SLACK_BOT_TOKEN ' environment variable")
        self.client = WebClient(token=self.token)

    def get_slack_username(self, email: str) -> Optional[str]:
        """
        Look up a slack user by their email address.

        Args:
          email (str): Email of the slack user to look up

        Returns:
          str: A string containing user information if found, else None.
        """
        try:
            response = self.client.users_lookupByEmail(email=email)
            user = response["user"]
            return user["profile"]["display_name"]
        except SlackApiError as e:
            LOGGER.error(f"Error looking up user {e.response['error']}")
            return None

    def send_notification(self, channel: str, text: str) -> None:
        """
        Posts a message to specified slack channel

        Args:
         channel (str): channel to post slack message
         text (str): message text to post

        Raises:
          SlackApiError: if an error occurs while sending the message
        """
        try:
            LOGGER.info(f"attempting to send slack message in channel #{channel}: {text}")
            self.client.chat_postMessage(channel=channel, text=text)

        except SlackApiError as e:
            LOGGER.error(f"Error posting slack message: {e.response['error']}")

    def get_slack_usergroup(self, group_name: str) -> Optional[str]:
        """
        Look up a slack usergroup by their group name.

        Args:
          group_name (str): string containing slack team handle or usergroup name

        Returns:
          Optional[str]: A string containing usergroup id  if found, else None.
        """
        try:
            response = self.client.usergroups_list()
            for group in response["usergroups"]:
                if group["name"] == group_name:
                    LOGGER.info(f"user group : {group['name']}")
                    usergroup_id = group["id"]
                    return usergroup_id
            LOGGER.info("\n Slack user group not found \n")
            return None
        except SlackApiError as e:
            LOGGER.error(f"Error looking up user {e.response['error']}")
            return None
