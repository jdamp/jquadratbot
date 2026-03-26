# Tasks: iCalendar Event Reminders

**Input**: Design documents from `/specs/002-ical-reminders/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅

**Tests**: Included per constitution Principle II (Red-Green-Refactor is NON-NEGOTIABLE).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Exact file paths included in every task description

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add new packages, directory scaffolding, and test fixtures before any implementation begins.

- [x] T001 Add `icalendar>=6.0` and `python-dateutil>=2.9` runtime dependencies with rationale comments to `pyproject.toml`
- [x] T002 [P] Add `mypy` ignore overrides for `icalendar` and `dateutil` modules in `pyproject.toml` (mirrors existing `telegram.*` / `google.*` overrides)
- [x] T003 [P] Create empty `src/reminders/__init__.py` and `tests/reminders/__init__.py` to establish package roots
- [x] T004 Create `tests/reminders/fixtures/sample.ics` containing: one non-recurring event, one RRULE weekly event, one RDATE extra occurrence, and one EXDATE excluded occurrence — all with known dates for deterministic test assertions

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core data structures shared by all user stories. Must be complete before any story phase begins.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [x] T005 Create `CalendarEvent` frozen dataclass (fields: `summary: str`, `date: datetime.date`) in `src/reminders/parser.py`
- [x] T006 Create `ReminderConfig` frozen dataclass with `from_env()` classmethod in `src/reminders/config.py`; validate `REMINDER_ICAL_PATH` (required, non-empty) and `REMINDER_CHAT_ID` (required, valid int); `REMINDER_TIMEZONE` defaults to `"Europe/Berlin"` using `zoneinfo.ZoneInfo`; `REMINDER_TIME` defaults to `datetime.time(18, 0)` — full validation with `ValueError` on bad input, `sys.exit(1)` on missing required vars

**Checkpoint**: Data model and config loading are ready — user story implementation can now begin.

---

## Phase 3: User Story 1 — Automated Day-Before Reminder (Priority: P1) 🎯 MVP

**Goal**: Bot sends a single Telegram message to the configured chat at the scheduled time when non-recurring events are scheduled for the following calendar day.

**Independent Test**: Provide `sample.ics` with a non-recurring event on a known date, trigger the job callback manually in a test, assert the correct message text is passed to `bot.send_message`.

### Tests for User Story 1 ⚠️ Write FIRST — confirm they FAIL before implementing

- [x] T007 [P] [US1] Write failing unit tests for `format_reminder_message()` in `tests/reminders/test_formatter.py`: test zero events → `None`, one event → correct message text, multiple events → all summaries listed, fallback summary for event with no SUMMARY field
- [x] T008 [P] [US1] Write failing unit tests for `parse_ical()` and `get_events_for_date()` (non-recurring only) in `tests/reminders/test_parser.py`: single event matching target date, single event on different date returns empty, missing SUMMARY falls back to `"Unnamed event"`, unreadable file path returns empty list with a logged warning
- [x] T009 [US1] Write failing integration test for `register()` in `tests/reminders/test_scheduler.py`: mock `Application.job_queue.run_daily`, assert it is called once with the correct time and timezone; mock `bot.send_message`, trigger the job callback with an iCal file containing a tomorrow event, assert `send_message` is called with the formatted text

### Implementation for User Story 1

- [x] T010 [P] [US1] Implement `format_reminder_message(events: list[CalendarEvent], tomorrow: datetime.date) -> str | None` in `src/reminders/formatter.py` — returns `None` when list is empty; builds message per `contracts/reminder-message-format.md`
- [x] T011 [P] [US1] Implement `parse_ical(path: str) -> list[CalendarEvent]` and `get_events_for_date(events: list[CalendarEvent], date: datetime.date) -> list[CalendarEvent]` in `src/reminders/parser.py` for non-recurring events only; log warning and return `[]` if file is missing or unparseable
- [x] T012 [US1] Implement `async def _reminder_job(context: ContextTypes.DEFAULT_TYPE) -> None` in `src/reminders/scheduler.py`: reads `ReminderConfig` stored in `context.bot_data`, calls `parse_ical`, `get_events_for_date`, `format_reminder_message`, sends message if not `None` (depends on T010, T011)
- [x] T013 [US1] Implement `register(app: Application, config: BotConfig) -> None` in `src/reminders/scheduler.py`: loads `ReminderConfig.from_env()`, stores it in `app.bot_data["reminder_config"]`, registers `_reminder_job` via `app.job_queue.run_daily()`; export `register` from `src/reminders/__init__.py` (depends on T012)
- [x] T014 [US1] Update `src/bot.py`: add `from src.reminders import register as register_reminders` import and call `register_reminders(app, config)` after existing handler registration (depends on T013) — this is the only change to existing code

**Checkpoint**: US1 fully functional — run `tests/reminders/test_formatter.py`, `test_parser.py`, `test_scheduler.py` and verify all pass. Bot sends reminders for non-recurring events.

---

## Phase 4: User Story 2 — Recurring Event Support (Priority: P2)

**Goal**: Parser correctly expands RRULE, RDATE, and EXDATE to find all concrete occurrence dates; reminders fire on every real occurrence and are suppressed on excluded ones.

**Independent Test**: Using `sample.ics` (created in T004), assert that recurrence occurrences appear exactly as expected over a 4-week window, RDATE additions appear, and EXDATE exclusions are absent — all via `get_events_for_date()`.

### Tests for User Story 2 ⚠️ Write FIRST — confirm they FAIL before implementing

- [x] T015 [US2] Write failing unit tests for recurrence expansion in `tests/reminders/test_parser.py`: RRULE weekly event appears on all expected dates over 4 weeks; RRULE event with UNTIL does not appear after UNTIL date; RDATE extra date appears; EXDATE excluded date does not appear; combination of RRULE + RDATE + EXDATE from `sample.ics` matches exact expected occurrence list

### Implementation for User Story 2

- [x] T016 [US2] Extend `parse_ical()` in `src/reminders/parser.py` to detect RRULE on a VEVENT and use `dateutil.rrule.rrulestr()` with `dtstart` to expand occurrences into a `dateutil.rrule.rruleset` within a rolling `[today, today + 365 days]` window; yield one `CalendarEvent` per occurrence date (depends on T015)
- [x] T017 [US2] Extend `parse_ical()` in `src/reminders/parser.py` to add RDATE dates to the `rruleset` via `rruleset.rdate()` when RDATE is present on the VEVENT (depends on T016)
- [x] T018 [US2] Extend `parse_ical()` in `src/reminders/parser.py` to exclude EXDATE dates from the `rruleset` via `rruleset.exdate()` when EXDATE is present on the VEVENT (depends on T017)

**Checkpoint**: US2 complete — all test cases in T015 pass. Both recurring and non-recurring events are handled correctly end-to-end.

---

## Phase 5: User Story 3 — Configurable Reminder Time (Priority: P3)

**Goal**: Operator can set `REMINDER_TIME=HH:MM` in the environment to change the daily reminder firing time without touching code; the default of `18:00` applies when unset.

**Independent Test**: Set `REMINDER_TIME=08:00` in the test environment, construct `ReminderConfig.from_env()`, assert `config.reminder_time == datetime.time(8, 0)`; assert `run_daily` is called with this time. Separately assert unset env var yields `datetime.time(18, 0)`.

### Tests for User Story 3 ⚠️ Write FIRST — confirm they FAIL before implementing

- [x] T019 [P] [US3] Write failing unit tests for `REMINDER_TIME` parsing in `tests/reminders/test_scheduler.py` (or a dedicated `tests/reminders/test_config.py`): valid `"08:00"` → `datetime.time(8, 0)`; valid `"23:59"` → `datetime.time(23, 59)`; unset → `datetime.time(18, 0)`; invalid format `"25:00"` → `ValueError`; invalid string `"noon"` → `ValueError`

### Implementation for User Story 3

- [x] T020 [US3] Extend `ReminderConfig.from_env()` in `src/reminders/config.py` to parse `REMINDER_TIME` env var as `HH:MM` using `datetime.time.fromisoformat()` or manual split; raise `ValueError` with clear message on invalid format; default to `datetime.time(18, 0)` (depends on T019)
- [x] T021 [US3] Update `register()` in `src/reminders/scheduler.py` to pass `config.reminder_time` and `config.timezone` to `app.job_queue.run_daily()`; log the scheduled time and chat ID at `INFO` level on startup (depends on T020)

**Checkpoint**: All three user stories complete and independently testable.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Static analysis, coverage gate, final validation.

- [x] T022 [P] Run `uv run ruff check src/reminders/ tests/reminders/` and fix all warnings to zero
- [x] T023 [P] Run `uv run mypy src/reminders/ tests/reminders/` and fix all type errors to zero
- [x] T024 Run `uv run pytest tests/reminders/ --cov=src/reminders --cov-report=term-missing` and confirm ≥80% line coverage; add targeted tests if below threshold
- [x] T025 Validate the quickstart flow from `specs/002-ical-reminders/quickstart.md`: install deps, set env vars, start bot, observe log line confirming job registration

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately; T001–T004 can all run in parallel after T001 is done
- **Foundational (Phase 2)**: Depends on T001 (pyproject.toml updated for imports to resolve); T005 and T006 can run in parallel
- **User Stories (Phase 3–5)**: All depend on Foundational (Phase 2) completion
  - US1 (Phase 3) must complete before US2 (Phase 4) — US2 extends the parser started in US1
  - US3 (Phase 5) depends on Phase 2 foundational config; can be developed in parallel with US2 on different files
- **Polish (Phase 6)**: Depends on all user story phases

### User Story Dependencies

- **US1 (P1)**: Can start after Foundational — no dependency on US2 or US3
- **US2 (P2)**: Depends on US1 (extends `parser.py`); tests (T015) can be written in parallel with US1 implementation
- **US3 (P3)**: Depends on Foundational `ReminderConfig` (T006) — configuration extension is independent of parser changes; tests (T019) can be written in parallel with US1/US2

### Within Each User Story

1. Write tests → confirm they FAIL
2. Implement until tests pass
3. Run ruff + mypy (zero errors required per constitution)
4. Commit

### Parallel Opportunities

- T001, T002, T003 in Phase 1 (after T001 is kicked off)
- T004, T002, T003 fully parallel
- T005, T006 in Phase 2 (different files)
- T007, T008 in Phase 3 (different test files)
- T010, T011 in Phase 3 (different source files)
- T019 (US3 test) can be written during US2 implementation
- T022, T023 in Phase 6 (different tools)

---

## Parallel Example: User Story 1

```bash
# Write tests in parallel (T007, T008):
Task: "Write failing unit tests for format_reminder_message() in tests/reminders/test_formatter.py"
Task: "Write failing unit tests for parse_ical() and get_events_for_date() in tests/reminders/test_parser.py"

