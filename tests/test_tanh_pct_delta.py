"""Unit tests for :func:`benj_stocks_normalized.transforms._tanh_pct_delta` (pure helper)."""

import math

import pytest

from benj_stocks_normalized.transforms import _tanh_pct_delta


@pytest.mark.parametrize(
    ("prev", "curr", "expected"),
    [
        (0.0, 0.0, 0.0),
        (-1.0, 0.0, 0.0),
        (-3.0, -2.0, 0.0),
        (-1.0, 5.0, 1.0),
        (0.0, 1.0, 1.0),
        (0.0, 0.01, 1.0),
        (100.0, 0.0, -1.0),
        (100.0, -1.0, -1.0),
        (10.0, 10.0, 0.0),
    ],
)
def test_tanh_pct_delta_sentinels(prev: float, curr: float, expected: float) -> None:
    assert _tanh_pct_delta(prev, curr, 1.0) == expected


def test_tanh_pct_delta_uses_tanh_for_positive_moves() -> None:
    assert _tanh_pct_delta(100.0, 110.0, 1.0) == pytest.approx(math.tanh(0.1))
    assert _tanh_pct_delta(100.0, 90.0, 1.0) == pytest.approx(math.tanh(-0.1))


def test_tanh_pct_delta_only_uses_tanh_when_both_effective_levels_positive() -> None:
    """After coercing ``<= 0`` to 0, tanh applies only when both sides are ``> 0``."""
    assert _tanh_pct_delta(100.0, -50.0, 1.0) == -1.0
    assert _tanh_pct_delta(-10.0, 100.0, 1.0) == 1.0
    assert _tanh_pct_delta(50.0, 100.0, 1.0) == pytest.approx(math.tanh(1.0))


def test_tanh_pct_delta_respects_delta_scale() -> None:
    assert _tanh_pct_delta(100.0, 110.0, 2.0) == pytest.approx(math.tanh(0.2))
    assert _tanh_pct_delta(100.0, 110.0, 0.0) == 0.0
