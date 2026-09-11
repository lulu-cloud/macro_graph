import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from macro_graph.graph import build_graph, export_graph


class GraphTests(unittest.TestCase):
    def test_build_and_export(self) -> None:
        assets = {
            "assets": [{"id": "A", "name": "A", "asset_class": "rate"}],
            "non_market_nodes": [{"id": "B", "name": "B", "node_type": "commodity"}],
        }
        relationships = {
            "relationships": [
                {
                    "source": "A",
                    "target": "B",
                    "relationship": "pressure",
                    "direction": "negative",
                    "strength": 0.8,
                    "confidence": 0.9,
                    "reason": "fixture",
                    "source_reference": "fixture:test",
                }
            ]
        }
        graph = build_graph(assets, relationships)
        self.assertEqual(graph.number_of_edges(), 1)
        with tempfile.TemporaryDirectory() as directory:
            paths = export_graph(graph, Path(directory), datetime.now(timezone.utc))
            self.assertTrue(Path(paths["json"]).exists())
            self.assertTrue(Path(paths["graphml"]).exists())

    def test_unknown_node_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "unknown node"):
            build_graph(
                {"assets": [], "non_market_nodes": []},
                {
                    "relationships": [
                        {
                            "source": "MISSING",
                            "target": "ALSO_MISSING",
                            "relationship": "x",
                            "direction": "positive",
                            "strength": 1,
                            "confidence": 1,
                            "reason": "x",
                            "source_reference": "x",
                        }
                    ]
                },
            )
