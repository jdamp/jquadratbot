"""Handler for the /interpret command."""

import logging

from telegram import Update
from telegram.ext import ContextTypes

from src.config import BotConfig
from src.context import get_or_create_session, reset_session
from src.gemini.errors import GeminiError
from src.gemini.interpret import interpret_image

logger = logging.getLogger(__name__)

_ERROR_NO_IMAGE = (
    "I need an image to work with. Please attach a photo and try again, "
    "or send a follow-up question if you already shared an image in this session."
)
_ERROR_TOO_LARGE = "That image is too large. Please send a photo under 10 MB."
_ERROR_EXPIRED = (
    "Your previous conversation has expired due to inactivity. "
    "Please re-share the image if you'd like to continue."
)
_ERROR_GEMINI = "There was an issue with the Gemini API. Please try again in a moment."
_ACK = "Analysing your image\u2026"


async def interpret_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /interpret slash command."""
    if update.message is None or update.effective_chat is None:
        return

    config: BotConfig = context.bot_data["config"]
    client = context.bot_data["client"]
    chat_id = update.effective_chat.id

    session = get_or_create_session(chat_id)

    # Check session expiry when relying on context (no new image attached)
    has_photo = bool(update.message.photo)

    if not has_photo and session.is_expired(config.session_timeout_minutes):
        reset_session(chat_id)
        await update.message.reply_text(_ERROR_EXPIRED)
        return

    # Extract question: caption for photo messages, text for text-only messages
    raw_text: str = update.message.caption or update.message.text or ""
    # Strip the /interpret command prefix
    question = raw_text.removeprefix("/interpret").strip() or None

    image_bytes: bytes | None = None

    if has_photo:
        photo = update.message.photo[-1]

        if photo.file_size and photo.file_size > config.max_image_size_bytes:
            await update.message.reply_text(_ERROR_TOO_LARGE)
            return

        tg_file = await photo.get_file()
        image_bytes = bytes(await tg_file.download_as_bytearray())
    else:
        # Text-only follow-up: must have an active session with history
        if not session.history:
            await update.message.reply_text(_ERROR_NO_IMAGE)
            return

    await update.message.reply_text(_ACK)

    try:
        result = await interpret_image(
            client=client,
            config=config,
            session=session,
            image_bytes=image_bytes,
            question=question,
        )
        await update.message.reply_text(result)
    except GeminiError:
        logger.exception("Gemini error in /interpret")
        await update.message.reply_text(_ERROR_GEMINI)
