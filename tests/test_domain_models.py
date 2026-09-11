import unittest
from datetime import datetime, timezone
from decimal import Decimal

from macro_graph.domain import Observation


class ObservationTests(unittest.TestCase):
    def test_requires_timezone_aware_timestamps(self) -> None:
        aware = datetime(2026, 9, 10, tzinfo=timezone.utc)
        with self.assertRaisesRegex(ValueError, "observed_at"):
            Observation(
                canonical_id="US10Y",
                provider="fred",
                provider_series_id="DGS10",
                observed_at=datetime(2026, 9, 10),  # noqa: DTZ001 - intentional invalid input
                available_at=aware,
                retrieved_at=aware,
                value=Decimal("4.10"),
                unit="percent",
                frequency="daily",
            )

    def test_accepts_point_in_time_metadata(self) -> None:
        timestamp = datetime(2026, 9, 10, tzinfo=timezone.utc)
        item = Observation(
            canonical_id="US10Y",
            provider="fred",
            provider_series_id="DGS10",
            observed_at=timestamp,
            available_at=timestamp,
            retrieved_at=timestamp,
            value=Decimal("4.10"),
            unit="percent",
            frequency="daily",
            vintage="2026-09-10",
        )
        self.assertEqual(item.vintage, "2026-09-10")
