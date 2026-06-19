"""Resolve a period selector into ``(start, end)`` epoch-second bounds (end exclusive).

A ``None`` bound means unbounded on that side, so ``(None, None)`` is all-time.

``period`` tokens:
  all       -> (None, None)
  <N>m      -> rolling: the last N calendar months up to now (e.g. 3m, 12m)
  <YYYY>    -> a single calendar year (e.g. 2023)

Explicit ISO dates ``start``/``end`` (``YYYY-MM-DD``), if given, override ``period``.
"""

from __future__ import annotations

import calendar
import re
from datetime import datetime, timezone


def resolve_period(
    period: str | None = "all",
    start: str | None = None,
    end: str | None = None,
) -> tuple[int | None, int | None]:
    if start is not None or end is not None:
        return _iso_to_epoch(start), _iso_to_epoch(end)

    if not period or period == "all":
        return None, None

    if re.fullmatch(r"\d+m", period):
        return _epoch(_months_ago(int(period[:-1]))), None

    if re.fullmatch(r"\d{4}", period):
        year = int(period)
        return _epoch(_utc(year, 1, 1)), _epoch(_utc(year + 1, 1, 1))

    raise ValueError(
        f"Unknown period {period!r}; use 'all', '<N>m' (e.g. 3m), or a year (e.g. 2023)."
    )


def _utc(year: int, month: int, day: int) -> datetime:
    return datetime(year, month, day, tzinfo=timezone.utc)


def _epoch(dt: datetime) -> int:
    return int(dt.timestamp())


def _iso_to_epoch(value: str | None) -> int | None:
    if value is None:
        return None
    return _epoch(datetime.fromisoformat(value).replace(tzinfo=timezone.utc))


def _months_ago(months: int) -> datetime:
    now = datetime.now(timezone.utc)
    index = now.year * 12 + (now.month - 1) - months
    year, month = divmod(index, 12)
    month += 1
    day = min(now.day, calendar.monthrange(year, month)[1])
    return now.replace(year=year, month=month, day=day)
