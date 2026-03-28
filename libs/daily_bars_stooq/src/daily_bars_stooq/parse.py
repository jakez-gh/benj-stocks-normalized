from __future__ import annotations

from datetime import date

from daily_bars_core import DailyBar


def parse_stooq_daily_csv(text: str) -> list[DailyBar]:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if not lines:
        return []
    if not _header_is_stooq_daily(lines[0]):
        raise ValueError(f"unexpected CSV header: cannot parse {lines[0]!r}")
    out: list[DailyBar] = []
    for line in lines[1:]:
        try:
            out.append(_parse_stooq_daily_line(line))
        except ValueError as e:
            raise ValueError(f"cannot parse Stooq daily row: {line!r}") from e
    return out


def _header_is_stooq_daily(header: str) -> bool:
    parts = [p.strip().lower() for p in header.split(",")]
    return parts == ["date", "open", "high", "low", "close", "volume"]


def _parse_stooq_daily_line(line: str) -> DailyBar:
    parts = line.split(",")
    if len(parts) != 6:
        raise ValueError("expected 6 columns")
    d_raw, o_raw, h_raw, l_raw, c_raw, v_raw = (p.strip() for p in parts)
    try:
        y, m, day = (int(x) for x in d_raw.split("-"))
        trade_date = date(y, m, day)
    except ValueError as e:
        raise ValueError("invalid date") from e
    try:
        o = float(o_raw)
        h = float(h_raw)
        low = float(l_raw)
        c = float(c_raw)
        v = int(float(v_raw))
    except ValueError as e:
        raise ValueError("invalid numeric field") from e
    return DailyBar(
        trade_date=trade_date,
        open=o,
        high=h,
        low=low,
        close=c,
        volume=v,
    )
