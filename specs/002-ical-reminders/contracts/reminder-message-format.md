# Contract: Reminder Message Format

**Feature**: 002-ical-reminders
**Date**: 2026-03-26

---

## Overview

The reminder subsystem sends a single Telegram message to the configured chat when one or more events are scheduled for the following calendar day.

---

## Message Contract

### When events exist for tomorrow

```
Reminder: tomorrow is [WEEKDAY], [DD]. [MONTH_NAME] [YYYY]

The following collections are scheduled:
• [SUMMARY 1]
• [SUMMARY 2]
```

**Rules**:
- Date line always uses the locale-independent format: weekday name (English), day number, full month name (English), 4-digit year.
- Each event appears on its own bullet line (`•` U+2022).
- Events are listed in their natural order from the iCal file; no sorting is applied.
- The message is plain text (no Markdown or HTML formatting); consistent with the existing bot's response style.

**Example** (two events):
```
Reminder: tomorrow is Monday, 20. April 2026

The following collections are scheduled:
• EB Glas-Tonne
• EB Gelber Sack
```

**Example** (one event):
```
Reminder: tomorrow is Wednesday, 01. April 2026

The following collections are scheduled:
• EB Gelber Sack
```

---

### When no events exist for tomorrow

No message is sent. Silence is the correct behaviour.

---

## Internal Module Interface Contract

The `src/reminders` package exposes exactly one public function used by `bot.py`:

```
register(app: telegram.ext.Application, config: src.config.BotConfig) -> None
```

- `app`: the fully-constructed `Application` instance (with an active `JobQueue`).
- `config`: the existing `BotConfig`; the reminder module reads its own `ReminderConfig` from env vars independently.
- Returns `None`; raises `SystemExit(1)` (via `sys.exit`) if `REMINDER_ICAL_PATH` or `REMINDER_CHAT_ID` are missing or invalid.
- Side effect: schedules a single `run_daily` job on `app.job_queue`.

**Calling convention in `bot.py`**:
```python
from src.reminders import register as register_reminders
register_reminders(app, config)
```

This is the **only** change to `bot.py`; no other existing file is modified.