# Implement in parallel once tests fail (T010, T011):
Task: "Implement format_reminder_message() in src/reminders/formatter.py"
Task: "Implement parse_ical() and get_events_for_date() (non-recurring) in src/reminders/parser.py"

# Then sequentially (T012 → T013 → T014):
Task: "Implement _reminder_job() in src/reminders/scheduler.py"
Task: "Implement register() and export from src/reminders/__init__.py"
Task: "Update src/bot.py with register_reminders call"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1 (basic reminders, non-recurring events)
4. **STOP and VALIDATE**: run test suite, start bot with `sample.ics`, confirm message is sent
5. Ship if sufficient for immediate use

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. US1 → basic reminders working (MVP)
3. US2 → RRULE/RDATE/EXDATE support (needed for real-world iCal files)
4. US3 → configurable time (quality-of-life)
5. Each phase adds value without breaking prior phases

---

## Notes

- **[P]** = different files, no cross-task dependencies
- **[Story]** label traces each task to a specific user story for independent testability
- Constitution Principle II requires tests to FAIL before implementation — do not skip this step
- Commit after each completed task or logical group using conventional commit format (`feat:`, `test:`, `chore:`)
- `src/bot.py` is touched only once (T014) — all other changes are confined to `src/reminders/`
- Stop at any Phase checkpoint to validate story independently before continuing
