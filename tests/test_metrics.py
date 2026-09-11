import unittest

from macro_graph.analysis.metrics import aligned_correlation, summarize_market, summarize_rate


def market_rows(values):
    return [
        {
            "session_date": f"2026-01-{index:02d}",
            "close": str(value),
            "adj_close": str(value),
            "volume": "100",
            "provider": "fixture",
            "retrieved_at": "2026-01-31T00:00:00+00:00",
            "quality_flags_json": "[]",
        }
        for index, value in enumerate(values, 1)
    ]


class MetricTests(unittest.TestCase):
    def test_market_returns_and_relative_strength(self) -> None:
        asset = market_rows([100, 101, 102, 104, 105, 110])
        benchmark = market_rows([100, 100, 101, 102, 103, 104])
        result = summarize_market(asset, benchmark)
        self.assertAlmostEqual(result["5d_return"], 10.0)
        self.assertAlmostEqual(result["relative_strength_vs_nasdaq_pct_points"]["5d"], 6.0)

    def test_rate_change_is_basis_points(self) -> None:
        rows = [
            {
                "period": "2026-01-01",
                "value": "4.00",
                "provider": "fixture",
                "retrieved_at": "2026-01-01T00:00:00+00:00",
                "quality_flags_json": "[]",
            },
            {
                "period": "2026-01-02",
                "value": "4.12",
                "provider": "fixture",
                "retrieved_at": "2026-01-02T00:00:00+00:00",
                "quality_flags_json": "[]",
            },
        ]
        self.assertAlmostEqual(summarize_rate(rows)["daily_change_bp"], 12.0)

    def test_correlation_includes_sample_size(self) -> None:
        left = market_rows([100, 101, 103, 106, 110, 115])
        right = market_rows([50, 51, 53, 56, 60, 65])
        result = aligned_correlation(left, right, 5)
        self.assertEqual(result["status"], "OK")
        self.assertEqual(result["sample_size"], 5)
        self.assertGreater(result["value"], 0.9)
