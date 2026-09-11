# MVP Implementation Plan

The MVP is deliberately incremental. Each milestone ends with tests, a visible artifact, a source ledger, and a reliability note.

## Acceptance boundary

MVP assets:

- Macro/rates: effective Fed Funds, US02Y, US10Y, 10Y real yield, 10Y breakeven.
- Markets: DXY, gold, Brent, S&P 500, Nasdaq Composite, SOXX.
- Companies: NVDA, AVGO, MU, SNDK, INTC, LITE, GLW.

MVP outputs:

- `data/macro_graph.sqlite3`
- `output/snapshots/market_snapshot_YYYYMMDD.json`
- `output/graphs/graph.json` and `graph.graphml`
- `output/reports/YYYY-MM-DD.md`

The first report may contain `UNKNOWN` where a reliable source or causal discriminator is absent. That is an accepted and preferred result.

## Milestone 0 — decisions and executable foundation

Deliver:

- select market provider and document licensing/reliability;
- confirm DXY/gold/Brent proxy definitions and report cutoff;
- configuration loader, structured logging, CLI parser, run manifest;
- migrations and a temporary-database test harness.

Exit checks:

- `python -m macro_graph.jobs.daily_job --help` succeeds;
- config validation rejects duplicate canonical IDs and unsupported units;
- test suite runs offline.

Known risk: market provider choice remains the largest external dependency.

## Milestone 1 — official rates collection and SQLite

Deliver:

- FRED observations adapter with vintage fields;
- U.S. Treasury nominal-curve adapter with FRED fallback;
- normalization and idempotent repositories;
- freshness and cross-source checks for 2Y/10Y.

Tests and evidence:

- recorded-response contract fixtures;
- missing value (`.`), holiday, retry, revision, and duplicate tests;
- compare Treasury and FRED nominal yields within a declared tolerance;
- show row counts and a sample SQL query.

Unreliable/limited: official daily series may be published after the market close and can be stale on holidays.

## Milestone 2 — market prices and derived metrics

Deliver:

- first `MarketDataProvider` implementation;
- mapping for all MVP market/company symbols;
- adjusted/raw basis retention;
- 1/5/20/60/120-session returns, relative strength, volume ratio, robust z-score;
- pairwise-aligned rolling correlations with sample counts.

Tests and evidence:

- fixture-based provider contract tests;
- split/dividend, missing session, timezone, incomplete candle, and contract-roll tests;
- reconciliation sample against provider-visible values.

Unreliable/limited: free feeds may be delayed, revised, rate-limited, or missing volume. Futures continuous series embed roll effects.

## Milestone 3 — deterministic daily snapshot

Deliver:

- pipeline `collect -> validate -> store -> calculate -> snapshot`;
- point-in-time selector and `--date`/`--as-of` rerun;
- atomic JSON export with quality and provider-status sections;
- `COMPLETE`, `DEGRADED`, and `FAILED` run statuses.

Tests and evidence:

- golden snapshot schema;
- rerunning identical inputs produces the same content hash;
- late and revised observations are excluded by cutoff;
- demonstrate a degraded run with one optional provider unavailable.

## Milestone 4 — curated causal graph

Deliver:

- typed node/edge config validation;
- initial macro, rates, commodity, AI-demand, industry, and company nodes;
- NetworkX directed multigraph;
- JSON and GraphML export;
- edge evidence annotations, including contradictions and missing evidence.

Tests and evidence:

- no orphan nodes, invalid direction, or duplicate versioned edge;
- export/import round-trip;
- render a small inspection image or open the graph in a viewer for visual QA.

Unreliable/limited: weights and confidence are curated research judgments, not estimated causal coefficients.

## Milestone 5 — rule-based regimes and report

Deliver:

- preregistered rule configuration and minimum-data thresholds;
- multi-label regime scores with counterevidence;
- ten-section Markdown report;
- strict FACT/OBSERVATION/INFERENCE/HYPOTHESIS/UNKNOWN records;
- causal path validation table for the day.

Tests and evidence:

- deterministic rule fixtures for hawkish tightening, inflation shock, growth scare, hardware rotation, conflicts, and insufficient data;
- report assertions that every inference has evidence IDs and every missing section says `UNKNOWN`;
- generate and inspect one historical sample report.

## Milestone 6 — scheduling and operating runbook

Deliver:

- cron examples and timezone/DST guidance;
- lock, timeout, bounded retry, cache, log rotation, and SQLite backup;
- health/status command and failure notification hook;
- backfill procedure.

Tests and evidence:

- overlapping run is rejected safely;
- interrupted run resumes or reruns idempotently;
- a full historical date run produces all four artifacts.

## Post-MVP order

1. Economic calendar and release-time event windows.
2. BLS CPI/PPI/NFP and BEA PCE/GDP with revision-aware histories.
3. Fed/FOMC calendar and speeches; licensed CME FedWatch or explicit unavailable status.
4. EIA petroleum data and demand-vs-supply shock classifier.
5. Earnings calendars and SEC filings/company facts.
6. CFTC COT weekly positioning.
7. News ingestion with source provenance and evidence extraction.
8. Options and ETF creations/redemptions only after a reliable licensed source is chosen.
9. `docs/MACRO_MARKET_GUIDE.md`, developed chapter-by-chapter with primary sources and historical cases rather than generated all at once.

## Definition of done for every milestone

- tests pass offline;
- one representative output is shown and visually/semantically inspected;
- source, units, timestamp, price basis, and freshness are visible;
- known gaps and failure modes are documented;
- no unsupported causal claim or hidden fallback is introduced.
