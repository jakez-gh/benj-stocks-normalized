from datetime import date
from io import BytesIO
from unittest.mock import patch

from daily_bars_stooq import retrieve_daily_bars_stooq


def test_retrieve_daily_bars_stooq_sorts_chronologically():
    csv_body = (
        "Date,Open,High,Low,Close,Volume\n"
        "2024-01-03,3,3,3,3,30\n"
        "2024-01-01,1,1,1,1,10\n"
        "2024-01-02,2,2,2,2,20\n"
    )
    with (
        patch("daily_bars_stooq.stooq.urlopen", return_value=BytesIO(csv_body.encode())),
        patch(
            "daily_bars_stooq.stooq.adjust_stooq_bars_with_yfinance",
            side_effect=lambda b, *_a, **_k: b,
        ),
    ):
        bars = retrieve_daily_bars_stooq("x")
    assert [b.trade_date for b in bars] == [
        date(2024, 1, 1),
        date(2024, 1, 2),
        date(2024, 1, 3),
    ]
