from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class NormalizedDailyBar:
    """One calendar day of OHLCV in a stable, analysis-friendly shape.

    Data is sourced from :mod:`daily_bars` (benj-stocks): investor-continuous,
    split- and dividend-adjusted semantics match :class:`daily_bars_core.DailyBar`.

    * ``volume`` is a float so exports line up with typical dataframe / parquet use.
    * ``close_zscore`` is optional: population z-score of *close* over the series
      when you run :func:`benj_stocks_normalized.transforms.with_close_zscore`.
    """

    symbol: str
    trade_date: date
    open: float
    high: float
    low: float
    close: float
    volume: float
    close_zscore: float | None = None


@dataclass(frozen=True, slots=True)
class TanhDeltaDailyBar:
    """Day-over-day change for each OHLCV field, compressed with :func:`math.tanh`.

    Each value uses the **same** field vs yesterday (open vs prior open, …). Values
    ``<= 0`` are treated as **0** first. If effective prior and current are both
    ``> 0``, the move is ``tanh(delta_scale * (c - p) / p)``; otherwise the
    sentinel rules apply (``0.0``, ``±1.0``, or ``0.0`` when both zero or both
    equal positive levels).

    See :func:`benj_stocks_normalized.transforms.with_tanh_deltas_from_previous`.
    """

    symbol: str
    trade_date: date
    open_tanh: float
    high_tanh: float
    low_tanh: float
    close_tanh: float
    volume_tanh: float
