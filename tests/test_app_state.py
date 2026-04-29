import unittest
import logging
import tempfile
from pathlib import Path
from unittest.mock import MagicMock
from app_state import AppState
from config_manager import ConfigManager
from models import AppConfig, DiscordSettings, WebUISettings, FeatureSettings, ServerSettings

class TestAppState(unittest.TestCase):
    def test_masked_config_dict(self):
        config_manager_mock = MagicMock(spec=ConfigManager)

        discord_settings = DiscordSettings(token="supersecrettoken")
        webui_settings = WebUISettings(password="webuisecret")
        feature_settings = FeatureSettings(power_control_password="powersecret")
        server1 = ServerSettings(alias="server1", host="localhost", password="server1secret")
        server2 = ServerSettings(alias="server2", host="localhost", key="/path/to/key")
        server3 = ServerSettings(alias="server3", host="localhost", key="nonexistent_key")

        config = AppConfig(
            discord=discord_settings,
            webui=webui_settings,
            features=feature_settings,
            servers=[server1, server2, server3]
        )

        config_manager_mock.config = config

        logger_mock = MagicMock(spec=logging.Logger)

        with tempfile.TemporaryDirectory() as temp_dir:
            app_state = AppState(
                config_manager=config_manager_mock,
                logger=logger_mock,
                data_dir=Path(temp_dir)
            )

            masked_dict = app_state.masked_config_dict()

            self.assertEqual(masked_dict["discord"]["token"], "********")
            self.assertEqual(masked_dict["webui"]["password"], "********")
            self.assertEqual(masked_dict["features"]["power_control_password"], "********")
            self.assertEqual(masked_dict["servers"][0]["password"], "********")
            self.assertEqual(masked_dict["servers"][1]["key"], "/path/to/key")
            self.assertEqual(masked_dict["servers"][2]["key"], "********")

if __name__ == '__main__':
    unittest.main()
