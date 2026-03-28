from datetime import date

from daily_bars import (
    DailyBar,
    DEFAULT_RELATIVE_CLOSE_EPSILON,
    fetch_daily_bars_with_degradation,
    fuse_daily_bars_by_consensus,
)


def test_fuse_empty_when_no_source_data():
    assert fuse_daily_bars_by_consensus({}, ("yahoo",)) == []


def test_fuse_single_source_unchanged():
    b = DailyBar(date(2024, 1, 1), 10.0, 11.0, 9.0, 10.5, 1_000)
    out = fuse_daily_bars_by_consensus({"yahoo": [b]}, ("yahoo", "stooq"))
    assert out == [b]


def test_fuse_two_sources_average_when_relative_close_agrees():
    b1 = DailyBar(date(2024, 1, 1), 10.0, 12.0, 9.0, 11.0, 1_000)
    b2 = DailyBar(date(2024, 1, 1), 10.0, 12.0, 9.0, 11.02, 1_200)
    out = fuse_daily_bars_by_consensus(
        {"yahoo": [b1], "stooq": [b2]},
        ("yahoo", "stooq"),
        relative_close_epsilon=0.005,
    )
    assert len(out) == 1
    assert out[0].close == (11.0 + 11.02) / 2
    assert out[0].volume == 1100


def test_fuse_two_sources_primary_when_close_disagrees_beyond_epsilon():
    y = DailyBar(date(2024, 1, 1), 1.0, 1.0, 1.0, 1.0, 10)
    s = DailyBar(date(2024, 1, 1), 2.0, 2.0, 2.0, 2.0, 20)
    out = fuse_daily_bars_by_consensus(
        {"yahoo": [y], "stooq": [s]},
        ("yahoo", "stooq"),
        relative_close_epsilon=0.005,
    )
    assert out == [y]


def test_fuse_three_sources_median_close_and_scales_reference_bar():
    # Closes 10, 11, 100 -> median 11; closest to 11 is 11 (stooq second in order? y=10, s=11, a=100)
    y = DailyBar(date(2024, 1, 1), 20.0, 22.0, 18.0, 10.0, 100)
    s = DailyBar(date(2024, 1, 1), 22.0, 24.0, 20.0, 11.0, 200)
    av = DailyBar(date(2024, 1, 1), 200.0, 220.0, 180.0, 100.0, 300)
    out = fuse_daily_bars_by_consensus(
        {"yahoo": [y], "stooq": [s], "alpha_vantage": [av]},
        ("yahoo", "stooq", "alpha_vantage"),
    )
    assert len(out) == 1
    assert out[0].close == 11.0
    # ref is stooq (close 11 == median); scale = 11/11 = 1
    assert out[0].open == 22.0
    assert out[0].volume == 200  # median of 100,200,300


def test_fuse_three_sources_tie_distance_to_median_prefers_earlier_source():
    # median of 10,10,12 is 10; yahoo and stooq both distance 0 -> pick yahoo
    y = DailyBar(date(2024, 1, 1), 5.0, 6.0, 4.0, 10.0, 100)
    s = DailyBar(date(2024, 1, 1), 5.0, 6.0, 4.0, 10.0, 200)
    av = DailyBar(date(2024, 1, 1), 6.0, 7.0, 5.0, 12.0, 300)
    out = fuse_daily_bars_by_consensus(
        {"yahoo": [y], "stooq": [s], "alpha_vantage": [av]},
        ("yahoo", "stooq", "alpha_vantage"),
    )
    assert out[0].close == 10.0
    scale = 10.0 / 10.0
    assert out[0].open == 5.0 * scale
    assert out[0].volume == 200  # median volume


