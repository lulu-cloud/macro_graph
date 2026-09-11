# Macro Graph Architecture

Status: architecture baseline (2026-09-11). This document defines the first implementation boundary; it is not a claim that every listed feed is already integrated.

## 1. Purpose and non-goals

Macro Graph is a personal, long-running research system for explaining the chain:

`macro environment -> rates -> dollar -> commodities -> equity industries -> company fundamentals`

The system collects reproducible facts, calculates observations, evaluates explicitly declared causal hypotheses, and produces a daily evidence-led report. It is not an auto-trading system, a next-day price predictor, or a story generator.

Every report statement belongs to exactly one evidence class:

- `FACT`: directly sourced value, release, filing, or calculated deterministic result.
- `OBSERVATION`: description of measured co-movement, relative strength, volume, or regime-rule match.
- `INFERENCE`: interpretation supported by multiple facts/observations and an explicit reasoning rule.
- `HYPOTHESIS`: plausible explanation still lacking discriminating evidence.
- `UNKNOWN`: insufficient, stale, contradictory, or unavailable evidence.

No language model is allowed to promote a hypothesis to fact. Narrative generation, if added later, receives a bounded evidence packet and must cite fact IDs.

## 2. Architectural principles

1. **Point-in-time first.** Store observation date, source release time, source revision/vintage, and retrieval time separately. Historical regeneration may use only information available by that run's `as_of` cutoff.
2. **Canonical concepts, provider-specific symbols.** `DXY` is a node; `DX-Y.NYB` is one provider mapping. A broad trade-weighted dollar index must never silently replace DXY.
3. **Raw before derived.** Preserve source payload metadata and normalized rows. Returns, surprises, relative strength, z-scores, correlations, and regimes are deterministic derivatives.
4. **Fail soft, disclose hard.** A failed optional provider creates a freshness/error record and an `UNKNOWN` section; it does not crash the whole report. Required-series failure makes the run `DEGRADED`, never silently complete.
5. **Causal graph is curated.** Correlation is stored as validation evidence, not converted into a causal edge.
6. **Idempotent reruns.** Unique natural keys and upserts make `--date YYYY-MM-DD` safe. A run has a manifest containing config hash, code version, provider status, and data cutoff.
7. **Provider independence.** Fetching, normalization, storage, analytics, graph construction, and reporting are separate contracts.

## 3. System layout

```text
macro_graph/
├── ARCHITECTURE.md
├── README.md
├── pyproject.toml
├── config/
│   ├── assets.yaml
│   ├── relationships.yaml
│   └── settings.example.yaml
├── data/                       # local SQLite/cache; gitignored
├── docs/
│   └── MVP_IMPLEMENTATION_PLAN.md
├── src/macro_graph/
│   ├── domain/                 # typed records and evidence vocabulary
│   ├── providers/              # external source adapters only
│   ├── collectors/             # orchestration + normalization
│   ├── storage/                # SQLite migrations/repositories
│   ├── analysis/               # returns, rates, correlations, regimes
│   ├── graph/                  # curated NetworkX graph export
│   ├── reports/                # evidence packet + Markdown renderer
│   └── jobs/                   # daily pipeline entry point
├── tests/
└── output/
    ├── snapshots/
    ├── graphs/
    └── reports/
```

Dependency direction is one-way:

`jobs -> collectors/storage/analysis/graph/reports -> domain`

Providers implement domain contracts and never import report or graph code.

## 4. Data-source strategy

### MVP sources

| Need | Canonical item | Primary | Fallback / limitation |
|---|---|---|---|
| Effective Fed Funds | `FED_FUNDS_EFFECTIVE` | FRED `DFF` | Daily effective rate is not the target-range midpoint |
| Treasury yields | `US02Y`, `US10Y` | U.S. Treasury daily par curve | FRED `DGS2`, `DGS10`; holidays/staleness explicit |
| 10Y real yield | `US_REAL_YIELD_10Y` | FRED `DFII10` | TIPS constant-maturity estimate, not a single bond |
| 10Y breakeven | `US_BREAKEVEN_10Y` | FRED `T10YIE` | Model/market liquidity effects remain |
| Dollar | `DXY` | pluggable licensed/market feed | MVP convenience mapping may be `DX-Y.NYB`; never substitute FRED broad index without relabeling |
| Gold | `GOLD` | pluggable market feed | MVP may use `GC=F`, a futures proxy, clearly labeled |
| Brent | `BRENT` | pluggable market feed | MVP may use `BZ=F`, front-month/continuous futures proxy, not spot |
| Equity indices/ETF | `SP500`, `NASDAQ`, `SOXX` | pluggable market feed | MVP mappings `^GSPC`, `^IXIC`, `SOXX` |
| Companies | listed tickers | pluggable market feed | NVDA, AVGO, MU, SNDK, INTC, LITE, GLW |

