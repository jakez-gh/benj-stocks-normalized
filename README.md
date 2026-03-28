# benj-stocks

Private workspace for Python libraries and related project code related to trading stocks.

## `libs/` layout (daily OHLCV)

| Directory | Distribution / import | Role |
|-----------|------------------------|------|
| `daily_bars_core` | `daily-bars-core` → `daily_bars_core` | Shared `DailyBar`, `DailyBarsSource`, date filtering, compare helpers |
| `daily_bars_stooq` | `daily-bars-stooq` → `daily_bars_stooq` | Stooq CSV fetch + parse |
| `daily_bars_yahoo` | `daily-bars-yahoo` → `daily_bars_yahoo` | Yahoo Finance via `yfinance` |
| `daily_bars_alpha_vantage` | `daily-bars-alpha-vantage` → `daily_bars_alpha_vantage` | Alpha Vantage `TIME_SERIES_DAILY_ADJUSTED` |
| `daily_bars` | `daily-bars` → `daily_bars` | Combined facade: registry, degradation + fusion, re-exports |

### Install

From the repo root (use your own venv path if different):

```bash
python3 -m venv .venv
.venv/bin/pip install -e "libs/daily_bars_core[dev]" -e "libs/daily_bars_stooq[dev]" -e "libs/daily_bars_yahoo[dev]" -e "libs/daily_bars_alpha_vantage[dev]" -e "libs/daily_bars[dev]"
```

Run tests:

```bash
.venv/bin/pytest libs/daily_bars_core/tests libs/daily_bars_stooq/tests libs/daily_bars_yahoo/tests libs/daily_bars_alpha_vantage/tests libs/daily_bars/tests -q
```

### Usage

**Environment**

- **Alpha Vantage**: set `ALPHAVANTAGE_API_KEY`, or pass `api_key=` into `AlphaVantageDailyBarsSource` / `build_source_registry(alpha_vantage_api_key="...")`.

**Recommended: one call, multiple vendors, degrade + fuse**

Use the combined package so offline feeds do not crash the run; surviving data is merged per calendar day (see fusion rules below).

```python
from datetime import date

from daily_bars import build_source_registry, fetch_daily_bars_with_degradation

registry = build_source_registry()  # or alpha_vantage_api_key="..."

bars, report = fetch_daily_bars_with_degradation(
    registry,
    "AAPL",
    start=date(2024, 1, 1),
    end=date(2024, 6, 30),
    source_order=("yahoo", "stooq", "alpha_vantage"),
    symbols_by_source={
        "yahoo": "AAPL",
        "stooq": "aapl.us",
        "alpha_vantage": "AAPL",
    },
    # optional: relative_close_epsilon=0.005  # default 0.5% for two-feed agreement
)

for b in bars:
    print(b.trade_date, b.open, b.high, b.low, b.close, b.volume)

print("failed:", report.sources_failed)
print("errors:", report.errors)
```

Inspect `report.sources_attempted`, `report.sources_succeeded`, `report.bar_counts` for logging.

**Single vendor**

```python
from daily_bars_yahoo import YahooDailyBarsSource
from datetime import date

src = YahooDailyBarsSource()
bars = src.fetch_daily_bars("AAPL", start=date(2024, 1, 1), end=date(2024, 1, 31))
```

```python
from daily_bars_stooq import retrieve_daily_bars_stooq
from datetime import date

bars = retrieve_daily_bars_stooq("aapl.us", start=date(2024, 1, 1), end=date(2024, 1, 31))
```

**Registry without degradation** (you handle errors yourself):

```python
from daily_bars import build_source_registry, get_source

reg = build_source_registry()
bars = get_source(reg, "yahoo").fetch_daily_bars("AAPL", start=..., end=...)
```

**Core helpers** (compare two series, align dates):

```python
from daily_bars import align_by_date, mismatch_summary_for_date
```

### Semantics

- Bars are **investor-continuous** (split- and dividend-adjusted). Stooq raw CSV is restated using Yahoo adjustment ratios for the mapped ticker (e.g. `aapl.us` → `AAPL`).
- **`fetch_daily_bars_with_degradation`** tries each source in `source_order`, skips failures, then **`fuse_daily_bars_by_consensus`**: one feed → that bar; two feeds → **average** OHLCV if relative close agreement ≤ **0.5%** (`DEFAULT_RELATIVE_CLOSE_EPSILON`), else **primary** (first in order); **three or more** → **median close**, OHLC scaled from the bar whose close is nearest the median (tie → earlier in order), **median volume**. Returns `([], report)` if nothing usable is returned—no exception solely because one feed failed.

### Status (daily OHLCV stack)

**v0.1 — good enough to use locally and move on.** Packages are at `0.1.0`, editable from `libs/`, with **35** tests across the five packages. Optional later: CI, PyPI, response caching, retries.
