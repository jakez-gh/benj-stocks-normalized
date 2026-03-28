from datetime import date
from io import BytesIO
from unittest.mock import MagicMock, patch

import pandas as pd

from daily_bars_stooq import retrieve_daily_bars_stooq, stooq_symbol_to_yahoo_ticker


def test_stooq_symbol_to_yahoo_ticker_maps_us_suffix():
    assert stooq_symbol_to_yahoo_ticker("aapl.us") == "AAPL"


def test_retrieve_stooq_scales_ohlcv_with_yahoo_adjusted_vs_raw_ratios():
    csv_body = (
        "Date,Open,High,Low,Close,Volume\n"
        "2024-01-02,200.0,200.0,200.0,200.0,1000\n"
    )
    raw_df = pd.DataFrame(
        {"Close": [200.0], "Volume": [1000.0]},
        index=pd.to_datetime(["2024-01-02"]),
    )
    adj_df = pd.DataFrame(
        {"Close": [100.0], "Volume": [2000.0]},
        index=pd.to_datetime(["2024-01-02"]),
    )
    mock_ticker = MagicMock()
    mock_ticker.history.side_effect = [raw_df, adj_df]

    with (
        patch("daily_bars_stooq.stooq.urlopen", return_value=BytesIO(csv_body.encode())),
        patch("daily_bars_stooq.investor_adjust.yf.Ticker", return_value=mock_ticker),
    ):
        bars = retrieve_daily_bars_stooq("TEST.US", adjust_for_investor_series=True)

    assert len(bars) == 1
    b = bars[0]
    assert b.trade_date == date(2024, 1, 2)
    assert b.open == 100.0
    assert b.high == 100.0
    assert b.low == 100.0
    assert b.close == 100.0
    assert b.volume == 2000
    assert mock_ticker.history.call_count == 2