FRED supports observations plus real-time/vintage parameters, so the normalized model retains vintage metadata. Treasury is preferred for nominal curve truth; FRED is useful as a normalized fallback. The market adapter begins with a convenience implementation only after license/reliability acceptance, behind `MarketDataProvider`.

### Later official sources

- BLS API: CPI, PPI, payrolls, unemployment, earnings.
- BEA API: PCE, core PCE, GDP.
- EIA API v2: petroleum balances, inventories, and energy fundamentals.
- Federal Reserve: FOMC statements, calendars, target range, speeches.
- SEC EDGAR data APIs: submissions and company facts; preserve filing/accession provenance.
- CFTC Public Reporting Environment: weekly COT; never describe weekly positioning as daily flow.
- CME FedWatch official REST API: preferred if licensed. Current official offering is paid. The adapter must support `UNAVAILABLE` and cached last-known data; HTML scraping is an isolated, disabled-by-default experimental adapter.

### Source contract

Every fetch result includes:

```text
provider, series_id, canonical_id, observed_at, released_at,
available_at, retrieved_at, vintage, value, unit, frequency,
quality_flags, source_url, raw_payload_hash
```

`available_at` is the earliest timestamp the system may use the record. If it cannot be established, the conservative value is `retrieved_at` and the row receives `availability_inferred`.

## 5. Time and price semantics

- Store timestamps in UTC; retain source timezone and render in `America/New_York` plus local timezone when useful.
- `run_date` is a U.S. market session date, not the machine's calendar date.
- Daily close data is usable only after provider completion/finality rules pass.
- Returns use adjusted close for investment comparisons by default; raw OHLC and volume stay available. Every metric declares its price basis.
- Macro series use last observation **available by cutoff**, not forward-filled without an explicit `stale_days` field.
- Monthly releases require a period (`2026-08`) distinct from a release timestamp and vintage.
- Historical rerun defaults to point-in-time mode. `--latest-vintage` is a separate research mode and must be labeled.

## 6. SQLite model

SQLite uses WAL mode, foreign keys, UTC ISO-8601 timestamps, and schema migrations.

Core tables:

### Reference data

- `assets(id, canonical_symbol, name, asset_class, subtype, currency, active_from, active_to, metadata_json)`
- `companies(asset_id, cik, sector, industry, public_status, description, metadata_json)`
- `provider_symbols(provider, canonical_symbol, provider_symbol, valid_from, valid_to, metadata_json)`
- `graph_nodes(node_id, node_type, label, metadata_json, created_at, updated_at)`

OpenAI is a private-company ecosystem node with `public_status='private'`; it has no market-price mapping.

### Facts and observations

- `market_prices(asset_id, session_date, ts, interval, open, high, low, close, adj_close, volume, currency, price_basis, provider, retrieved_at, payload_hash, quality_flags_json)`
- `macro_indicators(series_id, period, observed_at, released_at, available_at, value, unit, frequency, vintage, provider, retrieved_at, payload_hash, quality_flags_json)`
- `economic_events(event_id, event_type, scheduled_at, released_at, period, actual, consensus, previous, revised_previous, unit, provider, source_url, status)`
- `event_surprises(event_id, surprise_abs, surprise_std, calculation_version, calculated_at)`
- `news_events(event_id, published_at, entity_ids_json, title, source, source_url, content_hash, evidence_status)`

Important uniqueness constraints:

- prices: `(asset_id, interval, ts, provider)`
- macro: `(series_id, period, vintage, provider)`
- event: stable provider event ID, otherwise `(event_type, scheduled_at, period, provider)`

### Causal and analytical data

- `relationships(relationship_id, source_node, target_node, relationship_type, direction, weight, confidence, lag_min_days, lag_max_days, regime_scope, description, source_reference, valid_from, valid_to, created_at, updated_at)`
- `relationship_evidence(relationship_id, evidence_id, evidence_type, window, statistic, value, sample_size, as_of, method_version)`
- `derived_metrics(metric_id, entity_id, as_of, window, metric_name, value, unit, method_version, inputs_hash, quality_flags_json)`
- `regime_results(as_of, regime, score, confidence, rule_id, evidence_json, method_version)`
- `daily_snapshots(run_date, as_of, status, schema_version, config_hash, payload_json, created_at)`
- `reports(run_date, as_of, path, content_hash, status, evidence_manifest_json, created_at)`
- `pipeline_runs(run_id, run_date, as_of, started_at, finished_at, status, code_version, config_hash, stages_json, errors_json)`

The JSON snapshot is an export, not the primary database.

## 7. Knowledge graph

Node types include `policy`, `rate`, `currency`, `commodity`, `macro_indicator`, `industry_demand`, `industry_segment`, `public_company`, `private_company`, `index`, and `regime`.

