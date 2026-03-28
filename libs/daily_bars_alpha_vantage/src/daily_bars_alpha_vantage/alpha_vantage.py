from __future__ import annotations

import json
import os
from datetime import date
from urllib.parse import urlencode
from urllib.request import urlopen

from daily_bars_core import DailyBar, filter_sort_daily_range

_ALPHA_VANTAGE_URL = "https://www.alphavantage.co/query"


def parse_alpha_vantage_daily_json(payload: str) -> list[DailyBar]:
    data = json.loads(payload)
    if "Note" in data:
        raise ValueError("Alpha Vantage rate limit or note response; retry later or upgrade plan")
    if "Error Message" in data:
        raise ValueError(f"Alpha Vantage error: {data['Error Message']}")
    series = data.get("Time Series (Daily)")
    if not series:
        raise ValueError("Alpha Vantage response missing Time Series (Daily)")
    bars: list[DailyBar] = []
    for d_str, row in series.items():
        y, m, day = (int(x) for x in d_str.split("-"))
        trade_date = date(y, m, day)
        if "5. adjusted close" not in row:
            raise ValueError(
                "expected Alpha Vantage TIME_SERIES_DAILY_ADJUSTED payload (missing '5. adjusted close')"
            )
        o = float(row["1. open"])
        h = float(row["2. high"])
        low = float(row["3. low"])
        c = float(row["4. close"])
        ac = float(row["5. adjusted close"])
        v = int(float(row["6. volume"]))
        ratio = ac / c if c else 1.0
        bars.append(
            DailyBar(
                trade_date=trade_date,
                open=o * ratio,
                high=h * ratio,
                low=low * ratio,
                close=ac,
                volume=v,
            )
        )
    return sorted(bars, key=lambda b: b.trade_date)


class AlphaVantageDailyBarsSource:
    name = "alpha_vantage"

    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key if api_key is not None else os.environ.get("ALPHAVANTAGE_API_KEY", "")

    def fetch_daily_bars(
        self,
        symbol: str,
        *,
        start: date | None = None,
        end: date | None = None,
        timeout_seconds: float = 30.0,
    ) -> list[DailyBar]:
        if not self._api_key:
            raise ValueError(
                "Alpha Vantage requires an API key: pass AlphaVantageDailyBarsSource(api_key=...) "
                "or set ALPHAVANTAGE_API_KEY"
            )
        query = urlencode(
            {
                "function": "TIME_SERIES_DAILY_ADJUSTED",
                "symbol": symbol.strip().upper(),
                "apikey": self._api_key,
                "outputsize": "full",
            }
        )
        url = f"{_ALPHA_VANTAGE_URL}?{query}"
        with urlopen(url, timeout=timeout_seconds) as resp:
            body = resp.read().decode("utf-8")
        bars = parse_alpha_vantage_daily_json(body)
        return filter_sort_daily_range(bars, start=start, end=end)
