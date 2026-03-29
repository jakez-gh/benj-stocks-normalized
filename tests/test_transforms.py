import math
from datetime import date

import pytest

from benj_stocks_normalized import (
    NormalizedDailyBar,
    TanhDeltaDailyBar,
    scale_ohlc_by_first_close,
    with_close_zscore,
    with_tanh_deltas_from_previous,
)


def test_scale_ohlc_by_first_close() -> None:
    base = [
        NormalizedDailyBar("X", date(2024, 1, 1), 100.0, 102.0, 99.0, 100.0, 500.0, None),
        NormalizedDailyBar("X", date(2024, 1, 2), 100.0, 104.0, 100.0, 102.0, 600.0, None),
    ]
    scaled = scale_ohlc_by_first_close(base)
    assert scaled[0].close == 1.0
    assert scaled[0].volume == 500.0
    assert scaled[1].close == pytest.approx(1.02)


def test_scale_ohlc_by_first_close_preserves_close_zscore() -> None:
    base = [
        NormalizedDailyBar("X", date(2024, 1, 1), 100.0, 100.0, 100.0, 100.0, 1.0, 0.5),
    ]
    scaled = scale_ohlc_by_first_close(base)
    assert scaled[0].close_zscore == 0.5


def test_scale_ohlc_by_first_close_empty() -> None:
    assert scale_ohlc_by_first_close([]) == []


def test_scale_ohlc_by_first_close_zero_raises() -> None:
    base = [
        NormalizedDailyBar("X", date(2024, 1, 1), 0.0, 0.0, 0.0, 0.0, 0.0, None),
    ]
    with pytest.raises(ValueError, match="first close"):
        scale_ohlc_by_first_close(base)


def test_with_close_zscore_empty() -> None:
    assert with_close_zscore([]) == []


def test_with_close_zscore() -> None:
    base = [
        NormalizedDailyBar("X", date(2024, 1, 1), 1.0, 1.0, 1.0, 10.0, 1.0, None),
        NormalizedDailyBar("X", date(2024, 1, 2), 1.0, 1.0, 1.0, 20.0, 1.0, None),
    ]
    z = with_close_zscore(base)
    assert z[0].close_zscore == pytest.approx(-1.0)
    assert z[1].close_zscore == pytest.approx(1.0)


def test_with_close_zscore_flat_is_zero() -> None:
    base = [
        NormalizedDailyBar("X", date(2024, 1, 1), 5.0, 5.0, 5.0, 5.0, 1.0, None),
        NormalizedDailyBar("X", date(2024, 1, 2), 5.0, 5.0, 5.0, 5.0, 1.0, None),
    ]
    z = with_close_zscore(base)
    assert z[0].close_zscore == 0.0
    assert z[1].close_zscore == 0.0


def test_tanh_deltas_empty() -> None:
    assert with_tanh_deltas_from_previous([]) == []


def test_tanh_deltas_single_bar_drop_first_yields_empty() -> None:
    one = [
        NormalizedDailyBar("X", date(2024, 1, 1), 100.0, 100.0, 100.0, 100.0, 1.0, None),
    ]
    assert with_tanh_deltas_from_previous(one, drop_first=True) == []


def test_tanh_deltas_single_bar_keep_first_is_all_zeros() -> None:
    one = [
        NormalizedDailyBar("X", date(2024, 1, 1), 100.0, 100.0, 100.0, 100.0, 1.0, None),
    ]
    out = with_tanh_deltas_from_previous(one, drop_first=False)
    assert out == [TanhDeltaDailyBar("X", date(2024, 1, 1), 0.0, 0.0, 0.0, 0.0, 0.0)]


def test_tanh_deltas_delta_scale_zero_flattens_interior_moves() -> None:
    base = [
        NormalizedDailyBar("X", date(2024, 1, 1), 100.0, 100.0, 100.0, 100.0, 1_000.0, None),
        NormalizedDailyBar("X", date(2024, 1, 2), 200.0, 200.0, 200.0, 200.0, 2_000.0, None),
    ]
    out = with_tanh_deltas_from_previous(base, delta_scale=0.0, drop_first=True)
    assert out[0].open_tanh == 0.0
    assert out[0].close_tanh == 0.0


