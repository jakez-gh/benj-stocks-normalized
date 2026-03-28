from __future__ import annotations

from datetime import date
from typing import Protocol

from daily_bars_core.models import DailyBar


class DailyBarsSource(Protocol):
    name: str

    def fetch_daily_bars(
        self,
        symbol: str,
        *,
        start: date | None = None,
        end: date | None = None,
        timeout_seconds: float = 30.0,
    ) -> list[DailyBar]:
        """Return investor-continuous daily bars (split/dividend-adjusted), oldest first."""
