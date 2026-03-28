from datetime import date

from daily_bars_core import DailyBar, align_by_date, mismatch_summary_for_date


def test_align_by_date_keeps_chronological_intersection():
    a = [
        DailyBar(date(2024, 1, 1), 1, 1, 1, 1, 10),
        DailyBar(date(2024, 1, 2), 2, 2, 2, 2, 20),
    ]
    b = [
        DailyBar(date(2024, 1, 2), 2.01, 2, 2, 2, 20),
        DailyBar(date(2024, 1, 3), 3, 3, 3, 3, 30),
    ]
    pairs = align_by_date(a, b)
    assert len(pairs) == 1
    assert pairs[0][0].trade_date == date(2024, 1, 2)


def test_mismatch_summary_detects_close_within_tolerance():
    left = DailyBar(date(2024, 1, 1), 10.0, 11.0, 9.0, 10.0, 1_000_000)
    right = DailyBar(date(2024, 1, 1), 10.0, 11.0, 9.0, 10.0005, 1_000_000)
    assert mismatch_summary_for_date(left, right, rel_tol=1e-3) == []


def test_mismatch_summary_flags_large_close_gap():
    left = DailyBar(date(2024, 1, 1), 10.0, 11.0, 9.0, 10.0, 1_000_000)
    right = DailyBar(date(2024, 1, 1), 10.0, 11.0, 9.0, 10.5, 1_000_000)
    fields = mismatch_summary_for_date(left, right, rel_tol=1e-4)
    assert "close" in fields
