from daily_bars import DEFAULT_RELATIVE_CLOSE_EPSILON, DegradationReport

from benj_stocks_normalized.api import fetch_normalized_daily_bars, fetch_tanh_delta_daily_bars
from benj_stocks_normalized.convert import daily_bars_to_normalized
from benj_stocks_normalized.schema import NormalizedDailyBar, TanhDeltaDailyBar
from benj_stocks_normalized.transforms import (
    scale_ohlc_by_first_close,
    with_close_zscore,
    with_tanh_deltas_from_previous,
)

__all__ = [
    "DEFAULT_RELATIVE_CLOSE_EPSILON",
    "DegradationReport",
    "NormalizedDailyBar",
    "TanhDeltaDailyBar",
    "daily_bars_to_normalized",
    "fetch_normalized_daily_bars",
    "fetch_tanh_delta_daily_bars",
    "scale_ohlc_by_first_close",
    "with_close_zscore",
    "with_tanh_deltas_from_previous",
]
