# Feature Specification: iCalendar Event Reminders

**Feature Branch**: `002-ical-reminders`
**Created**: 2026-03-26
**Status**: Draft
**Input**: User description: "Extend the existing telegram bot to read iCalendar files and send reminders to the telegram group at a configurable time before events."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Automated Day-Before Reminder (Priority: P1)

A bot administrator configures an iCalendar file (e.g., a municipal waste collection schedule) and a reminder time. The bot automatically sends a message to the configured Telegram group every day at that time if there are events scheduled for the following day. Group members receive a friendly reminder listing what is happening tomorrow without any manual intervention.

**Why this priority**: This is the core value of the feature — reliable, automated reminders so users never miss a scheduled event.

**Independent Test**: Can be fully tested by providing an iCal file with a known event date, setting the reminder time, and verifying a message is delivered to the group chat the day before the event.

**Acceptance Scenarios**:

1. **Given** an iCal file contains an event on April 21st and the reminder time is 18:00, **When** April 20th at 18:00 arrives, **Then** the bot sends a message to the Telegram group listing the event summary for April 21st.
2. **Given** an iCal file contains no events for a given tomorrow, **When** the reminder check runs, **Then** the bot sends no message.
3. **Given** multiple events are scheduled for the same day, **When** the reminder fires, **Then** all upcoming events for that day are included in a single message.

---

### User Story 2 - Recurring Event Support (Priority: P2)

The iCalendar file uses recurrence rules (RRULE), additional dates (RDATE), and exclusion dates (EXDATE) to define a repeating schedule (e.g., waste collection every two weeks). The bot correctly expands these recurrences and sends reminders for each actual occurrence, respecting added and excluded dates.

**Why this priority**: Real-world iCal files (such as municipal schedules) rely heavily on recurrence rules. Without this, most practical use cases would be broken.

**Independent Test**: Can be tested by providing an iCal file with an RRULE-based event and verifying reminders fire on all expected occurrence dates (including RDATE additions and EXDATE exclusions) over a multi-week period.

**Acceptance Scenarios**:

1. **Given** an event recurs every two weeks on Wednesday via RRULE, **When** the day before a recurrence falls, **Then** a reminder is sent.
2. **Given** an EXDATE excludes a specific recurrence date, **When** the day before the excluded date arrives, **Then** no reminder is sent for that occurrence.
3. **Given** an RDATE adds an extra non-recurring occurrence, **When** the day before that date arrives, **Then** a reminder is sent.

---

### User Story 3 - Configurable Reminder Time (Priority: P3)

The bot administrator can change the time at which daily reminders are sent (e.g., from 18:00 to 08:00) without modifying the source code, using a configuration setting. The change takes effect on the next bot start.

**Why this priority**: Different households may prefer reminders at different times. This is a convenience feature — the feature works with a sensible default even if not changed.

**Independent Test**: Can be tested by setting two different reminder times in configuration and verifying the reminder message is sent at the configured time in each case.

**Acceptance Scenarios**:

1. **Given** the reminder time is configured to 08:00, **When** the next day begins, **Then** the reminder fires at 08:00, not at the default 18:00.
2. **Given** the reminder time is not configured, **When** the bot starts, **Then** it defaults to 18:00.

---

### Edge Cases

- What happens when the iCal file is missing or unreadable at startup? → Bot logs an error and continues operating; all existing features remain unaffected.
- What happens when the iCal file contains events with no SUMMARY field? → Bot uses a fallback label (e.g., "Unnamed event").
- What happens when an RRULE has an UNTIL date that has passed? → No reminders are sent for expired recurrences.
- What happens when daylight saving time changes cause the reminder time to shift? → The reminder time is interpreted in a configured timezone; DST transitions are handled correctly.
- What happens when the Telegram group is unreachable at reminder time? → The bot logs the failure; no retry is required for that day.
- What happens when multiple iCal files need to be monitored? → Out of scope for this feature; a single configured file is supported.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The bot MUST read and parse a configured iCalendar (.ics) file on startup and refresh it before each daily reminder check.
- **FR-002**: The bot MUST expand recurring events defined with RRULE, RDATE, and EXDATE to determine all concrete occurrence dates within a rolling one-year window.
- **FR-003**: The bot MUST send a Telegram message to the configured group chat each day at the configured reminder time when one or more events are scheduled for the following calendar day.
- **FR-004**: The reminder message MUST list the SUMMARY of each event occurring the following day.
- **FR-005**: The reminder time MUST be configurable without changing the source code (via environment variable or configuration file) and MUST default to 18:00 if not specified.
- **FR-006**: The iCalendar file path MUST be configurable without changing the source code.
- **FR-007**: The reminder timezone MUST be configurable and MUST default to the system's local timezone if not specified.
- **FR-008**: The iCalendar reminder feature MUST be implemented as an independent, self-contained module that does not modify existing bot functionality, following the open-closed principle.
- **FR-009**: The bot MUST continue to function normally for all existing features even if the iCal file is missing, malformed, or reminder delivery fails.

### Key Entities

- **Calendar Event**: A single concrete occurrence derived from a VEVENT entry. Attributes: event summary (display name), occurrence date.
- **Reminder Schedule**: The daily time at which the bot evaluates and sends reminders. Attributes: time-of-day (HH:MM), timezone.
- **iCalendar Source**: The configured calendar file providing event data. Attributes: file path on the host system.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Reminder messages are delivered to the Telegram group within 60 seconds of the configured reminder time on days with upcoming events.
- **SC-002**: All concrete occurrences of recurring events (RRULE, RDATE, EXDATE) are correctly identified — zero missed or spurious reminders in a test scenario covering at least 10 recurrences.
- **SC-003**: The reminder time and iCal file path can be changed via configuration without any code change, verified by running the bot with two different configurations.
- **SC-004**: All existing bot features (Gemini image capabilities) continue to work correctly with the iCalendar feature enabled — zero regressions in integration tests.
- **SC-005**: The bot starts successfully and all existing features remain available even when the configured iCal file is absent.

## Assumptions

- A single iCalendar (.ics) file is provided; monitoring multiple files simultaneously is out of scope.
- Events use all-day date format (DATE, not DATETIME) for DTSTART, matching the provided example.
- Reminders cover only the immediately following calendar day (T+1); configurable lead times per event are out of scope.
- The Telegram group chat ID used for reminders is the same as the one already configured for the existing bot.
- The bot process runs continuously; it manages its own internal scheduling rather than relying on an external cron job.
- Reminder messages are plain text; no special formatting or media is required.
- The iCal file is stored locally on the host running the bot; remote URL fetching is out of scope.
