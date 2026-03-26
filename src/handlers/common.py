"""Common handlers: /help, /start, unknown commands, and global error handler."""

import logging

from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

HELP_TEXT = """Here's what I can do:

/interpret [question] — Describe or answer questions about a photo
/generate <description> — Generate a new image from your description
/modify <instruction> — Edit an existing photo (attach it or reply to one)
/reset — Clear our conversation history
/help — Show this message"""


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start — welcome message + command list."""
    if update.message is None:
        return
    await update.message.reply_text(
        f"Hi! I'm a family image bot powered by Google Gemini.\n\n{HELP_TEXT}"
    )


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help — display available commands."""
    if update.message is None:
        return
    await update.message.reply_text(HELP_TEXT)


async def unknown_command_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle any unrecognised slash command."""
    if update.message is None:
        return
    await update.message.reply_text(f"I don't know that command.\n\n{HELP_TEXT}")


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log unexpected errors and notify the user if possible."""
    logger.error("Unhandled exception", exc_info=context.error)
    if isinstance(update, Update) and update.message is not None:
        await update.message.reply_text(
            "There was an issue with the Gemini API. Please try again in a moment."
        )
