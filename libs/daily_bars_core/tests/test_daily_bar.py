from datetime import date

from daily_bars_core import DailyBar


def test_daily_bar_holds_date_and_ohlcv():
    bar = DailyBar(
        trade_date=date(2024, 1, 2),
        open=10.0,
        high=11.0,
        low=9.5,
        close=10.5,
        volume=1_000_000,
    )
    assert bar.trade_date == date(2024, 1, 2)
    assert bar.open == 10.0
    assert bar.high == 11.0
    assert bar.low == 9.5
    assert bar.close == 10.5
    assert bar.volume == 1_000_000


def test_daily_bar_instances_compare_equal_when_fields_match():
    a = DailyBar(
        trade_date=date(2024, 1, 2),
        open=1.0,
        high=2.0,
        low=0.5,
        close=1.5,
        volume=100,
    )
    b = DailyBar(
        trade_date=date(2024, 1, 2),
        open=1.0,
        high=2.0,
        low=0.5,
        close=1.5,
        volume=100,
    )
    assert a == b
