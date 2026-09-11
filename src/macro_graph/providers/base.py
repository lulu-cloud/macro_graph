"""Interfaces that keep the system independent of a particular vendor."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date, datetime
from typing import Protocol

from macro_graph.domain import MarketBar, Observation, ProviderStatus


class MacroDataProvider(Protocol):
    name: str

    def fetch_series(
        self, canonical_ids: Sequence[str], start: date, end: date, *, as_of: datetime
    ) -> list[MarketBar]: ...

    def health(self) -> ProviderStatus: ...


class MarketDataProvider(Protocol):
    name: str

    def fetch_daily_bars(
        self, canonical_ids: Sequence[str], start: date, end: date, *, as_of: datetime
    ) -> list[Observation]: ...

    def health(self) -> ProviderStatus: ...
