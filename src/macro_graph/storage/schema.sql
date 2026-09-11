PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

CREATE TABLE IF NOT EXISTS assets (
    id INTEGER PRIMARY KEY,
    canonical_symbol TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    asset_class TEXT NOT NULL,
    subtype TEXT,
    currency TEXT,
    active_from TEXT,
    active_to TEXT,
    metadata_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS companies (
    asset_id INTEGER PRIMARY KEY REFERENCES assets(id),
    cik TEXT,
    sector TEXT,
    industry TEXT,
    public_status TEXT NOT NULL CHECK (public_status IN ('public', 'private')),
    description TEXT,
    metadata_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS provider_symbols (
    provider TEXT NOT NULL,
    canonical_symbol TEXT NOT NULL,
    provider_symbol TEXT NOT NULL,
    valid_from TEXT,
    valid_to TEXT,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    PRIMARY KEY (provider, canonical_symbol, valid_from)
);

CREATE TABLE IF NOT EXISTS market_prices (
    asset_id INTEGER NOT NULL REFERENCES assets(id),
    session_date TEXT NOT NULL,
    ts TEXT NOT NULL,
    interval TEXT NOT NULL,
    open TEXT,
    high TEXT,
    low TEXT,
    close TEXT NOT NULL,
    adj_close TEXT,
    volume TEXT,
    currency TEXT,
    price_basis TEXT NOT NULL,
    provider TEXT NOT NULL,
    retrieved_at TEXT NOT NULL,
    payload_hash TEXT,
    quality_flags_json TEXT NOT NULL DEFAULT '[]',
    PRIMARY KEY (asset_id, interval, ts, provider)
);

CREATE TABLE IF NOT EXISTS macro_indicators (
    series_id TEXT NOT NULL,
    period TEXT NOT NULL,
    observed_at TEXT NOT NULL,
    released_at TEXT,
    available_at TEXT NOT NULL,
    value TEXT,
    unit TEXT NOT NULL,
    frequency TEXT NOT NULL,
    vintage TEXT NOT NULL,
    provider TEXT NOT NULL,
    retrieved_at TEXT NOT NULL,
    payload_hash TEXT,
    quality_flags_json TEXT NOT NULL DEFAULT '[]',
    PRIMARY KEY (series_id, period, vintage, provider)
);

CREATE TABLE IF NOT EXISTS economic_events (
    event_id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL,
    scheduled_at TEXT NOT NULL,
    released_at TEXT,
    period TEXT,
    actual TEXT,
    consensus TEXT,
    previous TEXT,
    revised_previous TEXT,
    unit TEXT,
    provider TEXT NOT NULL,
    source_url TEXT,
    status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS event_surprises (
    event_id TEXT NOT NULL REFERENCES economic_events(event_id),
    surprise_abs TEXT,
    surprise_std TEXT,
    calculation_version TEXT NOT NULL,
    calculated_at TEXT NOT NULL,
    PRIMARY KEY (event_id, calculation_version)
);

CREATE TABLE IF NOT EXISTS relationships (
    relationship_id TEXT PRIMARY KEY,
    source_node TEXT NOT NULL,
    target_node TEXT NOT NULL,
    relationship_type TEXT NOT NULL,
    direction TEXT NOT NULL CHECK (direction IN ('positive', 'negative', 'mixed', 'conditional')),
    weight REAL NOT NULL CHECK (weight BETWEEN 0 AND 1),
    confidence REAL NOT NULL CHECK (confidence BETWEEN 0 AND 1),
    lag_min_days INTEGER,
    lag_max_days INTEGER,
    regime_scope TEXT,
    description TEXT NOT NULL,
    source_reference TEXT NOT NULL,
    valid_from TEXT NOT NULL,
    valid_to TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS graph_nodes (
    node_id TEXT PRIMARY KEY,
    node_type TEXT NOT NULL,
    label TEXT NOT NULL,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS relationship_evidence (
    relationship_id TEXT NOT NULL REFERENCES relationships(relationship_id),
    evidence_id TEXT NOT NULL,
    evidence_type TEXT NOT NULL,
    window TEXT,
    statistic TEXT,
    value TEXT,
    sample_size INTEGER,
    as_of TEXT NOT NULL,
    method_version TEXT NOT NULL,
    PRIMARY KEY (relationship_id, evidence_id, method_version)
);

CREATE TABLE IF NOT EXISTS derived_metrics (
    metric_id TEXT PRIMARY KEY,
    entity_id TEXT NOT NULL,
    as_of TEXT NOT NULL,
    window TEXT NOT NULL,
    metric_name TEXT NOT NULL,
    value TEXT,
    unit TEXT NOT NULL,
    method_version TEXT NOT NULL,
    inputs_hash TEXT NOT NULL,
    quality_flags_json TEXT NOT NULL DEFAULT '[]',
    UNIQUE (entity_id, as_of, window, metric_name, method_version)
);

CREATE TABLE IF NOT EXISTS daily_snapshots (
    run_date TEXT NOT NULL,
    as_of TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('COMPLETE', 'DEGRADED', 'FAILED')),
    schema_version TEXT NOT NULL,
    config_hash TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY (run_date, as_of, config_hash)
);

CREATE TABLE IF NOT EXISTS regime_results (
    as_of TEXT NOT NULL,
    regime TEXT NOT NULL,
    score REAL NOT NULL,
    confidence REAL NOT NULL,
    rule_id TEXT NOT NULL,
    evidence_json TEXT NOT NULL,
    method_version TEXT NOT NULL,
    PRIMARY KEY (as_of, regime, rule_id, method_version)
);

CREATE TABLE IF NOT EXISTS reports (
    run_date TEXT NOT NULL,
    as_of TEXT NOT NULL,
    path TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    status TEXT NOT NULL,
    evidence_manifest_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY (run_date, as_of, path)
);

CREATE TABLE IF NOT EXISTS pipeline_runs (
    run_id TEXT PRIMARY KEY,
    run_date TEXT NOT NULL,
    as_of TEXT NOT NULL,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    status TEXT NOT NULL,
    code_version TEXT,
    config_hash TEXT NOT NULL,
    stages_json TEXT NOT NULL DEFAULT '{}',
    errors_json TEXT NOT NULL DEFAULT '[]'
);

CREATE INDEX IF NOT EXISTS idx_prices_session ON market_prices(session_date, asset_id);
CREATE INDEX IF NOT EXISTS idx_macro_available ON macro_indicators(series_id, available_at);
CREATE INDEX IF NOT EXISTS idx_events_scheduled ON economic_events(scheduled_at, event_type);
