"""Collect, validate, store, calculate, graph, and report a daily run."""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from macro_graph.collectors import build_snapshot
from macro_graph.graph import build_graph, export_graph
from macro_graph.providers import FredCsvProvider, YFinanceProvider
from macro_graph.reports import render_report
from macro_graph.settings import Settings, load_yaml
from macro_graph.storage import Database

LOGGER = logging.getLogger("macro_graph.daily")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a point-in-time Macro Graph daily run")
    parser.add_argument("--date", type=date.fromisoformat, dest="run_date")
    parser.add_argument(
        "--as-of",
        type=datetime.fromisoformat,
        help="Timezone-aware cutoff, for example 2026-09-11T02:30:00+00:00",
    )
    parser.add_argument(
        "--skip-collect",
        action="store_true",
        help="Rebuild outputs from the existing SQLite history without network access",
    )
    parser.add_argument("--verbose", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    as_of = args.as_of or datetime.now(timezone.utc)
    if as_of.tzinfo is None:
        raise SystemExit("--as-of must include a UTC offset or timezone")
    run_date = args.run_date or _default_run_date(datetime.now(timezone.utc))

    settings = Settings.load()
    assets = load_yaml(settings.assets_path)
    relationships = load_yaml(settings.relationships_path)
    config_hash = _config_hash(settings.assets_path, settings.relationships_path)
    database = Database(settings.database_path)
    database.initialize()
    database.sync_assets(assets)

    lock_path = settings.project_root / "data" / ".daily_job.lock"
    with _RunLock(lock_path):
        provider_status: dict[str, dict] = {}
        if not args.skip_collect:
            start = run_date - timedelta(days=240)
            rate_map = {row["id"]: row["fred"] for row in assets["assets"] if row.get("fred")}
            market_map = {
                row["id"]: row["market_symbol"]
                for row in assets["assets"]
                if row.get("market_symbol")
            }
            try:
                LOGGER.info("Collecting %d FRED series", len(rate_map))
                provider = FredCsvProvider(rate_map, timeout=settings.provider_timeout_seconds)
                observations = provider.fetch_series(list(rate_map), start, run_date, as_of=as_of)
                database.upsert_macro(observations)
                provider_status[provider.name] = {"status": "OK", "rows": len(observations)}
            except Exception as exc:
                LOGGER.exception("FRED collection failed")
                provider_status["fred_csv"] = {"status": "ERROR", "error": str(exc)}

            try:
                LOGGER.info("Collecting %d market series", len(market_map))
                market_provider = YFinanceProvider(market_map)
                bars = market_provider.fetch_daily_bars(
                    list(market_map), start, run_date, as_of=as_of
                )
                database.upsert_market(bars)
                provider_status[market_provider.name] = {"status": "OK", "rows": len(bars)}
            except Exception as exc:
                LOGGER.exception("Market collection failed")
                provider_status["yfinance"] = {"status": "ERROR", "error": str(exc)}
        else:
            provider_status["collection"] = {"status": "SKIPPED", "reason": "--skip-collect"}

        snapshot = build_snapshot(database, run_date, as_of, config_hash, provider_status)
        snapshot_path = (
            settings.output_dir / "snapshots" / f"market_snapshot_{run_date:%Y%m%d}.json"
        )
        _atomic_json(snapshot_path, snapshot)
        database.save_snapshot(run_date, as_of, snapshot["run"]["status"], config_hash, snapshot)

        graph = build_graph(assets, relationships)
        graph_paths = export_graph(graph, settings.output_dir / "graphs", as_of)
        report_path = settings.output_dir / "reports" / f"{run_date.isoformat()}.md"
        render_report(snapshot, report_path)

    result = {
        "status": snapshot["run"]["status"],
        "run_date": run_date.isoformat(),
        "snapshot": str(snapshot_path),
        "report": str(report_path),
        "graph": graph_paths,
        "missing_series": snapshot["quality"]["missing_series"],
        "stale_series": snapshot["quality"]["stale_series"],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if snapshot["run"]["status"] in {"COMPLETE", "DEGRADED"} else 1


def _default_run_date(now_utc: datetime) -> date:
    new_york = now_utc.astimezone(ZoneInfo("America/New_York"))
    candidate = new_york.date() if new_york.hour >= 18 else new_york.date() - timedelta(days=1)
    while candidate.weekday() >= 5:
        candidate -= timedelta(days=1)
    return candidate


def _config_hash(*paths: Path) -> str:
    digest = hashlib.sha256()
    for path in paths:
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _atomic_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


class _RunLock:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.fd: int | None = None

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self.fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError as exc:
            raise RuntimeError(f"Another daily run holds {self.path}") from exc
        os.write(self.fd, str(os.getpid()).encode())
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        if self.fd is not None:
            os.close(self.fd)
        self.path.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
