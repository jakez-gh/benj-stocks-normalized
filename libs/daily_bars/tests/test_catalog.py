import pytest

from daily_bars import build_source_registry, get_source


def test_get_source_returns_all_three_names():
    reg = build_source_registry(alpha_vantage_api_key="k")
    for name in ("stooq", "yahoo", "alpha_vantage"):
        assert get_source(reg, name).name == name


def test_get_source_unknown_raises():
    reg = build_source_registry(alpha_vantage_api_key="k")
    with pytest.raises(KeyError):
        get_source(reg, "nope")
