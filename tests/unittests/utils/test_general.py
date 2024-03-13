import json

from src.utils.general import render_jira_config, get_file_contents
from tests.unittests.conftest import DEFAULT_JIRA_SERVER_URL


def test_get_file_contents(tmp_path_factory, jira_token_path, jira_token):
    assert get_file_contents(file_path=jira_token_path) == jira_token


def test_render_jira_config(tmp_path_factory):
    tmp_dir = tmp_path_factory.mktemp("jira_config")
    test_output_file = render_jira_config(
        server_url=DEFAULT_JIRA_SERVER_URL, token="some-token", output_file=str(tmp_dir / "jira_config.json")
    )

    with open(test_output_file, "r") as file:
        output = json.load(file)
        assert output["url"] == DEFAULT_JIRA_SERVER_URL
        assert output["token"] == "some-token"
