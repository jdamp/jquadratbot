"""Bot entry point: ApplicationBuilder setup and handler registration."""

import logging

from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

from src.config import BotConfig
from src.gemini.client import create_client
from src.handlers.common import (
    error_handler,
    help_handler,
    start_handler,
    unknown_command_handler,
)
from src.handlers.generate import generate_handler
from src.handlers.interpret import interpret_handler
from src.handlers.modify import modify_handler
from src.handlers.reset import reset_handler

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def main() -> None:
    config = BotConfig.from_env()
    client = create_client(config)

    app = ApplicationBuilder().token(config.telegram_token).build()

    # Store config and client in bot_data for handlers to access
    app.bot_data["config"] = config
    app.bot_data["client"] = client

    # Common handlers
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("help", help_handler))
    app.add_handler(CommandHandler("interpret", interpret_handler))
    app.add_handler(CommandHandler("reset", reset_handler))
    app.add_handler(CommandHandler("generate", generate_handler))
    app.add_handler(CommandHandler("modify", modify_handler))

    # Unknown slash commands (must come after all CommandHandlers)
    app.add_handler(MessageHandler(filters.COMMAND, unknown_command_handler))

    # Global error handler
    app.add_error_handler(error_handler)

    logger.info("Bot starting — polling for updates…")
    app.run_polling()


if __name__ == "__main__":
    main()
