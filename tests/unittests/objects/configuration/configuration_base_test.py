import unittest
from unittest.mock import MagicMock
from unittest.mock import patch


class ConfigurationBaseTest(unittest.TestCase):
    @patch("src.objects.configuration.Jira")
    def setUp(self, mock_jira):
        self.mock_jira = mock_jira
        mock_jira.return_value = MagicMock()

    def tearDown(self):
        patch.stopall()
