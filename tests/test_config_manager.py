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

    def test_legacy_config_path_is_migrated_into_data_dir(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            data_dir = workspace / "data"
            data_dir.mkdir()
            legacy_config = workspace / "config.json"
            legacy_config.write_text(
                json.dumps(
                    {
                        "discord": {"token": "", "guild_id": "", "allowed_roles": "Admin"},
                        "features": {"enable_docker": True, "power_control_enabled": False, "power_control_password": ""},
                        "webui": {"enabled": True, "password": "legacy-password"},
                        "servers": [{"alias": "srv1", "host": "1.2.3.4", "user": "root", "port": 22, "auth_method": "key", "password": "", "key": ""}],
                    }
                ),
                encoding="utf-8",
            )

            env = {"SECRET_KEY": "z" * 32, "DATA_DIR": str(data_dir)}
            with patch.dict(os.environ, env, clear=False):
                current_dir = os.getcwd()
                os.chdir(workspace)
                try:
                    manager = ConfigManager()
                finally:
                    os.chdir(current_dir)

            self.assertEqual(manager.config.servers[0].alias, "srv1")
            self.assertTrue((data_dir / "config.json").exists())
            migrated = json.loads((data_dir / "config.json").read_text(encoding="utf-8"))
            self.assertTrue(migrated["webui"]["password"].startswith("PBKDF2_SHA256$"))

    def test_export_raw_config_returns_file_bytes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "config.json"
            env = {"SECRET_KEY": "x" * 32, "DATA_DIR": temp_dir}
            with patch.dict(os.environ, env, clear=False):
                manager = ConfigManager()

                # Write some distinct bytes directly to the file
                test_bytes = b'{"custom": "data", "id": 12345}'
                config_file.write_bytes(test_bytes)

                # export_raw_config should return the exact bytes from the file
                exported = manager.export_raw_config()
                self.assertEqual(exported, test_bytes)

    def test_export_raw_config_creates_file_if_missing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "config.json"
            env = {"SECRET_KEY": "x" * 32, "DATA_DIR": temp_dir}
            with patch.dict(os.environ, env, clear=False):
                manager = ConfigManager()

                # The file is created during ConfigManager init (save_config via migrate_from_env)
                self.assertTrue(config_file.exists())

                # Delete the file
                config_file.unlink()
                self.assertFalse(config_file.exists())

                # Exporting should recreate it and return its new bytes
                exported = manager.export_raw_config()
                self.assertTrue(config_file.exists())
                self.assertEqual(exported, config_file.read_bytes())

                # Verify it contains valid JSON and expected structure
                exported_data = json.loads(exported)
                self.assertIn("features", exported_data)
                self.assertIn("webui", exported_data)


if __name__ == "__main__":
    unittest.main()
