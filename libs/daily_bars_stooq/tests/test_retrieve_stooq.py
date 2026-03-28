from datetime import date
from io import BytesIO
from unittest.mock import patch

from daily_bars_core import DailyBar
from daily_bars_stooq import retrieve_daily_bars_stooq


def test_retrieve_daily_bars_stooq_requests_lowercase_symbol_in_url():
    csv_body = (
        "Date,Open,High,Low,Close,Volume\n"
        "2024-01-02,1.0,2.0,0.5,1.5,100\n"
    )

    captured = {}

    def fake_urlopen(url, timeout=None):
        captured["url"] = url
        return BytesIO(csv_body.encode())

    with (
        patch("daily_bars_stooq.stooq.urlopen", side_effect=fake_urlopen),
        patch(
            "daily_bars_stooq.stooq.adjust_stooq_bars_with_yfinance",
            side_effect=lambda b, *_a, **_k: b,
        ),
    ):
        retrieve_daily_bars_stooq("AAPL.US")

    assert "aapl.us" in str(captured["url"]).lower()


def test_retrieve_daily_bars_stooq_filters_by_start_and_end_inclusive():
    csv_body = (
        "Date,Open,High,Low,Close,Volume\n"
        "2024-01-01,1,1,1,1,10\n"
        "2024-01-02,2,2,2,2,20\n"
        "2024-01-03,3,3,3,3,30\n"
    )

    with (
        patch("daily_bars_stooq.stooq.urlopen", return_value=BytesIO(csv_body.encode())),
        patch(
            "daily_bars_stooq.stooq.adjust_stooq_bars_with_yfinance",
            side_effect=lambda b, *_a, **_k: b,
        ),
    ):
        bars = retrieve_daily_bars_stooq(
            "x",
            start=date(2024, 1, 2),
            end=date(2024, 1, 2),
        )

    assert bars == [
        DailyBar(
            trade_date=date(2024, 1, 2),
            open=2.0,
            high=2.0,
            low=2.0,
            close=2.0,
            volume=20,
        )
    ]
