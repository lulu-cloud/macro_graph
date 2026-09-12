import json
import tempfile
import unittest
from pathlib import Path

from macro_graph.web.server import DashboardData


class DashboardDataTests(unittest.TestCase):
    def test_reads_latest_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            (output / "snapshots").mkdir()
            (output / "reports").mkdir()
            (output / "graphs").mkdir()
            (output / "snapshots" / "market_snapshot_20260101.json").write_text(
                json.dumps({"run": {"run_date": "2026-01-01"}}), encoding="utf-8"
            )
            (output / "snapshots" / "market_snapshot_20260102.json").write_text(
                json.dumps({"run": {"run_date": "2026-01-02"}}), encoding="utf-8"
            )
            (output / "reports" / "2026-01-02.md").write_text("# report", encoding="utf-8")
            (output / "graphs" / "graph.json").write_text(
                json.dumps({"nodes": []}), encoding="utf-8"
            )
            data = DashboardData(output)
            self.assertEqual(data.snapshot()["run"]["run_date"], "2026-01-02")
            self.assertEqual(data.report()["date"], "2026-01-02")
            self.assertEqual(data.graph()["nodes"], [])

    def test_reads_chinese_manual(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "output"
            (root / "docs").mkdir()
            (root / "docs" / "MANUAL_RESEARCH_GUIDE_ZH.md").write_text(
                "# 中文说明书", encoding="utf-8"
            )
            data = DashboardData(output, root)
            self.assertEqual(data.manual()["content"], "# 中文说明书")

    def test_reads_shared_chinese_glossary(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "output"
            (root / "config").mkdir()
            (root / "config" / "glossary.zh-CN.json").write_text(
                json.dumps({"schema_version": 1, "terms": [{"key": "DXY"}]}),
                encoding="utf-8",
            )
            data = DashboardData(output, root)
            self.assertEqual(data.glossary()["terms"][0]["key"], "DXY")

    def test_empty_state_is_explicit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            data = DashboardData(Path(directory))
            self.assertEqual(data.snapshot()["error"], "NO_SNAPSHOT")
            self.assertEqual(data.report()["error"], "NO_REPORT")
            self.assertEqual(data.graph()["error"], "NO_GRAPH")
            self.assertEqual(data.manual()["error"], "NO_MANUAL")
            self.assertEqual(data.glossary()["error"], "NO_GLOSSARY")
