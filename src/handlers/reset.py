"""Handler for the /reset command."""

from telegram import Update
from telegram.ext import ContextTypes

from src.gemini.context import reset_session, sessions

_MSG_CLEARED = (
    "Conversation cleared. I've forgotten our previous images \u2014 start fresh anytime!"
)
_MSG_NOTHING = "There's nothing to clear \u2014 no active conversation in this chat."


async def reset_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /reset slash command."""
    if update.message is None or update.effective_chat is None:
        return

    chat_id = update.effective_chat.id
    had_session = chat_id in sessions
    reset_session(chat_id)

    await update.message.reply_text(_MSG_CLEARED if had_session else _MSG_NOTHING)
