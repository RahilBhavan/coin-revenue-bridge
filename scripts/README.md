# Analytical core reproduction

Requires Python 3.9+ and only the standard library. The fixture is synthetic and
exists to verify behavior; it is not a Coinbase forecast or sourced result.

The workbook is built with a separate spreadsheet tool that is not part of this repo; the committed workbook is the source of truth.

Run the automated suite:

```sh
python3 -m unittest discover -s tests -v
```

Run one fixture forecast and exact bridge without writing package artifacts:

```sh
python3 scripts/analyze.py \
  --database /tmp/strategic-finance.sqlite \
  --input tests/fixtures/reported_metrics.csv \
  --target-period 2025-03-31 \
  --information-cutoff 2025-02-15 \
  --definition-family consumer_v1
```

The input may use the canonical long-form columns shown in the test fixture or
the source-data contract in `data/processed/reported-metric-observations.csv`.
The latter is deterministically normalized during ingestion: `period` becomes
`period_start`, `unit` splits into currency/scale, `published_at_utc` is reduced
to its UTC date, and `definition_id` defaults to its supplied definition family.
No source file is changed.

Forecast history is restricted to observations public by the cutoff. When
revenue and volume have distinct compatible definition families, pass them as
`REVENUE_FAMILY|VOLUME_FAMILY`; a single family remains supported for canonical
fixtures. Values are normalized to USD millions before yield calculation.
Actual target-period volume is loaded only after the forecast is complete, for
the variance bridge.

Rows marked `analysis_use=descriptive_only` are refused by forecast mode. Use
the descriptive bridge for the SEC-derived feasibility dataset:

```sh
python3 scripts/descriptive_bridge.py \
  --database /tmp/strategic-finance-bridge.sqlite \
  --input data/processed/analytics-ready-metric-observations.csv \
  --comparison-period 2024-12-31 \
  --target-period 2025-03-31 \
  --information-cutoff 2025-05-08 \
  --definition-family PAIR-REV-POST2024Q1-VOL-SPOT-PRE2025Q4 \
  --format json
```

Use `--format csv` for a one-row reporting feed. Both formats label the analysis
as descriptive and include explicit revenue, volume, and effective-yield units.
Forecast-eligible real data also requires at least 12 comparable historical
quarters; synthetic test rows are isolated from that release-readiness gate.

## "No forecast" post images

`build_no_forecast_chart.py` renders `docs/no-forecast-chart-landscape.png` (1024x576 at 2x) and
`docs/no-forecast-chart-square.png` (1024x1024 at 2x), plus `docs/no-forecast-chart-alt.txt`.
It reads the 12-quarter gate from `README.md` and `outputs/final-package/validation-report.md`
and the nine quarters from `outputs/final-package/analytics-ready-metrics.csv`, and stops if
they disagree. The footer date and sha are those of the last commit that changed the data files.
It needs Chromium; fonts are bundled in `scripts/assets/fonts/`. Before each screenshot it
checks that all text is at least 26px, that nothing overflows and that the three fonts loaded.

```sh
python3 scripts/build_no_forecast_chart.py
```
