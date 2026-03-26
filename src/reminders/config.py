"""ReminderConfig: environment variable loading for the reminder subsystem."""

import datetime
import logging
import os
import zoneinfo
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ReminderConfig:
    """Configuration for the daily iCalendar reminder feature."""

    ical_path: str
    chat_id: int
    reminder_time: datetime.time
    timezone: zoneinfo.ZoneInfo

    @classmethod
    def from_env(cls) -> ReminderConfig:
        """Load reminder configuration from environment variables.

        Raises ValueError if any required or optional variable is invalid.
        """
        ical_path = os.getenv("REMINDER_ICAL_PATH", "").strip()
        if not ical_path:
            raise ValueError("REMINDER_ICAL_PATH is required but not set")

        chat_id_str = os.getenv("REMINDER_CHAT_ID", "").strip()
        if not chat_id_str:
            raise ValueError("REMINDER_CHAT_ID is required but not set")
        try:
            chat_id = int(chat_id_str)
        except ValueError as exc:
            raise ValueError(
                f"REMINDER_CHAT_ID must be an integer, got: {chat_id_str!r}"
            ) from exc

        time_str = os.getenv("REMINDER_TIME", "18:00").strip()
        try:
            parts = time_str.split(":")
            if len(parts) != 2:  # noqa: PLR2004
                raise ValueError("must have exactly HH and MM parts")
            reminder_time = datetime.time(int(parts[0]), int(parts[1]))
        except ValueError as exc:
            raise ValueError(
                f"REMINDER_TIME must be HH:MM format (24-hour), got: {time_str!r}"
            ) from exc

        tz_str = os.getenv("REMINDER_TIMEZONE", "Europe/Berlin").strip()
        try:
            timezone = zoneinfo.ZoneInfo(tz_str)
        except zoneinfo.ZoneInfoNotFoundError as exc:
            raise ValueError(
                f"REMINDER_TIMEZONE is not a valid IANA timezone name: {tz_str!r}"
            ) from exc

        return cls(
            ical_path=ical_path,
            chat_id=chat_id,
            reminder_time=reminder_time,
            timezone=timezone,
        )
