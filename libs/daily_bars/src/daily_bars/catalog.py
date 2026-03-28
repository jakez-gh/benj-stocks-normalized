from __future__ import annotations

from daily_bars_alpha_vantage import AlphaVantageDailyBarsSource
from daily_bars_core import DailyBarsSource
from daily_bars_stooq import StooqDailyBarsSource
from daily_bars_yahoo import YahooDailyBarsSource


def build_source_registry(*, alpha_vantage_api_key: str | None = None) -> dict[str, DailyBarsSource]:
    return {
        "stooq": StooqDailyBarsSource(),
        "yahoo": YahooDailyBarsSource(),
        "alpha_vantage": AlphaVantageDailyBarsSource(api_key=alpha_vantage_api_key),
    }


def get_source(registry: dict[str, DailyBarsSource], name: str) -> DailyBarsSource:
    if name not in registry:
        raise KeyError(name)
    return registry[name]
