import unittest
from datetime import datetime, timezone

from macro_graph.jobs.daily_job import _default_run_date


class DailyJobDateTests(unittest.TestCase):
    def test_before_new_york_cutoff_uses_previous_session(self) -> None:
        now = datetime(2026, 9, 11, 5, 30, tzinfo=timezone.utc)
        self.assertEqual(_default_run_date(now).isoformat(), "2026-09-10")

    def test_after_new_york_cutoff_uses_current_session(self) -> None:
        now = datetime(2026, 9, 11, 23, 0, tzinfo=timezone.utc)
        self.assertEqual(_default_run_date(now).isoformat(), "2026-09-11")

    def test_weekend_rolls_back_to_friday(self) -> None:
        now = datetime(2026, 9, 14, 5, 0, tzinfo=timezone.utc)
        self.assertEqual(_default_run_date(now).isoformat(), "2026-09-11")
