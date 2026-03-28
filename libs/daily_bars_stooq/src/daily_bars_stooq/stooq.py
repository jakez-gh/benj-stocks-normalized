from __future__ import annotations

from datetime import date
from urllib.parse import urlencode
from urllib.request import urlopen

from daily_bars_core import DailyBar, filter_sort_daily_range

from daily_bars_stooq.investor_adjust import (
    adjust_stooq_bars_with_yfinance,
    stooq_symbol_to_yahoo_ticker,
)
from daily_bars_stooq.parse import parse_stooq_daily_csv

_STOOQ_DAILY_URL = "https://stooq.com/q/d/l/"


def retrieve_daily_bars_stooq(
    symbol: str,
    *,
    start: date | None = None,
    end: date | None = None,
    timeout_seconds: float = 30.0,
    yahoo_symbol: str | None = None,
    adjust_for_investor_series: bool = True,
) -> list[DailyBar]:
    query = urlencode({"s": symbol.lower(), "i": "d"})
    url = f"{_STOOQ_DAILY_URL}?{query}"
    with urlopen(url, timeout=timeout_seconds) as resp:
        body = resp.read().decode("utf-8")
    bars = parse_stooq_daily_csv(body)
    bars = filter_sort_daily_range(bars, start=start, end=end)
    if adjust_for_investor_series and bars:
        yt = yahoo_symbol or stooq_symbol_to_yahoo_ticker(symbol)
        bars = adjust_stooq_bars_with_yfinance(bars, yt, timeout_seconds=timeout_seconds)
    return bars


class StooqDailyBarsSource:
    name = "stooq"

    def __init__(
        self,
        *,
        yahoo_symbol: str | None = None,
        adjust_for_investor_series: bool = True,
    ) -> None:
        self._yahoo_symbol = yahoo_symbol
        self._adjust_for_investor_series = adjust_for_investor_series

    def fetch_daily_bars(
        self,
        symbol: str,
        *,
        start: date | None = None,
        end: date | None = None,
        timeout_seconds: float = 30.0,
    ) -> list[DailyBar]:
        return retrieve_daily_bars_stooq(
            symbol,
            start=start,
            end=end,
            timeout_seconds=timeout_seconds,
            yahoo_symbol=self._yahoo_symbol,
            adjust_for_investor_series=self._adjust_for_investor_series,
        )
