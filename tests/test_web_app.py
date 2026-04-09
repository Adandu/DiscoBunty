import os
import tempfile
import unittest
from collections import deque
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from app_state import AppState, configure_logging
from config_manager import ConfigManager
from models import AppConfig
from web_app import create_web_app


class WebAppTests(unittest.TestCase):
    def _build_client(self):
        temp_dir = tempfile.TemporaryDirectory()
        env = {"SECRET_KEY": "z" * 32, "DATA_DIR": temp_dir.name}
        patcher = patch.dict(os.environ, env, clear=False)
        patcher.start()

        log_buffer = deque(maxlen=500)
        state = AppState(
            config_manager=ConfigManager(),
            logger=configure_logging(log_buffer),
            data_dir=Path(temp_dir.name),
            log_buffer=log_buffer,
        )
        config = AppConfig.model_validate(state.config.model_dump())
        config.webui.password = "admin-pass"
        state.save_config(config)
        client = TestClient(create_web_app(state))
        return temp_dir, patcher, client

    def test_login_and_health_flow(self):
        temp_dir, patcher, client = self._build_client()
        try:
            login_page = client.get("/login")
            self.assertEqual(login_page.status_code, 200)
            csrf_token = login_page.text.split('name="csrf_token" value="', 1)[1].split('"', 1)[0]

            response = client.post(
                "/login",
                data={"password": "admin-pass", "csrf_token": csrf_token},
                follow_redirects=False,
            )
            self.assertEqual(response.status_code, 303)

            home = client.get("/")
            self.assertEqual(home.status_code, 200)

            health = client.get("/health")
            self.assertEqual(health.status_code, 200)
            self.assertEqual(health.json()["status"], "ok")
        finally:
            client.close()
            patcher.stop()
            temp_dir.cleanup()


if __name__ == "__main__":
    unittest.main()
