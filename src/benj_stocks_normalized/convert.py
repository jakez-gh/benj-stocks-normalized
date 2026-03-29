from __future__ import annotations

from collections.abc import Sequence

from daily_bars_core import DailyBar

from benj_stocks_normalized.schema import NormalizedDailyBar


def daily_bars_to_normalized(bars: Sequence[DailyBar], symbol: str) -> list[NormalizedDailyBar]:
    """Map fused :class:`~daily_bars_core.DailyBar` rows into :class:`NormalizedDailyBar`."""
    return [
        NormalizedDailyBar(
            symbol=symbol,
            trade_date=b.trade_date,
            open=b.open,
            high=b.high,
            low=b.low,
            close=b.close,
            volume=float(b.volume),
            close_zscore=None,
        )
        for b in bars
    ]
