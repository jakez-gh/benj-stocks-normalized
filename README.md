# benj-stocks-normalized

Python library that builds on **[benj-stocks](https://github.com/jakez-gh/benj-stocks)** (`daily-bars` and friends) to expose a **stable, analysis-oriented** view of the same investor-continuous daily OHLCV data.

## Role

- **Data source**: [benj-stocks](https://github.com/jakez-gh/benj-stocks) (`daily_bars.fetch_daily_bars_with_degradation`, fusion, vendor symbols).
- **This package**: `NormalizedDailyBar` (level OHLCV), optional **OHLC scaling** (first close = 1), **close z-scores** over the window, and **tanh day-over-day deltas** in `TanhDeltaDailyBar` (primary normalized signal for models).

### Tanh deltas (default story)

Each field is compared to **yesterday’s same field** (open vs prior open, …, volume vs prior volume). **Any price or volume ≤ 0 is treated as 0** before the rules run.

**Boundary semantics** (per field, after that coercion): both effective levels **0** → **0.0**; **0 → positive** → **1.0**; **positive → 0** → **−1.0**. When **both prior and current are > 0** and **equal** → **0.0**; when **both > 0** and **unequal** → `tanh(delta_scale * (current − prior) / prior)` in **(−1, 1)**. **Volume** follows the same rules.

We use **per-field** deltas rather than a single tanh anchored only to yesterday’s close for all of O/H/L/C: that keeps gaps and intraday structure interpretable. With `drop_first=True` (default), the first row is omitted because there is no prior session.

## Install

Dependencies are pulled from the `main` branch of benj-stocks via PEP 508 Git URLs (see `pyproject.toml`).

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
```

## Usage

```python
from datetime import date

from benj_stocks_normalized import (
    fetch_normalized_daily_bars,
    scale_ohlc_by_first_close,
    with_close_zscore,
)

bars, report = fetch_normalized_daily_bars(
    "AAPL",
    start=date(2024, 1, 1),
    end=date(2024, 6, 30),
    symbols_by_source={
        "yahoo": "AAPL",
        "stooq": "aapl.us",
        "alpha_vantage": "AAPL",
    },
)

scaled = scale_ohlc_by_first_close(bars)
z = with_close_zscore(scaled)

for b in z[:5]:
    print(b.trade_date, b.close, b.close_zscore)

print("sources failed:", report.sources_failed)
```

**Tanh deltas (end-to-end from GitHub benj-stocks):**

```python
from benj_stocks_normalized import fetch_tanh_delta_daily_bars

td, report = fetch_tanh_delta_daily_bars(
    "AAPL",
    start=date(2024, 1, 1),
    end=date(2024, 6, 30),
    symbols_by_source={"yahoo": "AAPL", "stooq": "aapl.us", "alpha_vantage": "AAPL"},
    delta_scale=1.0,
    drop_first=True,
)
for row in td[:5]:
    print(row.trade_date, row.open_tanh, row.close_tanh, row.volume_tanh)
```

Alpha Vantage: set `ALPHAVANTAGE_API_KEY` or pass `alpha_vantage_api_key=` into `fetch_normalized_daily_bars` or `fetch_tanh_delta_daily_bars`.

You can also pass a custom `registry=` from `daily_bars.build_source_registry` if you construct sources yourself.

## Testing

After `pip install -e ".[dev]"`, run:

```bash
python3 -m pytest tests/ -q
```

Tests are **strict and offline-friendly**: `daily_bars.fetch_daily_bars_with_degradation` is **mocked** in `tests/test_api.py`, so the suite does not hit Yahoo/Stooq/Alpha Vantage. **Convert**, **transforms**, and **`_tanh_pct_delta`** semantics are covered directly; there is **no** live end-to-end network test in CI yet—add a manual or opt-in integration test if you want that.

## API

| Export | Purpose |
|--------|--------|
| `fetch_normalized_daily_bars` | Fetch fused bars from `daily_bars`, return `list[NormalizedDailyBar]` + `DegradationReport` |
| `fetch_tanh_delta_daily_bars` | Same fetch + `with_tanh_deltas_from_previous` (`delta_scale`, `drop_first`, same kwargs as above) |
| `daily_bars_to_normalized` | Map existing `DailyBar` rows to `NormalizedDailyBar` |
| `scale_ohlc_by_first_close` | Normalize OHLC by the first bar’s close; volume unchanged (shares) |
| `with_close_zscore` | Population z-score of close over the series (`close_zscore` field) |
| `with_tanh_deltas_from_previous` | Build `TanhDeltaDailyBar` from `NormalizedDailyBar` (per-field rules + `tanh` when both levels > 0) |
| `NormalizedDailyBar` | Level OHLCV row: `symbol`, `trade_date`, OHLC, `volume` (float), optional `close_zscore` |
| `TanhDeltaDailyBar` | `open_tanh`, …, `volume_tanh` in **[-1.0, 1.0]** (tanh interior or sentinel ±1 / 0) |
| `DegradationReport` | Re-export from `daily_bars` (multi-source fetch summary) |
| `DEFAULT_RELATIVE_CLOSE_EPSILON` | Re-export from `daily_bars` (fusion agreement tolerance, default `0.005`) |

Semantics of the underlying bars (splits, dividends, multi-source fusion) match benj-stocks / `daily-bars` documentation.

## Status

Early **0.1** library: suitable for local pipelines and notebooks. **Not** on PyPI yet; **no** GitHub Actions workflow in-repo yet—add CI (install + `pytest`) when you want automated checks.

### What is documented where

| Topic | Where |
|--------|--------|
| Install, usage, tanh semantics, API surface | This README |
| Package metadata, deps on benj-stocks | `pyproject.toml` |
| Public re-exports | `benj_stocks_normalized.__init__` and `__all__` |
| Function / type behavior | Docstrings on `api`, `convert`, `transforms`, `schema` |
| Regression / TDD specs | `tests/` (see Testing above) |
