from __future__ import annotations

from collections.abc import Sequence
from datetime import date

from daily_bars import (
    DEFAULT_RELATIVE_CLOSE_EPSILON,
    DegradationReport,
    build_source_registry,
    fetch_daily_bars_with_degradation,
)
from daily_bars_core import DailyBarsSource

from benj_stocks_normalized.convert import daily_bars_to_normalized
from benj_stocks_normalized.schema import NormalizedDailyBar, TanhDeltaDailyBar
from benj_stocks_normalized.transforms import with_tanh_deltas_from_previous


def fetch_normalized_daily_bars(
    symbol: str,
    *,
    start: date | None = None,
    end: date | None = None,
    timeout_seconds: float = 30.0,
    source_order: Sequence[str] = ("yahoo", "stooq", "alpha_vantage"),
    symbols_by_source: dict[str, str] | None = None,
    relative_close_epsilon: float = DEFAULT_RELATIVE_CLOSE_EPSILON,
    alpha_vantage_api_key: str | None = None,
    registry: dict[str, DailyBarsSource] | None = None,
) -> tuple[list[NormalizedDailyBar], DegradationReport]:
    """Fetch via :mod:`daily_bars` (benj-stocks), then map to :class:`NormalizedDailyBar`.

    This is a thin wrapper around :func:`daily_bars.fetch_daily_bars_with_degradation`
    plus :func:`benj_stocks_normalized.convert.daily_bars_to_normalized`.
    """
    reg = registry if registry is not None else build_source_registry(alpha_vantage_api_key=alpha_vantage_api_key)
    bars, report = fetch_daily_bars_with_degradation(
        reg,
        symbol,
        start=start,
        end=end,
        timeout_seconds=timeout_seconds,
        source_order=source_order,
        symbols_by_source=symbols_by_source,
        relative_close_epsilon=relative_close_epsilon,
    )
    return daily_bars_to_normalized(bars, symbol), report


def fetch_tanh_delta_daily_bars(
    symbol: str,
    *,
    start: date | None = None,
    end: date | None = None,
    timeout_seconds: float = 30.0,
    source_order: Sequence[str] = ("yahoo", "stooq", "alpha_vantage"),
    symbols_by_source: dict[str, str] | None = None,
    relative_close_epsilon: float = DEFAULT_RELATIVE_CLOSE_EPSILON,
    alpha_vantage_api_key: str | None = None,
    registry: dict[str, DailyBarsSource] | None = None,
    delta_scale: float = 1.0,
    drop_first: bool = True,
) -> tuple[list[TanhDeltaDailyBar], DegradationReport]:
    """Fetch from benj-stocks, then :func:`~benj_stocks_normalized.transforms.with_tanh_deltas_from_previous`."""
    normalized, report = fetch_normalized_daily_bars(
        symbol,
        start=start,
        end=end,
        timeout_seconds=timeout_seconds,
        source_order=source_order,
        symbols_by_source=symbols_by_source,
        relative_close_epsilon=relative_close_epsilon,
        alpha_vantage_api_key=alpha_vantage_api_key,
        registry=registry,
    )
    return with_tanh_deltas_from_previous(
        normalized,
        delta_scale=delta_scale,
        drop_first=drop_first,
    ), report
