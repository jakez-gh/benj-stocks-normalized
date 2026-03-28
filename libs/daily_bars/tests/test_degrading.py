from datetime import date

from daily_bars import DailyBar, fetch_daily_bars_with_degradation


class _FakeSource:
    def __init__(self, name: str, bars: list[DailyBar] | None = None, exc: Exception | None = None) -> None:
        self.name = name
        self._bars = bars or []
        self._exc = exc

    def fetch_daily_bars(
        self,
        symbol: str,
        *,
        start: date | None = None,
        end: date | None = None,
        timeout_seconds: float = 30.0,
    ) -> list[DailyBar]:
        if self._exc is not None:
            raise self._exc
        return list(self._bars)


def test_fetch_degradation_skips_failed_sources_and_returns_bars():
    ok = DailyBar(date(2024, 1, 1), 1, 1, 1, 1, 1)
    reg = {
        "yahoo": _FakeSource("yahoo", exc=OSError("offline")),
        "stooq": _FakeSource("stooq", bars=[ok]),
        "alpha_vantage": _FakeSource("alpha_vantage", exc=TimeoutError("slow")),
    }
    bars, report = fetch_daily_bars_with_degradation(
        reg,
        "X",
        source_order=("yahoo", "stooq", "alpha_vantage"),
    )
    assert bars == [ok]
    assert report.sources_failed == ("yahoo", "alpha_vantage")
    assert "stooq" in report.sources_succeeded
    assert report.errors["yahoo"].startswith("OSError:")


def test_fetch_degradation_uses_symbols_by_source():
    sym_used: dict[str, str] = {}

    class _Recording(_FakeSource):
        def fetch_daily_bars(self, symbol: str, **kwargs):
            sym_used[self.name] = symbol
            return []

    reg = {
        "yahoo": _Recording("yahoo"),
        "stooq": _Recording("stooq"),
    }
    fetch_daily_bars_with_degradation(
        reg,
        "DEFAULT",
        symbols_by_source={"stooq": "aapl.us", "yahoo": "AAPL"},
    )
    assert sym_used["yahoo"] == "AAPL"
    assert sym_used["stooq"] == "aapl.us"


def test_fetch_degradation_returns_empty_without_raising_when_all_fail():
    reg = {"yahoo": _FakeSource("yahoo", exc=RuntimeError("nope"))}
    bars, report = fetch_daily_bars_with_degradation(reg, "X", source_order=("yahoo",))
    assert bars == []
    assert report.sources_failed == ("yahoo",)
    assert not report.sources_succeeded
