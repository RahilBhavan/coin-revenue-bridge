PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS reported_metric_observation (
    observation_id TEXT PRIMARY KEY,
    metric_name TEXT NOT NULL,
    period_start TEXT NOT NULL CHECK (period_start GLOB '????-??-??'),
    period_end TEXT NOT NULL CHECK (period_end GLOB '????-??-??'),
    value_decimal TEXT NOT NULL,
    currency TEXT NOT NULL,
    scale TEXT NOT NULL,
    definition_id TEXT NOT NULL,
    definition_family TEXT NOT NULL,
    original_or_recast TEXT NOT NULL CHECK (original_or_recast IN ('original', 'recast')),
    source_id TEXT NOT NULL,
    published_at TEXT NOT NULL CHECK (published_at GLOB '????-??-??'),
    evidence_class TEXT NOT NULL,
    reviewer_status TEXT NOT NULL,
    analysis_use TEXT NOT NULL DEFAULT 'forecast_eligible',
    UNIQUE (metric_name, period_end, definition_id, source_id)
);

CREATE INDEX IF NOT EXISTS idx_observation_cutoff
ON reported_metric_observation(definition_family, published_at, period_end, metric_name);
