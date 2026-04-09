import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from config_manager import ConfigManager
from models import AppConfig


class ConfigManagerTests(unittest.TestCase):
    def test_env_migration_hashes_passwords_and_normalizes_booleans(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            env = {
                "SECRET_KEY": "x" * 32,
                "DATA_DIR": temp_dir,
                "ENABLE_DOCKER": "true",
                "POWER_CONTROL_ENABLED": "false",
                "WEBUI_ENABLED": "true",
                "WEB_PASSWORD": "web-pass",
                "POWER_CONTROL_PASSWORD": "power-pass",
            }
            with patch.dict(os.environ, env, clear=False):
                manager = ConfigManager()

            self.assertTrue(manager.config.features.enable_docker)
            self.assertTrue(manager.config.webui.enabled)
            self.assertTrue(manager.config.webui.password.startswith("PBKDF2_SHA256$"))
            self.assertTrue(manager.config.features.power_control_password.startswith("PBKDF2_SHA256$"))

            saved = json.loads(Path(temp_dir, "config.json").read_text(encoding="utf-8"))
            self.assertTrue(saved["webui"]["password"].startswith("PBKDF2_SHA256$"))
            self.assertIsInstance(saved["features"]["enable_docker"], bool)

    def test_save_config_persists_typed_booleans(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            env = {"SECRET_KEY": "y" * 32, "DATA_DIR": temp_dir}
            with patch.dict(os.environ, env, clear=False):
                manager = ConfigManager()
                config = AppConfig.model_validate(manager.config.model_dump())
                config.features.enable_docker = True
                config.webui.enabled = False
                manager.save_config(config)

            saved = json.loads(Path(temp_dir, "config.json").read_text(encoding="utf-8"))
            self.assertTrue(saved["features"]["enable_docker"])
            self.assertFalse(saved["webui"]["enabled"])


if __name__ == "__main__":
    unittest.main()
