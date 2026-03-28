from __future__ import annotations

from datetime import date, timedelta

import yfinance as yf

from daily_bars_core import DailyBar, filter_sort_daily_range


class YahooDailyBarsSource:
    """Yahoo Finance via yfinance.

    Uses split- and dividend-adjusted OHLCV (`auto_adjust=True`) so the series is
    continuous for an investor holding stock through splits and cash dividends.
    """

    name = "yahoo"

    def fetch_daily_bars(
        self,
        symbol: str,
        *,
        start: date | None = None,
        end: date | None = None,
        timeout_seconds: float = 30.0,
    ) -> list[DailyBar]:
        ticker = yf.Ticker(symbol.strip())
        start_s = start.isoformat() if start is not None else None
        end_exclusive = (end + timedelta(days=1)).isoformat() if end is not None else None
        df = ticker.history(
            start=start_s,
            end=end_exclusive,
            interval="1d",
            auto_adjust=True,
            timeout=int(timeout_seconds),
        )
        if df is None or df.empty:
            return []
        bars: list[DailyBar] = []
        for ts, row in df.iterrows():
            trade_date = ts.date() if hasattr(ts, "date") else date.fromisoformat(str(ts)[:10])
            bars.append(
                DailyBar(
                    trade_date=trade_date,
                    open=float(row["Open"]),
                    high=float(row["High"]),
                    low=float(row["Low"]),
                    close=float(row["Close"]),
                    volume=int(row["Volume"]),
                )
            )
        return filter_sort_daily_range(bars, start=start, end=end)
