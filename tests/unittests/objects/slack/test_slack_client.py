import pytest
from unittest.mock import MagicMock, patch
from slack_sdk.errors import SlackApiError
from slack_sdk import WebClient
from src.objects.slack_base import SlackClient


@pytest.fixture
def slack_client():
    """
    fixture to create slack client instance
    """
    return SlackClient(token="test-token")


@patch.object(WebClient, "users_lookupByEmail")
def test_get_slack_username_success(mock_users_lookup, slack_client):
    mock_users_lookup.return_value = {"user": {"profile": {"display_name": "test", "email": "test@example.com"}}}
    username = slack_client.get_slack_username("test@example.com")

    assert username == "test"
    mock_users_lookup.assert_called_once_with(email="test@example.com")


@patch.object(WebClient, "users_lookupByEmail")
def test_get_slack_username_failure(mock_users_lookup, slack_client):
    mock_users_lookup.side_effect = SlackApiError(
        "User not found", response=MagicMock(status=404, data={"error": "User not found"})
    )
    username = slack_client.get_slack_username("nonexistentemail@example.com")

    assert username is None
    mock_users_lookup.assert_called_once_with(email="nonexistentemail@example.com")


@patch.object(WebClient, "chat_postMessage")
def test_send_notification_success(mock_chat_post, slack_client):
    slack_client.send_notification("#test-channel", "test message")

    mock_chat_post.assert_called_once_with(channel="#test-channel", text="test message")


@patch.object(WebClient, "chat_postMessage")
def test_send_notification_failure(mock_chat_post, slack_client):
    mock_chat_post.side_effect = SlackApiError(
        "channel not found", response=MagicMock(status=404, sata={"error": "channel_not_found"})
    )

    slack_client.send_notification("#invalid-channel", "test message")

    mock_chat_post.assert_called_once_with(channel="#invalid-channel", text="test message")
