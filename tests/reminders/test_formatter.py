"""Unit tests for format_reminder_message — TDD: written before implementation."""

import datetime

from src.reminders.formatter import format_reminder_message
from src.reminders.parser import CalendarEvent


class TestFormatReminderMessage:
    def test_returns_none_when_no_events(self) -> None:
        result = format_reminder_message([], datetime.date(2026, 4, 20))
        assert result is None

    def test_single_event_contains_summary(self) -> None:
        events = [CalendarEvent(summary="EB Glas-Tonne", date=datetime.date(2026, 4, 21))]
        result = format_reminder_message(events, datetime.date(2026, 4, 21))
        assert result is not None
        assert "EB Glas-Tonne" in result

    def test_single_event_contains_formatted_date(self) -> None:
        # 2026-04-21 is a Tuesday
        events = [CalendarEvent(summary="Test", date=datetime.date(2026, 4, 21))]
        result = format_reminder_message(events, datetime.date(2026, 4, 21))
        assert result is not None
        assert "Tuesday" in result
        assert "21" in result
        assert "April" in result
        assert "2026" in result

    def test_multiple_events_all_listed(self) -> None:
        events = [
            CalendarEvent(summary="EB Glas-Tonne", date=datetime.date(2026, 4, 21)),
            CalendarEvent(summary="EB Gelber Sack", date=datetime.date(2026, 4, 21)),
        ]
        result = format_reminder_message(events, datetime.date(2026, 4, 21))
        assert result is not None
        assert "EB Glas-Tonne" in result
        assert "EB Gelber Sack" in result

    def test_message_uses_bullet_character(self) -> None:
        events = [CalendarEvent(summary="Collection", date=datetime.date(2026, 4, 21))]
        result = format_reminder_message(events, datetime.date(2026, 4, 21))
        assert result is not None
        assert "\u2022" in result

    def test_message_starts_with_reminder_header(self) -> None:
        events = [CalendarEvent(summary="Test", date=datetime.date(2026, 4, 20))]
        result = format_reminder_message(events, datetime.date(2026, 4, 20))
        assert result is not None
        assert result.startswith("Reminder: tomorrow is")

    def test_monday_date_formatted_correctly(self) -> None:
        # 2026-04-20 is a Monday
        events = [CalendarEvent(summary="Test", date=datetime.date(2026, 4, 20))]
        result = format_reminder_message(events, datetime.date(2026, 4, 20))
        assert result is not None
        assert "Monday" in result
        assert "20. April 2026" in result

    def test_event_order_preserved(self) -> None:
        events = [
            CalendarEvent(summary="First", date=datetime.date(2026, 4, 21)),
            CalendarEvent(summary="Second", date=datetime.date(2026, 4, 21)),
            CalendarEvent(summary="Third", date=datetime.date(2026, 4, 21)),
        ]
        result = format_reminder_message(events, datetime.date(2026, 4, 21))
        assert result is not None
        assert result.index("First") < result.index("Second") < result.index("Third")
