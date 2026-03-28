from datetime import date
from unittest.mock import MagicMock, patch

import pandas as pd

from daily_bars_yahoo import YahooDailyBarsSource


def test_yahoo_source_maps_history_to_sorted_daily_bars():
    df = pd.DataFrame(
        {
            "Open": [2.0, 1.0],
            "High": [2.1, 1.1],
            "Low": [1.9, 0.9],
            "Close": [2.05, 1.05],
            "Volume": [200, 100],
        },
        index=pd.to_datetime(["2024-01-02", "2024-01-01"]),
    )
    mock_ticker = MagicMock()
    mock_ticker.history.return_value = df

    with patch("daily_bars_yahoo.yahoo.yf.Ticker", return_value=mock_ticker):
        src = YahooDailyBarsSource()
        bars = src.fetch_daily_bars("AAPL")

    assert [b.trade_date for b in bars] == [date(2024, 1, 1), date(2024, 1, 2)]
    assert bars[0].volume == 100
    assert bars[1].close == 2.05
    mock_ticker.history.assert_called_once()
    kwargs = mock_ticker.history.call_args.kwargs
    assert kwargs.get("auto_adjust") is True
    assert kwargs.get("interval") == "1d"
