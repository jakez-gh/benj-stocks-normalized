from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class DailyBar:
    """One regular-hours daily bar on an *investor-continuous* basis.

    OHLC are split- and dividend-adjusted so a 2-for-1 split does not create a
    fictitious halving of prior prices: history is restated as if today's share
    count applied throughout. Volume is scaled consistently with that restatement
    where the upstream feed provides enough information (Yahoo; Alpha Vantage
    adjusted series; Stooq bars aligned using Yahoo adjustment ratios).
    """

    trade_date: date
    open: float
    high: float
    low: float
    close: float
    volume: int
