# Research: iCalendar Event Reminders

**Feature**: 002-ical-reminders
**Date**: 2026-03-26

---

## Decision 1: iCalendar parsing library

**Decision**: Use the `icalendar` PyPI package for parsing `.ics` files, supplemented by `python-dateutil` for recurrence rule expansion.

**Rationale**: `icalendar` is the canonical Python library for reading RFC 5545 iCalendar data. It handles the full file structure (VCALENDAR, VEVENT, RRULE, RDATE, EXDATE) and exposes these as typed Python objects. `python-dateutil` provides `rrulestr` and `rruleset`, which correctly expand recurrence sequences including RDATE additions and EXDATE exclusions. Together they cover all recurrence patterns in the example iCal file (FREQ=WEEKLY with INTERVAL, BYDAY, UNTIL; RDATE; EXDATE).

**Alternatives considered**:
- `recurring_ical_events` — a higher-level wrapper over `icalendar` + `dateutil` that handles edge cases automatically. Rejected to minimise dependency surface; the patterns in the example file are well-handled by direct `icalendar` + `dateutil` usage.
- Custom parser — rejected; RFC 5545 has many edge cases (folded lines, VTIMEZONE, value types) that would require significant implementation effort.

---

## Decision 2: Scheduling mechanism

**Decision**: Use `python-telegram-bot`'s built-in `JobQueue` (`application.job_queue.run_daily()`), which is already available when the bot runs.

**Rationale**: `python-telegram-bot ≥ 21.0` bundles APScheduler via its `JobQueue`, providing `run_daily(callback, time)`. This handles time-zone-aware scheduling and fires a single callback daily at the specified time. No additional scheduler dependency is needed. The existing `bot.py` already initialises an `Application` through `ApplicationBuilder`, which creates a `JobQueue` by default.

**Alternatives considered**:
- External cron + separate script — rejected; adds operational complexity (two processes, coordination) and conflicts with the "continuous process" assumption in the spec.
- `asyncio` sleep loop — rejected; fragile, does not handle DST transitions or process restarts gracefully. `JobQueue` uses APScheduler which is robust.
- `apscheduler` directly — rejected; already provided transitively by `python-telegram-bot`; direct use would duplicate the dependency.

---

## Decision 3: Module architecture (open-closed principle)

**Decision**: Implement the reminder feature as a self-contained `src/reminders/` package. It exposes a single `register(app, config)` function. `bot.py` calls `register()` once during startup — the only change to existing code. Future features follow the same pattern.

**Rationale**: The open-closed principle requires that adding a new feature does not require modifying existing modules. By placing all reminder logic in `src/reminders/` and having `bot.py` call a single registration function, the existing handlers, Gemini client, and configuration are untouched. New extensions (e.g., weather reminders, birthday greetings) each get their own package and a single `register()` call in `bot.py`.

**Alternatives considered**:
- Monolithic `bot.py` extension — rejected; directly violates open-closed principle.
- Auto-discovery via entry points — rejected; adds complexity not justified by current scale (YAGNI per constitution Principle V).

---

## Decision 4: Timezone handling

**Decision**: Read reminder timezone from a new `REMINDER_TIMEZONE` environment variable; default to `"Europe/Berlin"` (a sensible default given the example file's German municipal context).

**Rationale**: The example iCal file is from a German municipal service. `python-telegram-bot`'s `run_daily()` accepts a `tzinfo` argument; `zoneinfo.ZoneInfo` (Python 3.9+ stdlib) provides correct DST handling without additional dependencies.

**Alternatives considered**:
- UTC only — rejected; a reminder at "18:00 local time" must fire at the correct wall-clock time regardless of DST.
- `pytz` — rejected; `zoneinfo` is in the stdlib since Python 3.9, and the project targets Python 3.14.

---

## Decision 5: Chat ID for reminder delivery

**Decision**: Introduce a new required environment variable `REMINDER_CHAT_ID` (integer). This is separate from the group where image commands are sent, since the spec assumption "same chat ID" may not always hold and an explicit config value is safer.

**Rationale**: Hard-coding or silently reusing the existing chat ID would be fragile. A dedicated env var is explicit, testable, and consistent with constitution Principle V (externalised configuration). If the operator wants to use the same chat, they simply set both to the same value.

**Alternatives considered**:
- Reuse a chat ID already in config — rejected; the existing `BotConfig` has no chat-ID field (the bot is multi-chat capable), so there is nothing to reuse.

---

## Decision 6: New dependencies to add

| Package | Version constraint | Rationale |
|---|---|---|
| `icalendar` | `>=6.0` | iCal file parsing |
| `python-dateutil` | `>=2.9` | RRULE/RDATE/EXDATE expansion |

`zoneinfo` is Python stdlib (3.9+); no extra package needed.

`python-dateutil` may already be a transitive dependency (many packages pull it in), but it will be pinned explicitly as a direct dependency for clarity.
