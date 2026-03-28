from datetime import date

import pytest

from daily_bars_stooq.parse import parse_stooq_daily_csv


def test_parse_stooq_daily_csv_empty_body_returns_empty_list():
    assert parse_stooq_daily_csv("") == []


def test_parse_stooq_daily_csv_header_only_returns_empty_list():
    assert parse_stooq_daily_csv("Date,Open,High,Low,Close,Volume\n") == []


def test_parse_stooq_daily_csv_parses_rows_newest_first():
    text = """Date,Open,High,Low,Close,Volume
2024-01-03,10.5,12.0,10.0,11.5,2000000
2024-01-02,10.0,11.0,9.5,10.5,1000000
"""
    bars = parse_stooq_daily_csv(text)
    assert len(bars) == 2
    assert bars[0].trade_date == date(2024, 1, 3)
    assert bars[0].open == 10.5
    assert bars[0].high == 12.0
    assert bars[0].low == 10.0
    assert bars[0].close == 11.5
    assert bars[0].volume == 2_000_000
    assert bars[1].trade_date == date(2024, 1, 2)


def test_parse_stooq_daily_csv_raises_on_malformed_row():
    text = """Date,Open,High,Low,Close,Volume
not-a-date,1,2,3,4,5
"""
    with pytest.raises(ValueError, match="parse"):
        parse_stooq_daily_csv(text)
