"""Small stable contracts shared across providers and analysis layers."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from enum import Enum


class EvidenceClass(str, Enum):
    FACT = "FACT"
    OBSERVATION = "OBSERVATION"
    INFERENCE = "INFERENCE"
    HYPOTHESIS = "HYPOTHESIS"
    UNKNOWN = "UNKNOWN"


class ProviderStatus(str, Enum):
    OK = "OK"
    STALE = "STALE"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


class RunStatus(str, Enum):
    COMPLETE = "COMPLETE"
    DEGRADED = "DEGRADED"
    FAILED = "FAILED"


@dataclass(frozen=True)
class Observation:
    """A normalized point-in-time value; timestamps must be timezone-aware."""

    canonical_id: str
    provider: str
    provider_series_id: str
    observed_at: datetime
    available_at: datetime
    retrieved_at: datetime
    value: Decimal
    unit: str
    frequency: str
    released_at: datetime | None = None
    vintage: str | None = None
    source_url: str | None = None
    raw_payload_hash: str | None = None
    quality_flags: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        for name in ("observed_at", "available_at", "retrieved_at"):
            if getattr(self, name).tzinfo is None:
                raise ValueError(f"{name} must be timezone-aware")


@dataclass(frozen=True)
class MarketBar:
    canonical_id: str
    provider: str
    provider_symbol: str
    session_date: date
    timestamp: datetime
    open: Decimal | None
    high: Decimal | None
    low: Decimal | None
    close: Decimal
    adjusted_close: Decimal | None
    volume: Decimal | None
    currency: str | None
    retrieved_at: datetime
    price_basis: str = "raw_and_adjusted"
    quality_flags: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.timestamp.tzinfo is None or self.retrieved_at.tzinfo is None:
            raise ValueError("market timestamps must be timezone-aware")
