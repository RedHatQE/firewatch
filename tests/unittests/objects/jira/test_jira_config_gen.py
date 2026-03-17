import json

import pytest

from src.jira_config_gen.jira_config_gen import JiraConfig
from tests.unittests.conftest import DEFAULT_JIRA_SERVER_URL


@pytest.fixture
def template_path():
    from pathlib import Path

    return (Path(__file__).parents[4] / "src" / "templates" / "jira.config.j2").as_posix()


@pytest.fixture
def token_file(tmp_path):
    path = tmp_path / "token"
    path.write_text("fake-api-token")
    return path.as_posix()


class TestRenderTemplateEmail:
    def test_rendered_config_includes_email_when_provided(self, tmp_path, template_path, token_file):
        output = (tmp_path / "config.json").as_posix()
        config = JiraConfig(
            server_url=DEFAULT_JIRA_SERVER_URL,
            token_path=token_file,
            email="user@redhat.com",
            output_file=output,
            template_path=template_path,
        )

        with open(config.config_file_path) as f:
            rendered = json.load(f)

        assert rendered["email"] == "user@redhat.com"
        assert rendered["token"] == "fake-api-token"

    def test_rendered_config_omits_email_when_not_provided(self, tmp_path, template_path, token_file):
        output = (tmp_path / "config.json").as_posix()
        config = JiraConfig(
            server_url=DEFAULT_JIRA_SERVER_URL,
            token_path=token_file,
            output_file=output,
            template_path=template_path,
        )

        with open(config.config_file_path) as f:
            rendered = json.load(f)

        assert "email" not in rendered
        assert rendered["token"] == "fake-api-token"
