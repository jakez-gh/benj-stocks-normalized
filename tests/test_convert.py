"""Tests for :mod:`benj_stocks_normalized.convert`."""

from datetime import date

from daily_bars_core import DailyBar

from benj_stocks_normalized.convert import daily_bars_to_normalized
from benj_stocks_normalized.schema import NormalizedDailyBar


def test_daily_bars_to_normalized_single_row() -> None:
    bars = [DailyBar(date(2024, 1, 2), 10.0, 11.0, 9.0, 10.5, 1_000_000)]
    out = daily_bars_to_normalized(bars, "AAPL")
    assert out == [
        NormalizedDailyBar(
            "AAPL",
            date(2024, 1, 2),
            10.0,
            11.0,
            9.0,
            10.5,
            1_000_000.0,
            None,
        )
    ]


def test_daily_bars_to_normalized_empty() -> None:
    assert daily_bars_to_normalized([], "AAPL") == []


def test_daily_bars_to_normalized_preserves_order_and_symbol() -> None:
    bars = [
        DailyBar(date(2024, 1, 2), 1.0, 2.0, 0.5, 1.5, 100),
        DailyBar(date(2024, 1, 3), 1.5, 2.5, 1.0, 2.0, 200),
    ]
    out = daily_bars_to_normalized(bars, "ZZZ")
    assert len(out) == 2
    assert out[0].symbol == "ZZZ" and out[1].symbol == "ZZZ"
    assert out[0].trade_date == date(2024, 1, 2)
    assert out[1].trade_date == date(2024, 1, 3)
    assert out[0].volume == 100.0 and out[1].volume == 200.0


def test_daily_bars_to_normalized_coerces_volume_to_float() -> None:
    bars = [DailyBar(date(2024, 1, 2), 1.0, 1.0, 1.0, 1.0, 42)]
    out = daily_bars_to_normalized(bars, "X")
    assert out[0].volume == 42.0
    assert isinstance(out[0].volume, float)


def test_daily_bars_to_normalized_clears_close_zscore() -> None:
    bars = [DailyBar(date(2024, 1, 2), 1.0, 1.0, 1.0, 1.0, 1)]
    out = daily_bars_to_normalized(bars, "X")
    assert out[0].close_zscore is None
