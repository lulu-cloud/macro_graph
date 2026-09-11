"""Convenience market-data adapter behind the stable provider contract."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal

import pandas as pd
import yfinance as yf

from macro_graph.domain import MarketBar, ProviderStatus


def _decimal(value: object) -> Decimal | None:
    if value is None or pd.isna(value):
        return None
    return Decimal(str(float(value)))


class YFinanceProvider:
    name = "yfinance"

    def __init__(self, symbol_map: dict[str, str]) -> None:
        self.symbol_map = symbol_map

    def fetch_daily_bars(
        self, canonical_ids: Sequence[str], start: date, end: date, *, as_of: datetime
    ) -> list[MarketBar]:
        if as_of.tzinfo is None:
            raise ValueError("as_of must be timezone-aware")
        retrieved_at = datetime.now(timezone.utc)
        bars: list[MarketBar] = []
        for canonical_id in canonical_ids:
            symbol = self.symbol_map[canonical_id]
            frame = yf.download(
                symbol,
                start=start.isoformat(),
                end=(end + timedelta(days=1)).isoformat(),
                auto_adjust=False,
                actions=False,
                progress=False,
                threads=False,
                timeout=20,
            )
            if frame.empty:
                continue
            if isinstance(frame.columns, pd.MultiIndex):
                frame.columns = frame.columns.get_level_values(0)
            for index, row in frame.iterrows():
                session_date = index.date()
                if session_date > end:
                    continue
                timestamp = datetime.combine(session_date, time(21, 0), tzinfo=timezone.utc)
                bars.append(
                    MarketBar(
                        canonical_id=canonical_id,
                        provider=self.name,
                        provider_symbol=symbol,
                        session_date=session_date,
                        timestamp=timestamp,
                        open=_decimal(row.get("Open")),
                        high=_decimal(row.get("High")),
                        low=_decimal(row.get("Low")),
                        close=_decimal(row.get("Close")) or Decimal(0),
                        adjusted_close=_decimal(row.get("Adj Close")),
                        volume=_decimal(row.get("Volume")),
                        currency=None,
                        retrieved_at=retrieved_at,
                        quality_flags=("unofficial_market_feed",),
                    )
                )
        return bars

    def health(self) -> ProviderStatus:
        return ProviderStatus.OK
