# Macro Graph

Evidence-led macro and U.S. technology industry research system.

This repository contains a runnable, deliberately small MVP. It collects official FRED series through FRED's public CSV endpoint and market history through a replaceable yfinance adapter, then builds SQLite history, metrics, a causal graph, a JSON snapshot, and an evidence-labelled Markdown report.

## Read first

- [Architecture](ARCHITECTURE.md)
- [MVP implementation plan](docs/MVP_IMPLEMENTATION_PLAN.md)

## Bootstrap

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
python -m macro_graph.jobs.daily_job --date 2026-09-10
pytest
```

Generated artifacts are written under `output/`; the SQLite database is `data/macro_graph.sqlite3`.

To regenerate from already stored data without network access:

```bash
python -m macro_graph.jobs.daily_job --date 2026-09-10 --skip-collect
```

Start the local research dashboard:

```bash
python -m macro_graph.web.server
```

Then open [http://127.0.0.1:8765](http://127.0.0.1:8765). The dashboard reads the latest generated snapshot, report, and graph directly from `output/`.

## MVP status

- Official FRED CSV and replaceable yfinance market adapters
- SQLite storage and idempotent upserts
- 1/5/20/60/120-session metrics, relative strength, volume ratio, z-score, and correlations
- Rule-based regimes with insufficient-evidence fallbacks
- NetworkX JSON/GraphML causal graph
- Daily snapshot and ten-section Markdown report
- Local responsive dashboard with market overview, report reader, correlations, relative strength, and an interactive causal graph

Known MVP limits are printed inside every snapshot/report: true FRED vintage replay, a licensed market-data SLA, economic calendar, FedWatch, ETF flows, software ETF coverage, SEC filings, news, and options remain post-MVP work.

## Cron example

Run at 07:30 China time on weekdays:

```cron
30 7 * * 2-6 cd /absolute/path/to/macro_graph && .venv/bin/python -m macro_graph.jobs.daily_job >> data/daily_job.log 2>&1
```

U.S. daylight-saving time shifts relative to China, so production scheduling should eventually use a timezone-aware service timer and an exchange calendar.

## Safety boundary

This project produces research artifacts only. It contains no order placement, broker integration, or trading automation.
