"""Tests for ReminderConfig and the daily reminder job — TDD.

Covers:
- US1: register() schedules job and job sends correct message
- US3: REMINDER_TIME parsing and configurable scheduling
"""

import datetime
import zoneinfo
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.reminders.config import ReminderConfig
from src.reminders.scheduler import _reminder_job, register

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_ics_with_event(date: datetime.date, summary: str) -> str:
    """Build a minimal valid iCal string with one all-day event."""
    date_str = date.strftime("%Y%m%d")
    next_str = (date + datetime.timedelta(days=1)).strftime("%Y%m%d")
    return (
        "BEGIN:VCALENDAR\nVERSION:2.0\n"
        "BEGIN:VEVENT\n"
        f"DTSTART;VALUE=DATE:{date_str}\n"
        f"DTEND;VALUE=DATE:{next_str}\n"
        f"SUMMARY:{summary}\n"
        "UID:test-helper@test\n"
        "DTSTAMP:20260326T000000Z\n"
        "END:VEVENT\n"
        "END:VCALENDAR\n"
    )


# ---------------------------------------------------------------------------
# ReminderConfig tests (US3 — configurable time)
# ---------------------------------------------------------------------------

class TestReminderConfigFromEnv:
    def test_valid_config_returns_dataclass(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        ics = tmp_path / "cal.ics"
        ics.write_text("dummy")
        monkeypatch.setenv("REMINDER_ICAL_PATH", str(ics))
        monkeypatch.setenv("REMINDER_CHAT_ID", "-100123")
        monkeypatch.delenv("REMINDER_TIME", raising=False)
        monkeypatch.delenv("REMINDER_TIMEZONE", raising=False)
        config = ReminderConfig.from_env()
        assert config.ical_path == str(ics)
        assert config.chat_id == -100123
        assert config.reminder_time == datetime.time(18, 0)
        assert str(config.timezone) == "Europe/Berlin"

    def test_missing_ical_path_raises_value_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("REMINDER_ICAL_PATH", raising=False)
        monkeypatch.setenv("REMINDER_CHAT_ID", "-100123")
        with pytest.raises(ValueError, match="REMINDER_ICAL_PATH"):
            ReminderConfig.from_env()

    def test_empty_ical_path_raises_value_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("REMINDER_ICAL_PATH", "  ")
        monkeypatch.setenv("REMINDER_CHAT_ID", "-100123")
        with pytest.raises(ValueError, match="REMINDER_ICAL_PATH"):
            ReminderConfig.from_env()

    def test_missing_chat_id_raises_value_error(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setenv("REMINDER_ICAL_PATH", str(tmp_path / "cal.ics"))
        monkeypatch.delenv("REMINDER_CHAT_ID", raising=False)
        with pytest.raises(ValueError, match="REMINDER_CHAT_ID"):
            ReminderConfig.from_env()

    def test_non_integer_chat_id_raises_value_error(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setenv("REMINDER_ICAL_PATH", str(tmp_path / "cal.ics"))
        monkeypatch.setenv("REMINDER_CHAT_ID", "not-a-number")
        with pytest.raises(ValueError, match="REMINDER_CHAT_ID"):
            ReminderConfig.from_env()

    def test_custom_reminder_time_parsed(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        ics = tmp_path / "cal.ics"
        ics.write_text("dummy")
        monkeypatch.setenv("REMINDER_ICAL_PATH", str(ics))
        monkeypatch.setenv("REMINDER_CHAT_ID", "12345")
        monkeypatch.setenv("REMINDER_TIME", "08:00")
        config = ReminderConfig.from_env()
        assert config.reminder_time == datetime.time(8, 0)

    def test_late_night_time_parsed(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        ics = tmp_path / "cal.ics"
        ics.write_text("dummy")
        monkeypatch.setenv("REMINDER_ICAL_PATH", str(ics))
        monkeypatch.setenv("REMINDER_CHAT_ID", "12345")
        monkeypatch.setenv("REMINDER_TIME", "23:59")
        config = ReminderConfig.from_env()
        assert config.reminder_time == datetime.time(23, 59)

    def test_invalid_time_format_raises_value_error(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setenv("REMINDER_ICAL_PATH", str(tmp_path / "cal.ics"))
        monkeypatch.setenv("REMINDER_CHAT_ID", "12345")
        monkeypatch.setenv("REMINDER_TIME", "25:00")
        with pytest.raises(ValueError, match="REMINDER_TIME"):
            ReminderConfig.from_env()

    def test_non_time_string_raises_value_error(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setenv("REMINDER_ICAL_PATH", str(tmp_path / "cal.ics"))
        monkeypatch.setenv("REMINDER_CHAT_ID", "12345")
        monkeypatch.setenv("REMINDER_TIME", "noon")
        with pytest.raises(ValueError, match="REMINDER_TIME"):
            ReminderConfig.from_env()

    def test_invalid_timezone_raises_value_error(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setenv("REMINDER_ICAL_PATH", str(tmp_path / "cal.ics"))
        monkeypatch.setenv("REMINDER_CHAT_ID", "12345")
        monkeypatch.setenv("REMINDER_TIMEZONE", "Not/ATimezone")
        with pytest.raises(ValueError, match="REMINDER_TIMEZONE"):
            ReminderConfig.from_env()

    def test_custom_timezone_accepted(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        ics = tmp_path / "cal.ics"
        ics.write_text("dummy")
        monkeypatch.setenv("REMINDER_ICAL_PATH", str(ics))
        monkeypatch.setenv("REMINDER_CHAT_ID", "12345")
        monkeypatch.setenv("REMINDER_TIMEZONE", "America/New_York")
        config = ReminderConfig.from_env()
        assert str(config.timezone) == "America/New_York"


# ---------------------------------------------------------------------------
# register() tests (US1 / US3)
# ---------------------------------------------------------------------------

class TestRegister:
    def test_register_schedules_run_daily(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        ics = tmp_path / "cal.ics"
        ics.write_text("dummy")
        monkeypatch.setenv("REMINDER_ICAL_PATH", str(ics))
        monkeypatch.setenv("REMINDER_CHAT_ID", "-100999")

        mock_app = MagicMock()
        mock_app.bot_data = {}
        mock_app.job_queue = MagicMock()

        register(mock_app, MagicMock())

        mock_app.job_queue.run_daily.assert_called_once()

    def test_register_stores_config_in_bot_data(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        ics = tmp_path / "cal.ics"
        ics.write_text("dummy")
        monkeypatch.setenv("REMINDER_ICAL_PATH", str(ics))
        monkeypatch.setenv("REMINDER_CHAT_ID", "-100999")

        mock_app = MagicMock()
        mock_app.bot_data = {}
        mock_app.job_queue = MagicMock()

        register(mock_app, MagicMock())

        assert "reminder_config" in mock_app.bot_data
        assert isinstance(mock_app.bot_data["reminder_config"], ReminderConfig)

    def test_register_passes_configured_time_to_run_daily(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        ics = tmp_path / "cal.ics"
        ics.write_text("dummy")
        monkeypatch.setenv("REMINDER_ICAL_PATH", str(ics))
        monkeypatch.setenv("REMINDER_CHAT_ID", "-100999")
        monkeypatch.setenv("REMINDER_TIME", "08:30")

        mock_app = MagicMock()
        mock_app.bot_data = {}
        mock_app.job_queue = MagicMock()

        register(mock_app, MagicMock())

        call_args = mock_app.job_queue.run_daily.call_args
        # Second positional arg (or 'time' kwarg) is the time
        called_time = call_args.args[1] if len(call_args.args) > 1 else call_args.kwargs.get("time")
        assert called_time == datetime.time(8, 30)

    def test_register_skips_when_ical_path_missing(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("REMINDER_ICAL_PATH", raising=False)
        monkeypatch.delenv("REMINDER_CHAT_ID", raising=False)

        mock_app = MagicMock()
        mock_app.bot_data = {}
        mock_app.job_queue = MagicMock()

        register(mock_app, MagicMock())  # must not raise

        mock_app.job_queue.run_daily.assert_not_called()

    def test_register_skips_when_job_queue_is_none(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        ics = tmp_path / "cal.ics"
        ics.write_text("dummy")
        monkeypatch.setenv("REMINDER_ICAL_PATH", str(ics))
        monkeypatch.setenv("REMINDER_CHAT_ID", "-100999")

        mock_app = MagicMock()
        mock_app.bot_data = {}
        mock_app.job_queue = None

        register(mock_app, MagicMock())  # must not raise


# ---------------------------------------------------------------------------
# _reminder_job tests (US1)
# ---------------------------------------------------------------------------

class TestReminderJob:
    async def test_sends_message_when_tomorrow_has_events(
        self, tmp_path: Path
    ) -> None:
        tomorrow = datetime.date.today() + datetime.timedelta(days=1)
        ics = tmp_path / "cal.ics"
        ics.write_text(_make_ics_with_event(tomorrow, "Test Collection"))

        config = ReminderConfig(
            ical_path=str(ics),
            chat_id=-100123,
            reminder_time=datetime.time(18, 0),
            timezone=zoneinfo.ZoneInfo("Europe/Berlin"),
        )
        context = MagicMock()
        context.bot = AsyncMock()
        context.bot_data = {"reminder_config": config}

        await _reminder_job(context)

        context.bot.send_message.assert_called_once()
        call_kwargs = context.bot.send_message.call_args.kwargs
        assert call_kwargs["chat_id"] == -100123
        assert "Test Collection" in call_kwargs["text"]

    async def test_no_message_when_no_tomorrow_events(
        self, tmp_path: Path
    ) -> None:
        # Event is for today, not tomorrow
        today = datetime.date.today()
        ics = tmp_path / "cal.ics"
        ics.write_text(_make_ics_with_event(today, "Today Only"))

        config = ReminderConfig(
            ical_path=str(ics),
            chat_id=-100123,
            reminder_time=datetime.time(18, 0),
            timezone=zoneinfo.ZoneInfo("Europe/Berlin"),
        )
        context = MagicMock()
        context.bot = AsyncMock()
        context.bot_data = {"reminder_config": config}

        await _reminder_job(context)

        context.bot.send_message.assert_not_called()

    async def test_no_message_when_file_missing(self, tmp_path: Path) -> None:
        config = ReminderConfig(
            ical_path=str(tmp_path / "nonexistent.ics"),
            chat_id=-100123,
            reminder_time=datetime.time(18, 0),
            timezone=zoneinfo.ZoneInfo("Europe/Berlin"),
        )
        context = MagicMock()
        context.bot = AsyncMock()
        context.bot_data = {"reminder_config": config}

        await _reminder_job(context)  # must not raise

        context.bot.send_message.assert_not_called()

    async def test_message_includes_tomorrow_date(self, tmp_path: Path) -> None:
        tomorrow = datetime.date.today() + datetime.timedelta(days=1)
        ics = tmp_path / "cal.ics"
        ics.write_text(_make_ics_with_event(tomorrow, "Collection"))

        config = ReminderConfig(
            ical_path=str(ics),
            chat_id=-100999,
            reminder_time=datetime.time(18, 0),
            timezone=zoneinfo.ZoneInfo("Europe/Berlin"),
        )
        context = MagicMock()
        context.bot = AsyncMock()
        context.bot_data = {"reminder_config": config}

        await _reminder_job(context)

        text = context.bot.send_message.call_args.kwargs["text"]
        assert str(tomorrow.year) in text