An edge is a versioned hypothesis with semantics, not a generic association:

```json
{
  "source": "US_REAL_YIELD_10Y",
  "target": "GOLD",
  "relationship": "opportunity_cost_pressure",
  "direction": "negative",
  "strength": 0.8,
  "confidence": 0.9,
  "expected_lag_days": [0, 20],
  "regime_scope": ["normal_liquidity"],
  "reason": "Gold pays no coupon; higher real yields raise its opportunity cost.",
  "source_reference": "curated:macro-guide:gold-real-yield",
  "last_updated": "2026-09-11T00:00:00Z"
}
```

Strength expresses estimated economic importance; confidence expresses confidence in the edge definition. Neither is inferred from a single correlation. Counterexamples and failure conditions live in metadata (for example central-bank purchases or acute geopolitical stress can weaken the gold/real-yield relationship).

NetworkX builds a directed multigraph and exports `graph.json` and `graph.graphml`. The graph layer also expands an event into an **expected path**, but validation annotates each step with observed sign, magnitude, freshness, and agreement; it never rewrites the expected path as an observed cause.

## 8. Event and evidence model

For each release:

1. Store scheduled event metadata.
2. On release, store actual/consensus/previous and any revision.
3. Calculate absolute and standardized surprise using a versioned historical window.
4. Instantiate candidate paths from curated edge templates.
5. Measure market moves in declared windows, e.g. pre-release to +30m, close-to-close, and 2-day.
6. Label each link `SUPPORTED`, `CONTRADICTED`, `NOT_OBSERVED`, or `INSUFFICIENT_DATA`.

Example: a positive CPI surprise does not prove yields rose *because* of CPI. It creates a timestamped hypothesis; the event window, competing events, and relevant market changes determine how strongly the daily report may describe the inference.

## 9. Analytics

### Metrics

- Returns: 1D, 5D, 20D, 60D, 120D using trading sessions, not calendar-day offsets.
- Relative strength: log return of asset minus benchmark over the same valid sessions; ratios can also be exported for visualization.
- Volume: raw volume, 20-session median ratio, and robust z-score. Indices without comparable volume are marked unavailable.
- Z-score: rolling, minimum sample requirement, winsorization policy recorded in method version.
- Rolling correlations: pairwise-aligned returns at 5D/20D/60D/120D; 1D is co-movement/sign, not statistically meaningful correlation. Include sample size and missingness.

MVP validation pairs: gold/real-yield, gold/DXY, Nasdaq/10Y, SOXX/10Y, Brent/breakeven, LITE/SOXX. `MU / Memory Index` waits until a defensible memory index is selected.

### Capital rotation

The first version reports price/volume proxies only:

- sector and asset relative returns;
- breadth where constituents are available;
- volume confirmation;
- bond/credit proxies later (`TLT`, `HYG`, `GLD`, `IGV`, `SMH`).

Wording is constrained: price relative strength alone yields “observed relative strength,” not “fund inflow.” Verified ETF creations/redemptions, COT changes, or positioning data may raise the evidence level.

### Rule-based regimes

Each rule has thresholds, minimum coverage, conflict handling, and evidence IDs. Multiple regimes may coexist with scores; do not force one winner.

Illustrative rules (thresholds must be calibrated before production):

- `HAWKISH_TIGHTENING`: 2Y yield up, real yield up, DXY up, duration equities weak.
- `GROWTH_SCARE`: nominal yields down, cyclicals weak, credit weak, defensive assets strong.
- `INFLATION_SHOCK`: breakeven and oil up, nominal yields up, long-duration equities weak.
- `AI_HARDWARE_ROTATION`: SOXX outperforms QQQ while software underperforms QQQ, with hardware breadth confirmation.

If fewer than the configured minimum signals are fresh, output `UNKNOWN / INSUFFICIENT EVIDENCE`.

## 10. Daily snapshot contract

`output/snapshots/market_snapshot_YYYYMMDD.json` contains:

```json
{
  "schema_version": "1.0",
  "run": {
    "run_date": "2026-09-10",
    "as_of": "2026-09-11T02:30:00Z",
    "status": "COMPLETE",
    "config_hash": "...",
    "provider_status": {}
  },
  "macro": {},
  "rates": {},
  "fx": {},
  "commodities": {},
  "equity": {},
  "companies": {},
  "relative_strength": {},
  "correlations": {},
  "regimes": [],
  "quality": {"warnings": [], "stale_series": []}
}
```

Each instrument value includes source, provider symbol, price basis, observation/session time, retrieval time, freshness, and quality flags alongside requested metrics.

## 11. Daily pipeline

