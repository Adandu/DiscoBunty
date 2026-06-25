import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from main import main


class TestMain(unittest.IsolatedAsyncioTestCase):
    @patch("main.load_dotenv")
    @patch("main.uvicorn.Server.serve", new_callable=AsyncMock)
    @patch("main.uvicorn.Config")
    @patch("main.create_web_app")
    @patch("main.create_bot")
    @patch("main.ConfigManager")
    @patch("main.configure_logging")
    @patch("main.AppState")
    @patch("main.Path.mkdir")
    @patch("os.getenv")
    async def test_main_starts_both_services(
        self,
        mock_getenv,
        mock_mkdir,
        mock_app_state,
        mock_configure_logging,
        mock_config_manager,
        mock_create_bot,
        mock_create_web_app,
        mock_uvicorn_config,
        mock_uvicorn_serve,
        mock_load_dotenv,
    ):
        mock_getenv.side_effect = lambda key, default=None: "127.0.0.1" if key == "TRUSTED_PROXY_IPS" else ("dummy_data_dir" if key == "DATA_DIR" else default)

        # Setup state mock
        state_instance = MagicMock()
        state_instance.config.discord.token = "fake_token"
        state_instance.config.webui.enabled = True
        mock_app_state.return_value = state_instance

        # Setup bot mock
        bot_instance = MagicMock()
        bot_instance.start = AsyncMock()
        mock_create_bot.return_value = bot_instance

        # Setup web app mock
        app_instance = MagicMock()
        mock_create_web_app.return_value = app_instance

        # Run main
        await main()

        # Assertions
        mock_load_dotenv.assert_called_once()
        mock_mkdir.assert_called_once()
        mock_app_state.assert_called_once()
        mock_create_bot.assert_called_once_with(state_instance)
        mock_create_web_app.assert_called_once_with(state_instance)

        bot_instance.start.assert_awaited_once_with("fake_token")
        mock_uvicorn_config.assert_called_once_with(
            app_instance,
            host="0.0.0.0",
            port=8000,
            log_level="info",
            proxy_headers=True,
            forwarded_allow_ips="127.0.0.1",
        )
        mock_uvicorn_serve.assert_awaited_once()

    @patch("main.load_dotenv")
    @patch("main.create_web_app")
    @patch("main.create_bot")
    @patch("main.ConfigManager")
    @patch("main.configure_logging")
    @patch("main.AppState")
    @patch("main.Path.mkdir")
    async def test_main_starts_neither_service(
        self,
        mock_mkdir,
        mock_app_state,
        mock_configure_logging,
        mock_config_manager,
        mock_create_bot,
        mock_create_web_app,
        mock_load_dotenv,
    ):
        state_instance = MagicMock()
        state_instance.config.discord.token = ""
        state_instance.config.webui.enabled = False
        mock_app_state.return_value = state_instance

        bot_instance = MagicMock()
        bot_instance.start = AsyncMock()
        mock_create_bot.return_value = bot_instance

        await main()

        bot_instance.start.assert_not_called()

    @patch("main.load_dotenv")
    @patch("main.uvicorn.Server.serve", new_callable=AsyncMock)
    @patch("main.uvicorn.Config")
    @patch("main.create_web_app")
    @patch("main.create_bot")
    @patch("main.ConfigManager")
    @patch("main.configure_logging")
    @patch("main.AppState")
    @patch("main.Path.mkdir")
    async def test_main_handles_exception(
        self,
        mock_mkdir,
        mock_app_state,
        mock_configure_logging,
        mock_config_manager,
        mock_create_bot,
        mock_create_web_app,
        mock_uvicorn_config,
        mock_uvicorn_serve,
        mock_load_dotenv,
    ):
        state_instance = MagicMock()
        state_instance.config.discord.token = "fake_token"
        state_instance.config.webui.enabled = False
        mock_app_state.return_value = state_instance

        bot_instance = MagicMock()
        test_exception = Exception("Test Exception")
        bot_instance.start = AsyncMock(side_effect=test_exception)
        mock_create_bot.return_value = bot_instance

        await main()

        state_instance.logger.exception.assert_called_once_with("DiscoBunty service exited with an exception", exc_info=test_exception)
