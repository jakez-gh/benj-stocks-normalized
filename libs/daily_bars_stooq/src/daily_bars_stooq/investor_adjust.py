from __future__ import annotations

import math
from datetime import date, timedelta

import pandas as pd
import yfinance as yf

from daily_bars_core import DailyBar


def stooq_symbol_to_yahoo_ticker(stooq_symbol: str) -> str:
    s = stooq_symbol.strip().lower()
    if s.endswith(".us"):
        return s[:-3].upper()
    return stooq_symbol.strip().upper()


def _row_for_date(df: pd.DataFrame, d: date) -> pd.Series | None:
    for idx, row in df.iterrows():
        ts = idx.date() if hasattr(idx, "date") else idx
        if ts == d:
            return row
    return None


def adjust_stooq_bars_with_yfinance(
    bars: list[DailyBar],
    yahoo_ticker: str,
    *,
    timeout_seconds: float,
) -> list[DailyBar]:
    """Scale Stooq (raw) OHLCV using Yahoo same-day adjusted vs raw ratios.

    Stooq's daily CSV is not split/dividend-adjusted. We use yfinance's
    auto_adjust split point for the same listing to derive per-day price and
    volume multipliers so the series matches an investor-continuous view.
    """
    if not bars:
        return []
    start = bars[0].trade_date
    end = bars[-1].trade_date
    ticker = yf.Ticker(yahoo_ticker)
    end_exclusive = end + timedelta(days=1)
    kw: dict = {
        "start": start.isoformat(),
        "end": end_exclusive.isoformat(),
        "interval": "1d",
        "timeout": int(timeout_seconds),
    }
    raw_df = ticker.history(**kw, auto_adjust=False)
    adj_df = ticker.history(**kw, auto_adjust=True)
    if raw_df is None or raw_df.empty or adj_df is None or adj_df.empty:
        return list(bars)

    out: list[DailyBar] = []
    for b in bars:
        pr, vr = _price_and_volume_ratios(raw_df, adj_df, b.trade_date)
        out.append(
            DailyBar(
                trade_date=b.trade_date,
                open=b.open * pr,
                high=b.high * pr,
                low=b.low * pr,
                close=b.close * pr,
                volume=max(0, int(round(b.volume * vr))),
            )
        )
    return out


def _price_and_volume_ratios(raw_df: pd.DataFrame, adj_df: pd.DataFrame, d: date) -> tuple[float, float]:
    raw = _row_for_date(raw_df, d)
    adj = _row_for_date(adj_df, d)
    if raw is None or adj is None:
        return 1.0, 1.0
    rc = float(raw["Close"])
    ac = float(adj["Close"])
    rv = float(raw["Volume"])
    av = float(adj["Volume"])
    pr = ac / rc if rc and not math.isnan(rc) else 1.0
    if math.isnan(pr):
        pr = 1.0
    vr = av / rv if rv and not math.isnan(rv) and rv != 0 else 1.0
    if math.isnan(vr):
        vr = 1.0
    return pr, vr
