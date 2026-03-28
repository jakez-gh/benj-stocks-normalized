from datetime import date
from io import BytesIO
from unittest.mock import patch

from daily_bars_alpha_vantage import AlphaVantageDailyBarsSource


def test_alpha_vantage_source_fetches_and_filters_inclusive_end():
    payload = """
{
  "Time Series (Daily)": {
    "2024-01-01": {"1. open": "1", "2. high": "1", "3. low": "1", "4. close": "1", "5. adjusted close": "1", "6. volume": "10", "7. dividend amount": "0", "8. split coefficient": "1.0"},
    "2024-01-02": {"1. open": "2", "2. high": "2", "3. low": "2", "4. close": "2", "5. adjusted close": "2", "6. volume": "20", "7. dividend amount": "0", "8. split coefficient": "1.0"},
    "2024-01-03": {"1. open": "3", "2. high": "3", "3. low": "3", "4. close": "3", "5. adjusted close": "3", "6. volume": "30", "7. dividend amount": "0", "8. split coefficient": "1.0"}
  }
}
"""

    with patch("daily_bars_alpha_vantage.alpha_vantage.urlopen", return_value=BytesIO(payload.encode())):
        src = AlphaVantageDailyBarsSource(api_key="testkey")
        bars = src.fetch_daily_bars(
            "IBM",
            start=date(2024, 1, 2),
            end=date(2024, 1, 2),
        )

    assert len(bars) == 1
    assert bars[0].trade_date == date(2024, 1, 2)
    assert bars[0].close == 2.0
