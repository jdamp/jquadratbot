# Implementation Plan: iCalendar Event Reminders

**Branch**: `002-ical-reminders` | **Date**: 2026-03-26 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/002-ical-reminders/spec.md`

## Summary

Add automated day-before event reminders to the Telegram bot by parsing a locally-stored iCalendar file (using the `icalendar` + `python-dateutil` libraries) and scheduling a daily notification via `python-telegram-bot`'s built-in `JobQueue`. The reminder module is implemented as a self-contained `src/reminders/` package that registers itself with a single function call in `bot.py`, leaving all existing functionality untouched (open-closed principle).

## Technical Context

**Language/Version**: Python 3.14
**Primary Dependencies**: `python-telegram-bot[job-queue] ≥ 21.0` (JobQueue/APScheduler), `icalendar ≥ 6.0`, `python-dateutil ≥ 2.9`, `zoneinfo` (stdlib)
**Storage**: Local filesystem (single `.ics` file, read-only, re-read on each daily job execution)
**Testing**: `pytest` with `pytest-asyncio`; unit tests for parser and formatter; integration test for full reminder flow
**Target Platform**: Linux server (continuous process)
**Project Type**: Telegram bot (service)
**Performance Goals**: Personal-scale; reminder must fire within 60 seconds of configured time
**Constraints**: Reminder module must not import from or modify any existing `src/` module except being called from `bot.py`; iCal file re-read on every job run (no caching required at personal scale)
**Scale/Scope**: Family chat (2–4 users); single iCal file; one daily job

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Code Quality — full type annotations, ruff, mypy --strict | PASS | All new code will carry type annotations; checked in CI |
| II. Testing — unit + integration, Red-Green-Refactor, ≥80% coverage | PASS | tests/reminders/ will cover parser, formatter, scheduler |
| III. UX Consistency — consistent voice, human-readable errors, ≤3s feedback | PASS | Reminder is a push notification (no interaction); error logged, not sent to user |
| IV. Performance — personal scale; no blocking of event loop | PASS | JobQueue callback is async; iCal file I/O is small |
| V. Simplicity — no speculative abstractions; externalised config | PASS | Single `register()` entry point; env-var config; YAGNI respected |
| Constitution: new runtime dependency requires rationale comment | PASS | `icalendar` and `python-dateutil` will have rationale comments in pyproject.toml |

**Post-design re-check**: No violations introduced. The `src/reminders/` package boundary is clean; no circular imports.

## Project Structure

### Documentation (this feature)

```text
specs/002-ical-reminders/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── reminder-message-format.md
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
src/
├── bot.py                        # MODIFIED: add register_reminders call (1 import + 1 line)
├── config.py                     # UNCHANGED
├── context.py                    # UNCHANGED
├── gemini/                       # UNCHANGED
│   └── …
├── handlers/                     # UNCHANGED
│   └── …
└── reminders/                    # NEW package
    ├── __init__.py               # Exports: register()
    ├── config.py                 # ReminderConfig.from_env()
    ├── parser.py                 # parse_ical(), get_events_for_date()
    ├── formatter.py              # format_reminder_message()
    └── scheduler.py              # register() — wires JobQueue job

tests/
├── …existing…
└── reminders/                    # NEW
    ├── __init__.py
    ├── fixtures/
    │   └── sample.ics            # Test iCal file with known events
    ├── test_parser.py            # Unit: parse_ical, get_events_for_date, RRULE/RDATE/EXDATE
    ├── test_formatter.py         # Unit: format_reminder_message (0, 1, N events)
    └── test_scheduler.py         # Integration: register() schedules job, job sends message
```

**Structure Decision**: Single-project layout (Option 1). The new `src/reminders/` package sits alongside `src/gemini/` and `src/handlers/`, consistent with the existing module structure. No new top-level directories.

## Complexity Tracking

No constitution violations. Table not required.
