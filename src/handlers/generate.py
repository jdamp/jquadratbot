"""Handler for the /generate command."""

import io
import logging

from telegram import Update
from telegram.ext import ContextTypes

from src.config import BotConfig
from src.gemini.errors import ContentPolicyError, GeminiError
from src.gemini.generate import generate_image

logger = logging.getLogger(__name__)

_ERROR_NO_PROMPT = (
    "Please describe the image you'd like me to generate. "
    "Example: /generate a sunset over the mountains"
)
_ERROR_POLICY = (
    "I wasn't able to generate that image. Please try a different description."
)
_ERROR_GEMINI = "There was an issue with the Gemini API. Please try again in a moment."
_ACK = "Generating your image\u2026"


async def generate_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /generate slash command."""
    if update.message is None:
        return

    config: BotConfig = context.bot_data["config"]
    client = context.bot_data["client"]

    raw_text: str = update.message.text or ""
    prompt = raw_text.removeprefix("/generate").strip()

    if not prompt:
        await update.message.reply_text(_ERROR_NO_PROMPT)
        return

    await update.message.reply_text(_ACK)

    try:
        image_bytes = await generate_image(client=client, config=config, prompt=prompt)
        await update.message.reply_photo(photo=io.BytesIO(image_bytes))
    except ContentPolicyError:
        logger.info("Content policy violation in /generate")
        await update.message.reply_text(_ERROR_POLICY)
    except GeminiError:
        logger.exception("Gemini error in /generate")
        await update.message.reply_text(_ERROR_GEMINI)
