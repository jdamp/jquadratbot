# Quickstart: iCalendar Event Reminders

**Feature**: 002-ical-reminders
**Date**: 2026-03-26

---

## What this feature adds

The bot will automatically send a Telegram message to a configured chat every day at a set time (default 18:00) if there are events scheduled for the following day in a provided iCalendar file.

---

## Setup

### 1. Add new environment variables

Add the following to your `.env` file (alongside the existing `TELEGRAM_TOKEN`, `GEMINI_API_KEY`, etc.):

```dotenv
# Path to the iCalendar (.ics) file
REMINDER_ICAL_PATH=/path/to/your/calendar.ics

# Telegram chat ID to send reminders to (integer, negative for groups)
REMINDER_CHAT_ID=-1001234567890

# Optional: time to send reminder each day (HH:MM, 24-hour, default: 18:00)
REMINDER_TIME=18:00

# Optional: IANA timezone name (default: Europe/Berlin)
REMINDER_TIMEZONE=Europe/Berlin
```

### 2. Install new dependencies

```bash
uv add icalendar>=6.0 python-dateutil>=2.9
```

### 3. Run the bot

```bash
uv run python -m src.bot
```

The bot will log a confirmation line when the reminder job is registered, e.g.:
```
INFO - Reminder job scheduled daily at 18:00 Europe/Berlin for chat -1001234567890
```

---

## How it works

- Every day at `REMINDER_TIME` (in `REMINDER_TIMEZONE`), the bot reads the iCal file.
- It expands all recurring events (RRULE, RDATE, EXDATE) to find events scheduled for tomorrow.
- If any events exist, a single message is sent to `REMINDER_CHAT_ID`.
- If the iCal file is missing or unreadable, the error is logged and no message is sent; all other bot features continue working.

---

## Running tests

```bash
uv run pytest tests/reminders/ -v
```

---

## Disabling the reminder feature

If `REMINDER_ICAL_PATH` or `REMINDER_CHAT_ID` are not set, the reminder feature is skipped entirely at startup and a warning is logged. No other functionality is affected.
