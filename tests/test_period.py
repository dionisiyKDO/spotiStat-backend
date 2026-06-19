from datetime import datetime, timezone

import pytest

from spotistat.period import resolve_period


def _epoch(y, m, d):
    return int(datetime(y, m, d, tzinfo=timezone.utc).timestamp())


def test_all_is_unbounded():
    assert resolve_period("all") == (None, None)
    assert resolve_period(None) == (None, None)


def test_calendar_year():
    assert resolve_period("2023") == (_epoch(2023, 1, 1), _epoch(2024, 1, 1))


def test_rolling_months_recent_window_starts_later():
    start_3m, end_3m = resolve_period("3m")
    start_12m, _ = resolve_period("12m")
    now = datetime.now(timezone.utc).timestamp()
    assert end_3m is None
    assert start_12m < start_3m < now  # 3 months back is more recent than 12


def test_explicit_dates_override_period():
    start, end = resolve_period("2020", start="2023-06-01", end="2023-07-01")
    assert start == _epoch(2023, 6, 1)
    assert end == _epoch(2023, 7, 1)


def test_unknown_period_raises():
    with pytest.raises(ValueError):
        resolve_period("banana")