def test_tanh_deltas_drop_first() -> None:
    base = [
        NormalizedDailyBar("X", date(2024, 1, 1), 100.0, 102.0, 99.0, 100.0, 1_000.0, None),
        NormalizedDailyBar("X", date(2024, 1, 2), 110.0, 112.0, 109.0, 110.0, 1_100.0, None),
    ]
    out = with_tanh_deltas_from_previous(base, drop_first=True)
    assert len(out) == 1
    assert out[0].trade_date == date(2024, 1, 2)
    assert out[0].open_tanh == math.tanh(0.1)
    assert out[0].close_tanh == math.tanh(0.1)
    assert out[0].volume_tanh == math.tanh(0.1)


def test_tanh_deltas_keep_first_zeros() -> None:
    base = [
        NormalizedDailyBar("X", date(2024, 1, 1), 100.0, 102.0, 99.0, 100.0, 1_000.0, None),
        NormalizedDailyBar("X", date(2024, 1, 2), 110.0, 112.0, 109.0, 110.0, 1_100.0, None),
    ]
    out = with_tanh_deltas_from_previous(base, drop_first=False)
    assert len(out) == 2
    assert out[0] == TanhDeltaDailyBar("X", date(2024, 1, 1), 0.0, 0.0, 0.0, 0.0, 0.0)
    assert out[1].open_tanh == math.tanh(0.1)


def test_tanh_deltas_prev_zero_positive_today_is_one() -> None:
    base = [
        NormalizedDailyBar("X", date(2024, 1, 1), 100.0, 102.0, 99.0, 100.0, 0.0, None),
        NormalizedDailyBar("X", date(2024, 1, 2), 110.0, 112.0, 109.0, 110.0, 500.0, None),
    ]
    out = with_tanh_deltas_from_previous(base, drop_first=True)
    assert out[0].volume_tanh == 1.0


def test_tanh_deltas_positive_prev_zero_today_is_minus_one() -> None:
    base = [
        NormalizedDailyBar("X", date(2024, 1, 1), 100.0, 102.0, 99.0, 100.0, 500.0, None),
        NormalizedDailyBar("X", date(2024, 1, 2), 110.0, 112.0, 109.0, 110.0, 0.0, None),
    ]
    out = with_tanh_deltas_from_previous(base, drop_first=True)
    assert out[0].volume_tanh == -1.0


def test_tanh_deltas_both_zero_is_zero() -> None:
    base = [
        NormalizedDailyBar("X", date(2024, 1, 1), 100.0, 102.0, 99.0, 100.0, 0.0, None),
        NormalizedDailyBar("X", date(2024, 1, 2), 110.0, 112.0, 109.0, 110.0, 0.0, None),
    ]
    out = with_tanh_deltas_from_previous(base, drop_first=True)
    assert out[0].volume_tanh == 0.0


def test_tanh_deltas_same_positive_is_zero() -> None:
    base = [
        NormalizedDailyBar("X", date(2024, 1, 1), 100.0, 102.0, 99.0, 100.0, 1_000.0, None),
        NormalizedDailyBar("X", date(2024, 1, 2), 100.0, 102.0, 99.0, 100.0, 1_000.0, None),
    ]
    out = with_tanh_deltas_from_previous(base, drop_first=True)
    assert out[0].open_tanh == 0.0
    assert out[0].close_tanh == 0.0
    assert out[0].volume_tanh == 0.0


def test_tanh_deltas_mismatched_symbol_raises() -> None:
    base = [
        NormalizedDailyBar("X", date(2024, 1, 1), 100.0, 100.0, 100.0, 100.0, 1.0, None),
        NormalizedDailyBar("Y", date(2024, 1, 2), 101.0, 101.0, 101.0, 101.0, 1.0, None),
    ]
    with pytest.raises(ValueError, match="single symbol"):
        with_tanh_deltas_from_previous(base)


def test_tanh_deltas_negative_scale_raises() -> None:
    base = [
        NormalizedDailyBar("X", date(2024, 1, 1), 100.0, 100.0, 100.0, 100.0, 1.0, None),
    ]
    with pytest.raises(ValueError, match="delta_scale"):
        with_tanh_deltas_from_previous(base, delta_scale=-1.0)
