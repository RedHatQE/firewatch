import os
import tempfile
import unittest
from unittest.mock import MagicMock
from unittest.mock import patch

from cli.jira_config_gen.jira_config_gen import JiraConfig


class TestJiraConfig(unittest.TestCase):
    def setUp(self):
        self.mock_logger = patch("cli.objects.job.get_logger")
        self.mock_logger.start().return_value = MagicMock()
        self.template = """
                {
                    "token": "{{ token }}",
                    "url": "{{ server_url }}",
                    {% if "stage" in server_url %}
                    "proxies": {
                        "http": "http://squid.corp.redhat.com:3128",
                        "https": "http://squid.corp.redhat.com:3128"
                    }
                    {% endif %}
                }
                """

    def tearDown(self):
        patch.stopall()

    def test_jira_config_initializes_with_valid_input(self):
        with tempfile.TemporaryDirectory() as tmp_path:
            output_path = f"{tmp_path}/jira.config"
            token_path = f"{tmp_path}/TOKEN"
            template_path = f"{tmp_path}/jira.config.j2"
            with open(token_path, "w") as file:
                file.write("TEST_TOKEN")
            with open(template_path, "w") as file:
                file.write(str(self.template))

            config = JiraConfig(
                server_url="some-jira-url",
                token_path=token_path,
                output_file=output_path,
                template_path=template_path,
            )

            assert os.path.exists(config.config_file_path)
