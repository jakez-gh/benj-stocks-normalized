from __future__ import annotations

import math

from daily_bars_core.models import DailyBar


def align_by_date(
    left: list[DailyBar],
    right: list[DailyBar],
) -> list[tuple[DailyBar, DailyBar]]:
    by_l = {b.trade_date: b for b in left}
    by_r = {b.trade_date: b for b in right}
    common = sorted(set(by_l) & set(by_r))
    return [(by_l[d], by_r[d]) for d in common]


def mismatch_summary_for_date(
    left: DailyBar,
    right: DailyBar,
    *,
    rel_tol: float,
    abs_vol_tol: int = 0,
) -> list[str]:
    fields: list[str] = []
    for name, x, y in (
        ("open", left.open, right.open),
        ("high", left.high, right.high),
        ("low", left.low, right.low),
        ("close", left.close, right.close),
    ):
        if not math.isclose(x, y, rel_tol=rel_tol, abs_tol=1e-12):
            fields.append(name)
    if abs(left.volume - right.volume) > abs_vol_tol:
        fields.append("volume")
    return fields