```text
resolve run_date and as_of cutoff
    -> acquire per-run lock
    -> collect raw/normalized official macro and market data
    -> validate schema, units, freshness, duplicates, and calendar alignment
    -> transactional upsert into SQLite
    -> compute returns/relative strength/z-scores/correlations
    -> classify regimes and evaluate causal-path evidence
    -> export graph.json + graph.graphml
    -> build immutable evidence manifest
    -> render snapshot JSON and Markdown report atomically
    -> record COMPLETE or DEGRADED run manifest
```

Stage outputs are restartable. Files are written to a temporary sibling and atomically renamed. A second run for the same date either reuses matching input hashes or creates a new run manifest and replaces only deterministic exports.

CLI target:

```bash
python -m macro_graph.jobs.daily_job
python -m macro_graph.jobs.daily_job --date 2026-09-10
python -m macro_graph.jobs.daily_job --date 2026-09-10 --as-of 2026-09-11T02:30:00Z
```

Cron launches the command after the U.S. close with a safety delay; the job itself checks the exchange calendar and data completeness. Scheduling should be timezone-aware around U.S. daylight-saving changes rather than assuming one fixed UTC close.

## 12. Daily report design

The report follows the requested ten sections. Every bullet carries a class tag and, where applicable, a source/evidence ID. The renderer receives structured objects, not free-form source payloads.

Example:

```text
[FACT] US02Y rose 12 bp to 4.31% (Treasury, session date, retrieved time).
[OBSERVATION] SOXX outperformed QQQ by 2.3 percentage points over the session.
[INFERENCE, medium confidence] Price action is consistent with a hawkish rate repricing.
[HYPOTHESIS, low confidence] Semiconductor strength may reflect AI hardware rotation.
[UNKNOWN] No fund-flow dataset is available; capital inflow cannot be confirmed.
```

An inference requires declared evidence IDs, a rule ID, confidence, counterevidence, and alternative explanations. Missing evidence renders `UNKNOWN`; templates never fill gaps with generic prose.

## 13. Reliability and operations

- Per-provider timeout, bounded retries with jitter, cache, circuit breaker, and rate-limit compliance.
- Secrets only via environment/keychain; `.env` and database files are ignored.
- Raw response hashes, source URLs, user-agent/contact requirements, and terms/licensing notes are recorded.
- Validation gates: schema/type, nonnegative volume, OHLC consistency, unit/range checks, duplicate keys, suspicious jumps, stale dates, cross-source tolerance.
- Observability: structured logs, stage duration, row counts, last-success timestamp, freshness, retries, and report quality status.
- Backups: periodic SQLite online backup plus config/graph source under Git.
- No automatic orders, broker credentials, or trading actions.

## 14. Testing strategy

- Unit: normalization, returns, basis-point changes, surprise math, point-in-time selection, regime rules.
- Contract: captured provider fixtures and schema-change detection; no network in routine tests.
- Integration: temporary SQLite, migration, idempotent upsert/rerun, degraded provider path.
- Golden files: deterministic snapshot and report structure.
- Graph: schema, direction vocabulary, node existence, GraphML/JSON round trip.
- Lookahead tests: revised macro value and late market close must be excluded before `available_at`.
- Smoke: one opt-in live fetch per provider, separately scheduled from unit tests.

## 15. Deferred decisions

Before coding the actual collectors, confirm:

1. Market data provider and acceptable terms/cost. The convenience MVP can start with yfinance, but it is not an official or SLA-backed source.
2. Exact DXY and commodity definitions: cash index vs futures proxy and contract-roll policy.
3. Report cutoff and preferred schedule timezone.
4. Whether FRED API key and later CME FedWatch subscription are available.
5. Whether historical reruns require true point-in-time market data corrections beyond retained local vintages.

These choices affect provider configuration, not the domain or pipeline architecture.

## 16. Official source references checked for this baseline

- [FRED API and series observations](https://fred.stlouisfed.org/docs/api/fred/series_observations.html): observations, real-time periods, vintages, and missing-value semantics.
- [U.S. Treasury daily par yield curve](https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_yield_curve): official nominal Treasury curve downloads/feeds.
- [BLS Public Data API](https://www.bls.gov/developers/): CPI, PPI, employment, unemployment, and earnings series planned post-MVP.
- [EIA Open Data API v2](https://www.eia.gov/opendata/documentation.php): petroleum and inventory fundamentals planned post-MVP.
- [SEC EDGAR data APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces): submissions and XBRL company facts planned post-MVP.
- [CFTC Commitments of Traders](https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm): weekly positioning data and Public Reporting Environment API.
- [CME FedWatch API](https://www.cmegroup.com/market-data/market-data-api/fedwatch-api.html): official JSON REST product; paid access, so not an MVP hard dependency.

Links and product availability were checked on 2026-09-11. Provider behavior and terms must be revalidated when each adapter is implemented.
