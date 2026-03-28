from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Sequence

from daily_bars_core import DailyBar, DailyBarsSource

from daily_bars.fusion import DEFAULT_RELATIVE_CLOSE_EPSILON, fuse_daily_bars_by_consensus


@dataclass
class DegradationReport:
    """What happened while fetching from multiple sources (for observability / logging)."""

    sources_attempted: tuple[str, ...]
    sources_succeeded: tuple[str, ...]
    sources_failed: tuple[str, ...]
    errors: dict[str, str]
    bar_counts: dict[str, int]


def fetch_daily_bars_with_degradation(
    registry: dict[str, DailyBarsSource],
    symbol: str,
    *,
    start: date | None = None,
    end: date | None = None,
    timeout_seconds: float = 30.0,
    source_order: Sequence[str] = ("yahoo", "stooq", "alpha_vantage"),
    symbols_by_source: dict[str, str] | None = None,
    relative_close_epsilon: float = DEFAULT_RELATIVE_CLOSE_EPSILON,
) -> tuple[list[DailyBar], DegradationReport]:
    """Fetch from several sources; failures are skipped; surviving rows are **fused** per day.

    Fusion uses :func:`fuse_daily_bars_by_consensus` (median-close + reference bar when 3+ feeds,
    averaged OHLC when two agree within *relative_close_epsilon*, else primary order).

    Use *symbols_by_source* when tickers differ (e.g. ``{\"stooq\": \"aapl.us\", \"yahoo\": \"AAPL\"}``).
    Returns ``([], report)`` if every source errors or returns no rows—callers do not get an exception
    solely because one vendor is offline.
    """
    attempted = tuple(n for n in source_order if n in registry)
    by_source: dict[str, list[DailyBar]] = {}
    errors: dict[str, str] = {}
    bar_counts: dict[str, int] = {n: 0 for n in attempted}

    for name in attempted:
        src = registry[name]
        sym = symbol
        if symbols_by_source is not None and name in symbols_by_source:
            sym = symbols_by_source[name]
        try:
            bars = src.fetch_daily_bars(
                sym,
                start=start,
                end=end,
                timeout_seconds=timeout_seconds,
            )
            n = len(bars)
            bar_counts[name] = n
            if n:
                by_source[name] = bars
        except Exception as e:
            errors[name] = f"{type(e).__name__}: {e}"

    succeeded = tuple(n for n in attempted if n not in errors)
    merged = fuse_daily_bars_by_consensus(
        by_source,
        source_order,
        relative_close_epsilon=relative_close_epsilon,
    )
    report = DegradationReport(
        sources_attempted=attempted,
        sources_succeeded=succeeded,
        sources_failed=tuple(errors.keys()),
        errors=dict(errors),
        bar_counts=dict(bar_counts),
    )
    return merged, report
