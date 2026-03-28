from __future__ import annotations

import statistics
from datetime import date
from typing import Mapping, Sequence

from daily_bars_core import DailyBar

# Relative |c1-c2| / max(|c1|,|c2|) at or below this => treat two feeds as agreeing.
DEFAULT_RELATIVE_CLOSE_EPSILON = 0.005


def fuse_daily_bars_by_consensus(
    by_source: Mapping[str, list[DailyBar]],
    source_order: Sequence[str],
    *,
    relative_close_epsilon: float = DEFAULT_RELATIVE_CLOSE_EPSILON,
) -> list[DailyBar]:
    """Fuse bars from multiple sources into one investor-continuous series per calendar day.

    Policy (chosen for paper-style use with noisy free feeds):

    - **One** contributor for a date: use that bar unchanged.
    - **Two** contributors: if relative close difference ≤ *relative_close_epsilon*, use the
      **average** OHLCV (with bounds repaired so high/low envelope open/close). Otherwise use
      the **first** source in *source_order* (primary).
    - **Three or more**: **median close** as consensus; pick the contributor whose close is
      **closest** to that median (ties: earlier in *source_order* wins); scale that bar’s OHLC
      by ``median_close / ref.close`` so the bar stays geometrically valid; **volume** is the
      **median** of reported volumes.

    Dates present in any successful feed are included (gap-fill across sources).
    """
    order = [n for n in source_order if n in by_source and by_source[n]]
    if not order:
        return []
    indices: dict[str, dict[date, DailyBar]] = {n: {b.trade_date: b for b in by_source[n]} for n in order}
    all_dates = sorted(set().union(*(indices[n].keys() for n in order)))
    return [
        _fuse_one_date(d, [(n, indices[n][d]) for n in order if d in indices[n]], relative_close_epsilon)
        for d in all_dates
    ]


def _fuse_one_date(
    d: date,
    contributors: list[tuple[str, DailyBar]],
    eps: float,
) -> DailyBar:
    bars = [b for _, b in contributors]
    k = len(bars)
    if k == 1:
        return bars[0]
    if k == 2:
        return _fuse_two(d, bars[0], bars[1], eps)
    return _fuse_many(d, bars, eps)


def _fuse_two(d: date, b1: DailyBar, b2: DailyBar, eps: float) -> DailyBar:
    c1, c2 = b1.close, b2.close
    denom = max(abs(c1), abs(c2), 1e-12)
    if abs(c1 - c2) / denom <= eps:
        return _average_bar(d, b1, b2)
    # Disagree materially: primary is the first contributor in caller order (b1).
    return b1


def _average_bar(d: date, b1: DailyBar, b2: DailyBar) -> DailyBar:
    o = (b1.open + b2.open) / 2
    h = (b1.high + b2.high) / 2
    low = (b1.low + b2.low) / 2
    c = (b1.close + b2.close) / 2
    v = int(round((b1.volume + b2.volume) / 2))
    hi = max(o, h, low, c)
    lo = min(o, h, low, c)
    return DailyBar(d, o, hi, lo, c, v)


def _fuse_many(
    d: date,
    bars: list[DailyBar],
    eps: float,
) -> DailyBar:
    _ = eps  # reserved for future tightened rules
    closes = [b.close for b in bars]
    med_c = float(statistics.median(closes))
    ref_bar = bars[0]
    best_dist = abs(ref_bar.close - med_c)
    for b in bars[1:]:
        dist = abs(b.close - med_c)
        if dist < best_dist:
            best_dist = dist
            ref_bar = b
        # tie: keep earlier contributor (smaller index)
    scale = med_c / ref_bar.close if ref_bar.close else 1.0
    med_v = int(round(statistics.median([b.volume for b in bars])))
    o = ref_bar.open * scale
    h = ref_bar.high * scale
    low = ref_bar.low * scale
    hi = max(o, h, low, med_c)
    lo = min(o, h, low, med_c)
    return DailyBar(d, o, hi, lo, med_c, med_v)
