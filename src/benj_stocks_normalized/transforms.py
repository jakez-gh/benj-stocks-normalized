from __future__ import annotations

import math
from collections.abc import Sequence

from benj_stocks_normalized.schema import NormalizedDailyBar, TanhDeltaDailyBar


def _tanh_pct_delta(prev: float, curr: float, delta_scale: float) -> float:
    """Map prior/current **price or volume** to ``[-1.0, 1.0]``.

    Any value ``<= 0`` is treated as **0** before applying rules (bad prints and
    missing liquidity collapse to zero).

    Let ``p`` = ``0`` if ``prev <= 0`` else ``prev``, ``c`` = ``0`` if ``curr <= 0`` else ``curr``.

    - ``p <= 0`` and ``c <= 0`` → ``0.0``.
    - ``p <= 0`` and ``c > 0`` → ``1.0``.
    - ``p > 0`` and ``c <= 0`` → ``-1.0``.
    - ``p > 0``, ``c > 0``, ``c == p`` → ``0.0``.
    - ``p > 0``, ``c > 0``, ``c != p`` → ``tanh(delta_scale * (c - p) / p)``.
    """
    p = 0.0 if prev <= 0.0 else prev
    c = 0.0 if curr <= 0.0 else curr

    if p <= 0.0 and c <= 0.0:
        return 0.0
    if p <= 0.0 and c > 0.0:
        return 1.0
    if p > 0.0 and c <= 0.0:
        return -1.0
    if c == p:
        return 0.0
    pct = (c - p) / p
    return math.tanh(delta_scale * pct)


def with_tanh_deltas_from_previous(
    bars: Sequence[NormalizedDailyBar],
    *,
    delta_scale: float = 1.0,
    drop_first: bool = True,
) -> list[TanhDeltaDailyBar]:
    """Per-field tanh of day-over-day **percentage** change (same field vs yesterday).

    **Why not one tanh “against the close” for O/H/L/C?** Using yesterday’s open
    for today’s open (and likewise high/low/close/volume) keeps each channel
    meaningful. Driving every price off only the close hides gap structure and
    mixes intraday levels awkwardly.

    Per-field mapping uses :func:`_tanh_pct_delta` (non-positive levels treated as
    ``0`` before sentinels and ``tanh``).

    * *drop_first* ``True`` (default): the first calendar row is skipped (no prior
      day). Returned length is ``len(bars) - 1`` when ``len(bars) >= 1``.
    * *drop_first* ``False``: the first row is emitted with all tanh fields ``0.0``.
    """
    if not bars:
        return []
    if delta_scale < 0.0:
        raise ValueError("delta_scale must be non-negative")

    out: list[TanhDeltaDailyBar] = []

    if not drop_first and bars:
        b0 = bars[0]
        out.append(
            TanhDeltaDailyBar(
                symbol=b0.symbol,
                trade_date=b0.trade_date,
                open_tanh=0.0,
                high_tanh=0.0,
                low_tanh=0.0,
                close_tanh=0.0,
                volume_tanh=0.0,
            )
        )

    for i in range(1, len(bars)):
        prev, curr = bars[i - 1], bars[i]
        if curr.symbol != prev.symbol:
            raise ValueError("bars must be a single symbol in chronological order")
        out.append(
            TanhDeltaDailyBar(
                symbol=curr.symbol,
                trade_date=curr.trade_date,
                open_tanh=_tanh_pct_delta(prev.open, curr.open, delta_scale),
                high_tanh=_tanh_pct_delta(prev.high, curr.high, delta_scale),
                low_tanh=_tanh_pct_delta(prev.low, curr.low, delta_scale),
                close_tanh=_tanh_pct_delta(prev.close, curr.close, delta_scale),
                volume_tanh=_tanh_pct_delta(prev.volume, curr.volume, delta_scale),
            )
        )
    return out


def scale_ohlc_by_first_close(bars: Sequence[NormalizedDailyBar]) -> list[NormalizedDailyBar]:
    """Divide OHLC by the **first** bar's close (chronological order).

    The first row's close becomes ``1.0``. Volume stays in shares (unchanged) so
    activity remains comparable to the underlying feed.
    """
    if not bars:
        return []
    first_close = bars[0].close
    if first_close == 0.0:
        raise ValueError("first close is zero; cannot scale")
    inv = 1.0 / first_close
    out: list[NormalizedDailyBar] = []
    for b in bars:
        out.append(
            NormalizedDailyBar(
                symbol=b.symbol,
                trade_date=b.trade_date,
                open=b.open * inv,
                high=b.high * inv,
                low=b.low * inv,
                close=b.close * inv,
                volume=b.volume,
                close_zscore=b.close_zscore,
            )
        )
    return out


def with_close_zscore(bars: Sequence[NormalizedDailyBar]) -> list[NormalizedDailyBar]:
    """Attach population z-scores of *close* across the window (``close_zscore``)."""
    if not bars:
        return []
    closes = [b.close for b in bars]
    mean = sum(closes) / len(closes)
    var = sum((c - mean) ** 2 for c in closes) / len(closes)
    std = math.sqrt(var)
    if std == 0.0:
        return [
            NormalizedDailyBar(
                symbol=b.symbol,
                trade_date=b.trade_date,
                open=b.open,
                high=b.high,
                low=b.low,
                close=b.close,
                volume=b.volume,
                close_zscore=0.0,
            )
            for b in bars
        ]
    inv_std = 1.0 / std
    return [
        NormalizedDailyBar(
            symbol=b.symbol,
            trade_date=b.trade_date,
            open=b.open,
            high=b.high,
            low=b.low,
            close=b.close,
            volume=b.volume,
            close_zscore=(b.close - mean) * inv_std,
        )
        for b in bars
    ]
