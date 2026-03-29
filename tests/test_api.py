"""Tests for :mod:`benj_stocks_normalized.api` (benj-stocks calls mocked)."""

from datetime import date
from unittest.mock import MagicMock, patch

from daily_bars import DegradationReport
from daily_bars_core import DailyBar

from benj_stocks_normalized.api import fetch_normalized_daily_bars, fetch_tanh_delta_daily_bars
from benj_stocks_normalized.schema import NormalizedDailyBar, TanhDeltaDailyBar


def _sample_report() -> DegradationReport:
    return DegradationReport(
        sources_attempted=("yahoo",),
        sources_succeeded=("yahoo",),
        sources_failed=(),
        errors={},
        bar_counts={"yahoo": 1},
    )


@patch("benj_stocks_normalized.api.fetch_daily_bars_with_degradation")
@patch("benj_stocks_normalized.api.build_source_registry")
def test_fetch_normalized_builds_registry_when_none(
    mock_build: MagicMock,
    mock_fetch: MagicMock,
) -> None:
    reg = {"yahoo": MagicMock()}
    mock_build.return_value = reg
    mock_fetch.return_value = (
        [DailyBar(date(2024, 1, 2), 10.0, 11.0, 9.0, 10.0, 100)],
        _sample_report(),
    )

    bars, report = fetch_normalized_daily_bars("AAPL", start=date(2024, 1, 1))

    mock_build.assert_called_once_with(alpha_vantage_api_key=None)
    mock_fetch.assert_called_once()
    kwargs = mock_fetch.call_args.kwargs
    assert kwargs["start"] == date(2024, 1, 1)
    assert mock_fetch.call_args.args[0] is reg
    assert mock_fetch.call_args.args[1] == "AAPL"
    assert len(bars) == 1
    assert bars[0] == NormalizedDailyBar(
        "AAPL", date(2024, 1, 2), 10.0, 11.0, 9.0, 10.0, 100.0, None
    )
    assert report is mock_fetch.return_value[1]


@patch("benj_stocks_normalized.api.fetch_daily_bars_with_degradation")
@patch("benj_stocks_normalized.api.build_source_registry")
def test_fetch_normalized_skips_build_when_registry_passed(
    mock_build: MagicMock,
    mock_fetch: MagicMock,
) -> None:
    custom = {"yahoo": MagicMock()}
    mock_fetch.return_value = ([], _sample_report())

    fetch_normalized_daily_bars("X", registry=custom)

    mock_build.assert_not_called()
    assert mock_fetch.call_args.args[0] is custom


@patch("benj_stocks_normalized.api.fetch_daily_bars_with_degradation")
@patch("benj_stocks_normalized.api.build_source_registry")
def test_fetch_normalized_forwards_api_key_to_build_registry(
    mock_build: MagicMock,
    mock_fetch: MagicMock,
) -> None:
    mock_build.return_value = {"yahoo": MagicMock()}
    mock_fetch.return_value = ([], _sample_report())

    fetch_normalized_daily_bars("X", alpha_vantage_api_key="secret")

    mock_build.assert_called_once_with(alpha_vantage_api_key="secret")


@patch("benj_stocks_normalized.api.fetch_daily_bars_with_degradation")
@patch("benj_stocks_normalized.api.build_source_registry")
def test_fetch_normalized_forwards_optional_fetch_kwargs(
    mock_build: MagicMock,
    mock_fetch: MagicMock,
) -> None:
    registry = {"yahoo": MagicMock()}
    mock_fetch.return_value = ([], _sample_report())
    symbols_by_source = {"yahoo": "AAPL", "stooq": "aapl.us"}

    fetch_normalized_daily_bars(
        "AAPL",
        end=date(2024, 2, 1),
        timeout_seconds=5.0,
        source_order=("stooq", "yahoo"),
        symbols_by_source=symbols_by_source,
        relative_close_epsilon=0.01,
        registry=registry,
    )

    mock_build.assert_not_called()
    kw = mock_fetch.call_args.kwargs
    assert kw["end"] == date(2024, 2, 1)
    assert kw["timeout_seconds"] == 5.0
    assert kw["source_order"] == ("stooq", "yahoo")
    assert kw["symbols_by_source"] is symbols_by_source
    assert kw["relative_close_epsilon"] == 0.01


@patch("benj_stocks_normalized.api.fetch_normalized_daily_bars")
def test_fetch_tanh_delta_delegates_and_maps(mock_fetch_norm: MagicMock) -> None:
    norm = [
        NormalizedDailyBar("X", date(2024, 1, 1), 100.0, 100.0, 100.0, 100.0, 1.0, None),
        NormalizedDailyBar("X", date(2024, 1, 2), 110.0, 110.0, 110.0, 110.0, 1.0, None),
    ]
    rep = _sample_report()
    mock_fetch_norm.return_value = (norm, rep)
    registry = {"y": MagicMock()}

    td, out_report = fetch_tanh_delta_daily_bars(
        "X",
        delta_scale=1.0,
        drop_first=True,
        registry=registry,
    )

    mock_fetch_norm.assert_called_once()
    assert mock_fetch_norm.call_args.kwargs["registry"] is registry
    assert out_report is rep
    assert len(td) == 1
    assert td[0].trade_date == date(2024, 1, 2)
    assert isinstance(td[0], TanhDeltaDailyBar)


@patch("benj_stocks_normalized.api.fetch_normalized_daily_bars")
def test_fetch_tanh_delta_forwards_date_range_to_normalized(mock_fetch_norm: MagicMock) -> None:
    mock_fetch_norm.return_value = ([], _sample_report())
    start, end = date(2024, 1, 1), date(2024, 1, 31)
    reg = {"yahoo": MagicMock()}

    fetch_tanh_delta_daily_bars("AAPL", start=start, end=end, registry=reg, timeout_seconds=7.0)

    kw = mock_fetch_norm.call_args.kwargs
    assert kw["start"] is start
    assert kw["end"] is end
    assert kw["registry"] is reg
    assert kw["timeout_seconds"] == 7.0


@patch("benj_stocks_normalized.api.fetch_normalized_daily_bars")
def test_fetch_tanh_delta_drop_first_false_keeps_first_row(mock_fetch_norm: MagicMock) -> None:
    norm = [
        NormalizedDailyBar("X", date(2024, 1, 1), 100.0, 100.0, 100.0, 100.0, 1.0, None),
        NormalizedDailyBar("X", date(2024, 1, 2), 110.0, 110.0, 110.0, 110.0, 1.0, None),
    ]
    mock_fetch_norm.return_value = (norm, _sample_report())

    td, _ = fetch_tanh_delta_daily_bars("X", drop_first=False)

    assert len(td) == 2
    assert td[0].open_tanh == 0.0
