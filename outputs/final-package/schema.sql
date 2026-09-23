CREATE TABLE reported_metric_observation (
    observation_id TEXT PRIMARY KEY,
    period TEXT NOT NULL,
    period_end TEXT NOT NULL,
    metric_name TEXT NOT NULL,
    value_decimal TEXT NOT NULL,
    currency TEXT NOT NULL,
    scale TEXT NOT NULL,
    definition_family TEXT NOT NULL,
    metric_definition_family TEXT NOT NULL,
    vintage_status TEXT NOT NULL,
    source_id TEXT NOT NULL,
    published_at TEXT NOT NULL,
    analysis_use TEXT NOT NULL
);