def test_fuse_fills_dates_from_multiple_sources():
    y = DailyBar(date(2024, 1, 1), 1, 1, 1, 1, 10)
    s = DailyBar(date(2024, 1, 2), 2, 2, 2, 2, 20)
    out = fuse_daily_bars_by_consensus({"yahoo": [y], "stooq": [s]}, ("yahoo", "stooq"))
    assert [b.trade_date for b in out] == [date(2024, 1, 1), date(2024, 1, 2)]
    assert out[0].close == 1.0
    assert out[1].close == 2.0


def test_fuse_four_sources_even_count_median_close():
    y = DailyBar(date(2024, 1, 1), 1, 1, 1, 10.0, 10)
    s = DailyBar(date(2024, 1, 1), 1, 1, 1, 20.0, 20)
    a = DailyBar(date(2024, 1, 1), 1, 1, 1, 30.0, 30)
    x = DailyBar(date(2024, 1, 1), 1, 1, 1, 40.0, 40)
    out = fuse_daily_bars_by_consensus(
        {"yahoo": [y], "stooq": [s], "alpha_vantage": [a], "extra": [x]},
        ("yahoo", "stooq", "alpha_vantage", "extra"),
    )
    assert out[0].close == 25.0  # median of 10,20,30,40


def test_epsilon_boundary_two_sources_average_when_just_inside_default():
    b1 = DailyBar(date(2024, 1, 1), 100.0, 101.0, 99.0, 100.0, 1000)
    b2 = DailyBar(date(2024, 1, 1), 100.0, 101.0, 99.0, 100.4, 1000)
    out = fuse_daily_bars_by_consensus(
        {"yahoo": [b1], "stooq": [b2]},
        ("yahoo", "stooq"),
        relative_close_epsilon=DEFAULT_RELATIVE_CLOSE_EPSILON,
    )
    assert out[0].close == 100.2


def test_epsilon_boundary_two_sources_primary_when_just_outside_default():
    b1 = DailyBar(date(2024, 1, 1), 100.0, 101.0, 99.0, 100.0, 1000)
    b2 = DailyBar(date(2024, 1, 1), 100.0, 101.0, 99.0, 100.6, 1000)
    out = fuse_daily_bars_by_consensus(
        {"yahoo": [b1], "stooq": [b2]},
        ("yahoo", "stooq"),
        relative_close_epsilon=DEFAULT_RELATIVE_CLOSE_EPSILON,
    )
    assert out[0].close == 100.0


class _FakeSource:
    def __init__(self, name: str, bars: list[DailyBar] | None = None, exc: Exception | None = None) -> None:
        self.name = name
        self._bars = bars or []
        self._exc = exc

    def fetch_daily_bars(self, symbol: str, **kwargs):
        if self._exc is not None:
            raise self._exc
        return list(self._bars)


def test_fetch_degradation_applies_fusion_when_two_feeds_disagree():
    y = DailyBar(date(2024, 1, 1), 1, 1, 1, 1.0, 10)
    s = DailyBar(date(2024, 1, 1), 2, 2, 2, 2.0, 20)
    reg = {"yahoo": _FakeSource("yahoo", [y]), "stooq": _FakeSource("stooq", [s])}
    bars, _ = fetch_daily_bars_with_degradation(reg, "X", source_order=("yahoo", "stooq"))
    assert bars == [y]


def test_fetch_degradation_passes_epsilon_to_fusion():
    y = DailyBar(date(2024, 1, 1), 10.0, 10.0, 10.0, 100.0, 100)
    s = DailyBar(date(2024, 1, 1), 10.0, 10.0, 10.0, 100.4, 100)
    reg = {"yahoo": _FakeSource("yahoo", [y]), "stooq": _FakeSource("stooq", [s])}
    bars_loose, _ = fetch_daily_bars_with_degradation(
        reg, "X", source_order=("yahoo", "stooq"), relative_close_epsilon=0.01
    )
    assert bars_loose[0].close == 100.2
    bars_tight, _ = fetch_daily_bars_with_degradation(
        reg, "X", source_order=("yahoo", "stooq"), relative_close_epsilon=0.001
    )
    assert bars_tight[0].close == 100.0
