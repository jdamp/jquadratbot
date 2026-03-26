"""Reminder message formatter: converts CalendarEvent list to a Telegram message."""

import datetime

from src.reminders.parser import CalendarEvent


def format_reminder_message(
    events: list[CalendarEvent],
    tomorrow: datetime.date,
) -> str | None:
    """Format a day-before reminder message.

    Returns None when the events list is empty (no message should be sent).
    Returns a formatted plain-text string otherwise.

    Message format:
        Reminder: tomorrow is {Weekday}, {D}. {Month} {YYYY}

        The following collections are scheduled:
        • Event summary 1
        • Event summary 2
    """
    if not events:
        return None

    weekday = tomorrow.strftime("%A")
    day = tomorrow.day
    month = tomorrow.strftime("%B")
    year = tomorrow.year

    lines = [
        f"Reminder: tomorrow is {weekday}, {day}. {month} {year}",
        "",
        "The following collections are scheduled:",
    ]
    for event in events:
        lines.append(f"\u2022 {event.summary}")

    return "\n".join(lines)
