import asyncio
import os
from collections import deque
from pathlib import Path

from dotenv import load_dotenv
import uvicorn

from app_state import AppState, configure_logging
from bot_app import create_bot
from config_manager import ConfigManager
from web_app import create_web_app


async def main() -> None:
    load_dotenv()

    data_dir = Path(os.getenv("DATA_DIR", "data"))
    data_dir.mkdir(parents=True, exist_ok=True)
    log_buffer = deque(maxlen=500)

    state = AppState(
        config_manager=ConfigManager(),
        logger=configure_logging(log_buffer),
        data_dir=data_dir,
        log_buffer=log_buffer,
    )
    bot = create_bot(state)
    app = create_web_app(state)

    tasks = []
    if state.config.discord.token:
        tasks.append(bot.start(state.config.discord.token))
    if state.config.webui.enabled:
        tasks.append(
            uvicorn.Server(
                uvicorn.Config(
                    app,
                    host="0.0.0.0",
                    port=8000,
                    log_level="info",
                    proxy_headers=True,
                    forwarded_allow_ips=os.getenv("TRUSTED_PROXY_IPS", "127.0.0.1"),
                )
            ).serve()
        )

    if tasks:
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for result in results:
            if isinstance(result, Exception):
                state.logger.exception("DiscoBunty service exited with an exception", exc_info=result)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
