import tempfile
import unittest
from pathlib import Path

from macro_graph.storage import Database


class DatabaseTests(unittest.TestCase):
    def test_schema_and_asset_upsert_are_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database = Database(Path(directory) / "test.sqlite3")
            database.initialize()
            config = {"assets": [{"id": "US10Y", "name": "Ten Year", "asset_class": "rate"}]}
            database.sync_assets(config)
            database.sync_assets(config)
            with database.connect() as connection:
                count = connection.execute("SELECT COUNT(*) FROM assets").fetchone()[0]
            self.assertEqual(count, 1)
