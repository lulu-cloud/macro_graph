"""Official FRED CSV adapter.

The public graph CSV endpoint keeps the MVP runnable without an API key. A future
API adapter will add exact ALFRED vintages; until then ``available_at`` is the
retrieval timestamp and ``availability_inferred`` is explicit.
"""

from __future__ import annotations

import csv
import hashlib
import io
from collections.abc import Sequence
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation

import httpx

from macro_graph.domain import Observation, ProviderStatus


class FredCsvProvider:
    name = "fred_csv"
    base_url = "https://fred.stlouisfed.org/graph/fredgraph.csv"

    def __init__(self, series_map: dict[str, str], timeout: float = 20.0) -> None:
        self.series_map = series_map
        self.timeout = timeout

    def fetch_series(
        self, canonical_ids: Sequence[str], start: date, end: date, *, as_of: datetime
    ) -> list[Observation]:
        if as_of.tzinfo is None:
            raise ValueError("as_of must be timezone-aware")
        retrieved_at = datetime.now(timezone.utc)
        results: list[Observation] = []
        with httpx.Client(timeout=self.timeout, follow_redirects=True) as client:
            for canonical_id in canonical_ids:
                series_id = self.series_map[canonical_id]
                response = client.get(
                    self.base_url,
                    params={"id": series_id, "cosd": start.isoformat(), "coed": end.isoformat()},
                )
                response.raise_for_status()
                payload_hash = hashlib.sha256(response.content).hexdigest()
                reader = csv.DictReader(io.StringIO(response.text))
                for row in reader:
                    raw_value = row.get(series_id, ".")
                    try:
                        value = Decimal(raw_value)
                    except (InvalidOperation, TypeError):
                        continue
                    observed = datetime.fromisoformat(row["observation_date"]).replace(
                        tzinfo=timezone.utc
                    )
                    if observed > as_of:
                        continue
                    results.append(
                        Observation(
                            canonical_id=canonical_id,
                            provider=self.name,
                            provider_series_id=series_id,
                            observed_at=observed,
                            available_at=retrieved_at,
                            retrieved_at=retrieved_at,
                            value=value,
                            unit="percent",
                            frequency="daily",
                            vintage=retrieved_at.date().isoformat(),
                            source_url=str(response.url),
                            raw_payload_hash=payload_hash,
                            quality_flags=("availability_inferred", "latest_vintage_only"),
                        )
                    )
        return results

    def health(self) -> ProviderStatus:
        return ProviderStatus.OK
