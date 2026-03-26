"""Unit tests for calendar parser — TDD: written before implementation.

Covers:
- US1: non-recurring event parsing
- US2: RRULE/RDATE/EXDATE recurrence expansion
"""

import datetime
from pathlib import Path

import pytest

from src.reminders.parser import CalendarEvent, get_events_for_date, parse_ical

FIXTURES_DIR = Path(__file__).parent / "fixtures"
SAMPLE_ICS = str(FIXTURES_DIR / "sample.ics")

# Fixed expansion end covering all fixture dates
EXPANSION_END = datetime.date(2027, 1, 1)


class TestCalendarEvent:
    def test_is_frozen(self) -> None:
        from dataclasses import FrozenInstanceError

        event = CalendarEvent(summary="Test", date=datetime.date(2026, 4, 21))
        with pytest.raises(FrozenInstanceError):
            event.summary = "Other"  # type: ignore[misc]

    def test_fields(self) -> None:
        event = CalendarEvent(summary="Test", date=datetime.date(2026, 4, 21))
        assert event.summary == "Test"
        assert event.date == datetime.date(2026, 4, 21)


class TestParseIcalNonRecurring:
    def test_single_non_recurring_event_included(self) -> None:
        events = parse_ical(SAMPLE_ICS, expansion_end=EXPANSION_END)
        singles = [e for e in events if e.summary == "Single Event"]
        assert len(singles) == 1
        assert singles[0].date == datetime.date(2026, 5, 15)

    def test_missing_file_returns_empty_list(self, tmp_path: Path) -> None:
        result = parse_ical(str(tmp_path / "nonexistent.ics"))
        assert result == []

    def test_malformed_file_returns_empty_list(self, tmp_path: Path) -> None:
        bad_file = tmp_path / "bad.ics"
        bad_file.write_text("this is not valid ical data!!!\x00\x01\x02")
        result = parse_ical(str(bad_file))
        assert result == []

    def test_event_with_no_summary_uses_fallback(self, tmp_path: Path) -> None:
        ics = tmp_path / "no_summary.ics"
        ics.write_text(
            "BEGIN:VCALENDAR\nVERSION:2.0\n"
            "BEGIN:VEVENT\n"
            "DTSTART;VALUE=DATE:20260515\n"
            "DTEND;VALUE=DATE:20260516\n"
            "UID:no-summary@test\n"
            "DTSTAMP:20260326T000000Z\n"
            "END:VEVENT\n"
            "END:VCALENDAR\n"
        )
        events = parse_ical(str(ics))
        assert len(events) == 1
        assert events[0].summary == "Unnamed event"

    def test_returns_list_type(self) -> None:
        result = parse_ical(SAMPLE_ICS, expansion_end=EXPANSION_END)
        assert isinstance(result, list)
        assert all(isinstance(e, CalendarEvent) for e in result)


class TestGetEventsForDate:
    def test_returns_matching_events(self) -> None:
        target = datetime.date(2026, 4, 21)
        events = [
            CalendarEvent(summary="Match", date=target),
            CalendarEvent(summary="No match", date=datetime.date(2026, 4, 22)),
        ]
        result = get_events_for_date(events, target)
        assert len(result) == 1
        assert result[0].summary == "Match"

    def test_returns_empty_when_no_match(self) -> None:
        events = [CalendarEvent(summary="Event", date=datetime.date(2026, 4, 21))]
        result = get_events_for_date(events, datetime.date(2026, 5, 1))
        assert result == []

    def test_returns_multiple_matching_events(self) -> None:
        target = datetime.date(2026, 4, 21)
        events = [
            CalendarEvent(summary="A", date=target),
            CalendarEvent(summary="B", date=target),
            CalendarEvent(summary="C", date=datetime.date(2026, 4, 22)),
        ]
        result = get_events_for_date(events, target)
        assert len(result) == 2

    def test_empty_events_returns_empty(self) -> None:
        result = get_events_for_date([], datetime.date(2026, 4, 21))
        assert result == []


class TestRecurringEvents:
    """US2: Verify RRULE/RDATE/EXDATE expansion."""

    def test_rrule_occurrence_appears_on_expected_date(self) -> None:
        # sample.ics recurring event starts 2026-04-02 (Thu), bi-weekly
        events = parse_ical(SAMPLE_ICS, expansion_end=EXPANSION_END)
        dates = {e.date for e in events if e.summary == "Recurring Event"}
        assert datetime.date(2026, 4, 2) in dates

    def test_rrule_second_occurrence_appears(self) -> None:
        events = parse_ical(SAMPLE_ICS, expansion_end=EXPANSION_END)
        dates = {e.date for e in events if e.summary == "Recurring Event"}
        assert datetime.date(2026, 4, 16) in dates

    def test_exdate_occurrence_excluded(self) -> None:
        # 2026-04-30 is excluded via EXDATE
        events = parse_ical(SAMPLE_ICS, expansion_end=EXPANSION_END)
        dates = {e.date for e in events if e.summary == "Recurring Event"}
        assert datetime.date(2026, 4, 30) not in dates

    def test_rdate_extra_occurrence_included(self) -> None:
        # 2026-05-01 is added via RDATE (not a Thursday)
        events = parse_ical(SAMPLE_ICS, expansion_end=EXPANSION_END)
        dates = {e.date for e in events if e.summary == "Recurring Event"}
        assert datetime.date(2026, 5, 1) in dates

    def test_rrule_occurrence_after_exdate_still_appears(self) -> None:
        # 2026-05-14 is the next occurrence after the excluded 2026-04-30
        events = parse_ical(SAMPLE_ICS, expansion_end=EXPANSION_END)
        dates = {e.date for e in events if e.summary == "Recurring Event"}
        assert datetime.date(2026, 5, 14) in dates

    def test_until_date_respected(self) -> None:
        # UNTIL=20261231T000000Z — no occurrences in 2027
        events = parse_ical(SAMPLE_ICS, expansion_end=EXPANSION_END)
        dates = {e.date for e in events if e.summary == "Recurring Event"}
        jan_2027 = {d for d in dates if d >= datetime.date(2027, 1, 1)}
        assert len(jan_2027) == 0

    def test_multiple_occurrences_in_april_may(self) -> None:
        events = parse_ical(SAMPLE_ICS, expansion_end=EXPANSION_END)
        apr_may = [
            e
            for e in events
            if e.summary == "Recurring Event"
            and datetime.date(2026, 4, 1) <= e.date <= datetime.date(2026, 5, 31)
        ]
        # Expected: Apr 2, Apr 16, May 1 (RDATE), May 14, May 28
        assert len(apr_may) == 5

    def test_non_recurring_and_recurring_coexist(self) -> None:
        events = parse_ical(SAMPLE_ICS, expansion_end=EXPANSION_END)
        summaries = {e.summary for e in events}
        assert "Single Event" in summaries
        assert "Recurring Event" in summaries
