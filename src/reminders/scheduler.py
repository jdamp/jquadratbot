"""Reminder scheduler: register the daily reminder job with PTB's JobQueue."""

import datetime
import logging
from typing import Any

from src.config import BotConfig
from src.reminders.config import ReminderConfig
from src.reminders.formatter import format_reminder_message
from src.reminders.parser import get_events_for_date, parse_ical

logger = logging.getLogger(__name__)


async def _reminder_job(context: Any) -> None:
    """Daily job callback: parse iCal, find tomorrow's events, send reminder."""
    config: ReminderConfig = context.bot_data["reminder_config"]
    events = parse_ical(config.ical_path)
    tomorrow = datetime.date.today() + datetime.timedelta(days=1)
    days_events = get_events_for_date(events, tomorrow)
    message = format_reminder_message(days_events, tomorrow)
    if message is not None:
        await context.bot.send_message(chat_id=config.chat_id, text=message)


def register(app: Any, _config: BotConfig) -> None:
    """Register the daily reminder job with the application's JobQueue.

    Silently skips (logs a warning) if REMINDER_ICAL_PATH or REMINDER_CHAT_ID
    are not configured, keeping all existing bot features unaffected.
    """
    try:
        reminder_config = ReminderConfig.from_env()
    except ValueError as exc:
        logger.warning("Reminder feature disabled: %s", exc)
        return

    if app.job_queue is None:
        logger.error("Job queue not available — reminder feature disabled")
        return

    app.bot_data["reminder_config"] = reminder_config
    app.job_queue.run_daily(
        _reminder_job,
        reminder_config.reminder_time,
    )
    logger.info(
        "Reminder job scheduled daily at %s %s for chat %s",
        reminder_config.reminder_time,
        reminder_config.timezone,
        reminder_config.chat_id,
    )
