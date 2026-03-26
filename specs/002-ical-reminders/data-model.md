# Data Model: iCalendar Event Reminders

**Feature**: 002-ical-reminders
**Date**: 2026-03-26

---

## Entities

### CalendarEvent

Represents a single concrete occurrence of a calendar event on a specific date.

| Field | Type | Description |
|-------|------|-------------|
| `summary` | `str` | Human-readable event name (from VEVENT SUMMARY field). Falls back to `"Unnamed event"` if SUMMARY is absent. |
| `date` | `datetime.date` | The calendar date on which the event occurs. Derived from DTSTART (expanded for recurrences). |

**Validation rules**:
- `summary` is always a non-empty string (fallback applied at parse time).
- `date` is always a `datetime.date` (not `datetime.datetime`); all-day events only.

**Source**: Parsed from iCalendar VEVENT entries. One `CalendarEvent` is produced per concrete occurrence (i.e., a recurring event with 10 occurrences produces 10 `CalendarEvent` instances).

---

### ReminderConfig

Configuration for the reminder subsystem, loaded from environment variables.

| Field | Type | Source env var | Default |
|-------|------|----------------|---------|
| `ical_path` | `str` | `REMINDER_ICAL_PATH` | — (required) |
| `chat_id` | `int` | `REMINDER_CHAT_ID` | — (required) |
| `reminder_time` | `datetime.time` | `REMINDER_TIME` | `18:00` |
| `timezone` | `zoneinfo.ZoneInfo` | `REMINDER_TIMEZONE` | `Europe/Berlin` |

**Validation rules**:
- `ical_path` must be a non-empty string; file existence is validated at startup.
- `chat_id` must be a valid non-zero integer.
- `reminder_time` must parse as `HH:MM` (24-hour); invalid format raises `ValueError` at startup.
- `REMINDER_TIMEZONE` must be a valid IANA timezone name recognised by `zoneinfo`; invalid value raises `ValueError` at startup.

**Loading**: `ReminderConfig.from_env()` — mirrors the pattern in `src/config.py`.

---

## State Transitions

The reminder subsystem is stateless between runs. No persistence is required:

- On each daily job execution, the iCal file is re-read from disk.
- Events for "tomorrow" (relative to the job's execution time in the configured timezone) are computed fresh.
- No deduplication state is maintained; if the bot restarts mid-day, the reminder will fire again at the next scheduled time.

---

## Recurrence Expansion Algorithm

For each VEVENT in the parsed iCal file:

1. Read `DTSTART` as a `datetime.date`.
2. If RRULE is present: parse using `dateutil.rrule.rrulestr()` with `dtstart` set to `DTSTART`.
3. If RDATE is present: add extra dates to a `dateutil.rrule.rruleset`.
4. If EXDATE is present: add exclusion dates to the same `rruleset`.
5. Expand all occurrences in the window `[today, today + 365 days]`.
6. For each occurrence date that matches the target date (tomorrow): yield a `CalendarEvent`.

If no RRULE is present, only the single `DTSTART` date is checked against the target date.
