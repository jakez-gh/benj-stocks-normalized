from __future__ import annotations

from datetime import date

from daily_bars_core.models import DailyBar


def filter_sort_daily_range(
    bars: list[DailyBar],
    *,
    start: date | None,
    end: date | None,
) -> list[DailyBar]:
    out = bars
    if start is not None:
        out = [b for b in out if b.trade_date >= start]
    if end is not None:
        out = [b for b in out if b.trade_date <= end]
    return sorted(out, key=lambda b: b.trade_date)
