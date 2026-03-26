"""Handler for the /modify command."""

import io
import logging

from telegram import Update
from telegram.ext import ContextTypes

from src.config import BotConfig
from src.gemini.errors import ContentPolicyError, GeminiError
from src.gemini.modify import modify_image

logger = logging.getLogger(__name__)

_ERROR_NO_IMAGE = (
    "I need an image to modify. Please attach a photo or reply to one."
)
_ERROR_NO_INSTRUCTION = (
    "Please describe what you'd like me to change. "
    "Example: /modify make the sky orange"
)
_ERROR_TOO_LARGE = "That image is too large. Please send a photo under 10 MB."
_ERROR_POLICY = (
    "I wasn't able to apply that change. Please try a different instruction."
)
_ERROR_GEMINI = "There was an issue with the Gemini API. Please try again in a moment."
_ACK = "Modifying your image\u2026"


async def modify_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /modify slash command."""
    if update.message is None:
        return

    config: BotConfig = context.bot_data["config"]
    client = context.bot_data["client"]

    # Resolve photo: direct attachment takes priority, then reply-to-message
    photo = None
    if update.message.photo:
        photo = update.message.photo[-1]
    elif (
        update.message.reply_to_message is not None
        and update.message.reply_to_message.photo
    ):
        photo = update.message.reply_to_message.photo[-1]

    if photo is None:
        await update.message.reply_text(_ERROR_NO_IMAGE)
        return

    # Extract instruction from caption (photo+caption) or text (reply scenario)
    raw_text: str = update.message.caption or update.message.text or ""
    instruction = raw_text.removeprefix("/modify").strip()

    if not instruction:
        await update.message.reply_text(_ERROR_NO_INSTRUCTION)
        return

    if photo.file_size and photo.file_size > config.max_image_size_bytes:
        await update.message.reply_text(_ERROR_TOO_LARGE)
        return

    tg_file = await photo.get_file()
    image_bytes = bytes(await tg_file.download_as_bytearray())

    await update.message.reply_text(_ACK)

    try:
        modified_bytes = await modify_image(
            client=client,
            config=config,
            image_bytes=image_bytes,
            instruction=instruction,
        )
        await update.message.reply_photo(photo=io.BytesIO(modified_bytes))
    except ContentPolicyError:
        logger.info("Content policy violation in /modify")
        await update.message.reply_text(_ERROR_POLICY)
    except GeminiError:
        logger.exception("Gemini error in /modify")
        await update.message.reply_text(_ERROR_GEMINI)
