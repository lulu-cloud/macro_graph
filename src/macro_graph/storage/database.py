"""Minimal SQLite repository for the runnable MVP."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from datetime import date, datetime
from pathlib import Path

from macro_graph.domain import MarketBar, Observation


class Database:
    def __init__(self, path: Path) -> None:
        self.path = path

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def initialize(self) -> None:
        schema_path = Path(__file__).with_name("schema.sql")
        with self.connect() as connection:
            connection.executescript(schema_path.read_text(encoding="utf-8"))

    def sync_assets(self, asset_config: dict) -> None:
        rows = list(asset_config.get("assets", []))
        with self.connect() as connection:
            for row in rows:
                connection.execute(
                    """
                    INSERT INTO assets(canonical_symbol, name, asset_class, metadata_json)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(canonical_symbol) DO UPDATE SET
                        name=excluded.name,
                        asset_class=excluded.asset_class,
                        metadata_json=excluded.metadata_json
                    """,
                    (
                        row["id"],
                        row["name"],
                        row["asset_class"],
                        json.dumps(row, ensure_ascii=False, sort_keys=True),
                    ),
                )

    def upsert_macro(self, observations: Sequence[Observation]) -> None:
        with self.connect() as connection:
            connection.executemany(
                """
                INSERT INTO macro_indicators(
                    series_id, period, observed_at, released_at, available_at, value,
                    unit, frequency, vintage, provider, retrieved_at, payload_hash,
                    quality_flags_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(series_id, period, vintage, provider) DO UPDATE SET
                    value=excluded.value,
                    retrieved_at=excluded.retrieved_at,
                    payload_hash=excluded.payload_hash,
                    quality_flags_json=excluded.quality_flags_json
                """,
                [
                    (
                        item.canonical_id,
                        item.observed_at.date().isoformat(),
                        item.observed_at.isoformat(),
                        item.released_at.isoformat() if item.released_at else None,
                        item.available_at.isoformat(),
                        str(item.value),
                        item.unit,
                        item.frequency,
                        item.vintage or item.retrieved_at.date().isoformat(),
                        item.provider,
                        item.retrieved_at.isoformat(),
                        item.raw_payload_hash,
                        json.dumps(item.quality_flags),
                    )
                    for item in observations
                ],
            )

    def upsert_market(self, bars: Sequence[MarketBar]) -> None:
        with self.connect() as connection:
            asset_ids = {
                row["canonical_symbol"]: row["id"]
                for row in connection.execute("SELECT id, canonical_symbol FROM assets")
            }
            connection.executemany(
                """
                INSERT INTO market_prices(
                    asset_id, session_date, ts, interval, open, high, low, close,
                    adj_close, volume, currency, price_basis, provider, retrieved_at,
                    quality_flags_json
                ) VALUES (?, ?, ?, '1d', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(asset_id, interval, ts, provider) DO UPDATE SET
                    open=excluded.open, high=excluded.high, low=excluded.low,
                    close=excluded.close, adj_close=excluded.adj_close,
                    volume=excluded.volume, retrieved_at=excluded.retrieved_at,
                    quality_flags_json=excluded.quality_flags_json
                """,
                [
                    (
                        asset_ids[item.canonical_id],
                        item.session_date.isoformat(),
                        item.timestamp.isoformat(),
                        str(item.open) if item.open is not None else None,
                        str(item.high) if item.high is not None else None,
                        str(item.low) if item.low is not None else None,
                        str(item.close),
                        str(item.adjusted_close) if item.adjusted_close is not None else None,
                        str(item.volume) if item.volume is not None else None,
                        item.currency,
                        item.price_basis,
                        item.provider,
                        item.retrieved_at.isoformat(),
                        json.dumps(item.quality_flags),
                    )
                    for item in bars
                ],
            )

    def market_history(self, canonical_id: str, through: date) -> list[dict]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT p.session_date, p.close, p.adj_close, p.volume, p.provider,
                       p.retrieved_at, p.quality_flags_json
                FROM market_prices p JOIN assets a ON a.id = p.asset_id
                WHERE a.canonical_symbol=? AND p.session_date<=?
                ORDER BY p.session_date
                """,
                (canonical_id, through.isoformat()),
            ).fetchall()
        return [dict(row) for row in rows]

    def macro_history(self, series_id: str, through: date) -> list[dict]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT period, value, provider, retrieved_at, quality_flags_json
                FROM macro_indicators
                WHERE series_id=? AND period<=?
                ORDER BY period, vintage
                """,
                (series_id, through.isoformat()),
            ).fetchall()
        latest_by_period = {row["period"]: dict(row) for row in rows}
        return [latest_by_period[key] for key in sorted(latest_by_period)]

    def save_snapshot(
        self, run_date: date, as_of: datetime, status: str, config_hash: str, payload: dict
    ) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO daily_snapshots(
                    run_date, as_of, status, schema_version, config_hash, payload_json, created_at
                ) VALUES (?, ?, ?, '1.0', ?, ?, ?)
                ON CONFLICT(run_date, as_of, config_hash) DO UPDATE SET
                    status=excluded.status, payload_json=excluded.payload_json,
                    created_at=excluded.created_at
                """,
                (
                    run_date.isoformat(),
                    as_of.isoformat(),
                    status,
                    config_hash,
                    json.dumps(payload, ensure_ascii=False, sort_keys=True),
                    datetime.now(as_of.tzinfo).isoformat(),
                ),
            )
