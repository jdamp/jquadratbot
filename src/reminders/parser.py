"""Calendar parser: parse iCal files and expand recurring events.

Handles RRULE (weekly/monthly/yearly with INTERVAL, BYDAY, UNTIL),
RDATE (extra occurrences), and EXDATE (excluded occurrences) using
the icalendar + python-dateutil libraries.
"""

import datetime
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dateutil.rrule import rruleset, rrulestr
from icalendar import Calendar

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CalendarEvent:
    """A single concrete occurrence of a calendar event."""

    summary: str
    date: datetime.date


def _prop_to_datetimes(component: Any, prop_name: str) -> list[datetime.datetime]:
    """Extract naive datetime objects from an RDATE or EXDATE property.

    Handles both single vDDDLists and lists of them (multiple property lines).
    Converts all-day dates (datetime.date) to midnight datetime for use in rruleset.
    """
    prop = component.get(prop_name)
    if prop is None:
        return []
    props: list[Any] = prop if isinstance(prop, list) else [prop]
    result: list[datetime.datetime] = []
    for p in props:
        # vDDDLists has a .dts attribute; fallback to treating p itself as a single value
        dts: list[Any] = getattr(p, "dts", [p])
        for d in dts:
            dt: Any = getattr(d, "dt", d)
            if isinstance(dt, datetime.datetime):
                result.append(dt.replace(tzinfo=None))
            elif isinstance(dt, datetime.date):
                result.append(datetime.datetime.combine(dt, datetime.time()))
    return result


def parse_ical(
    path: str,
    expansion_end: datetime.date | None = None,
) -> list[CalendarEvent]:
    """Parse an iCal file and return all concrete CalendarEvent occurrences.

    For recurring events, occurrences are expanded within the window
    [event DTSTART, expansion_end]. Non-recurring events are always included.

    Args:
        path: Filesystem path to the .ics file.
        expansion_end: Upper bound for recurrence expansion. Defaults to
            today + 365 days when not provided.

    Returns:
        List of CalendarEvent instances. Returns [] and logs a warning if the
        file is missing, unreadable, or not valid iCalendar data.
    """
    eff_end = expansion_end or (datetime.date.today() + datetime.timedelta(days=365))

    try:
        data = Path(path).read_bytes()
    except OSError as exc:
        logger.warning("Cannot read iCal file %r: %s", path, exc)
        return []

    try:
        cal = Calendar.from_ical(data)
    except Exception as exc:
        logger.warning("Cannot parse iCal file %r: %s", path, exc)
        return []

    events: list[CalendarEvent] = []

    for component in cal.walk():
        if component.name != "VEVENT":
            continue

        raw_summary = component.get("SUMMARY")  # type: ignore[no-untyped-call]
        summary = str(raw_summary).strip() if raw_summary is not None else ""
        summary = summary or "Unnamed event"

        dtstart_prop = component.get("DTSTART")  # type: ignore[no-untyped-call]
        if dtstart_prop is None:
            continue
        dtstart_val: Any = dtstart_prop.dt
        if isinstance(dtstart_val, datetime.datetime):
            dtstart_date = dtstart_val.date()
        else:
            dtstart_date = dtstart_val

        rrule_prop = component.get("RRULE")  # type: ignore[no-untyped-call]
        if rrule_prop is None:
            # Non-recurring: include unconditionally
            events.append(CalendarEvent(summary=summary, date=dtstart_date))
            continue

        # Recurring event — build an rruleset using dateutil
        dtstart_dt = datetime.datetime.combine(dtstart_date, datetime.time())
        dtstart_str = dtstart_dt.strftime("%Y%m%dT%H%M%S")
        rrule_str_val: str = rrule_prop.to_ical().decode()

        rset: rruleset = rrulestr(
            f"DTSTART:{dtstart_str}\nRRULE:{rrule_str_val}",
            ignoretz=True,
            forceset=True,
        )

        for rdate_dt in _prop_to_datetimes(component, "RDATE"):
            rset.rdate(rdate_dt)

        for exdate_dt in _prop_to_datetimes(component, "EXDATE"):
            rset.exdate(exdate_dt)

        window_end = datetime.datetime.combine(eff_end, datetime.time(23, 59, 59))
        for occurrence in rset.between(dtstart_dt, window_end, inc=True):
            events.append(CalendarEvent(summary=summary, date=occurrence.date()))

    return events


def get_events_for_date(
    events: list[CalendarEvent], date: datetime.date
) -> list[CalendarEvent]:
    """Return all events whose date matches the given date."""
    return [e for e in events if e.date == date]
