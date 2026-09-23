# Reporting pipeline

This directory contains the reviewer-facing generation path for the Coinbase
Strategic Finance project. It consumes two frozen CSVs and produces one
inspectable workbook, a draft decision memo, a draft reviewer packet, and a
machine-readable manifest.

## Input contracts

`processed_metrics.csv` must contain:

`period_end,consumer_transaction_revenue_mm,consumer_trading_volume_bn,published_at,definition_family,evidence_label,source_reference`

`forecast_results.csv` must contain:

`target_period,model_id,information_cutoff,predicted_revenue_mm,actual_revenue_mm,forecast_volume_bn,actual_volume_bn,forecast_yield_pct,actual_yield_pct,eligible_for_score,exclusion_reason,definition_family`

Values use USD millions for revenue, USD billions for volume, and percentage
points for yield. Yield values therefore use `0.15` for 0.15%, not 15%.
Required numeric fields may not be blank for eligible rows. `model_id` must be
one of `prior_quarter`, `prior_year`, or `driver`.

## Sample build

The checked-in fixture data is synthetic and exists only to prove the reporting
path. Run:

```bash
scripts/build_sample_reporting.sh
```

The command regenerates `reporting/sample-output/` deterministically and then
runs workbook and package validation. No internet access or dependency install
is required.

For real processed outputs, call the builder directly:

```bash
node scripts/build_reporting.mjs \
  --metrics path/to/processed_metrics.csv \
  --forecasts path/to/forecast_results.csv \
  --output-dir path/to/output \
  --label DRAFT
```

`DRAFT` and `SAMPLE / NOT FOR SHARING` are the only accepted labels. This
generator does not produce a share-ready artifact; the validation report and
human review gates remain separate.

## Descriptive pivot

The current feasibility verdict is `PIVOT—descriptive bridge`. The separate
contract in `descriptive-bridge-schema.md` and builder
`scripts/build_descriptive_reporting.mjs` produce a descriptive workbook,
memo, reviewer packet, preview, and manifest without forecast language. The
reader-facing workbook always displays `DESCRIPTIVE / NOT A FORECAST`; fixture
builds also display `SAMPLE / NOT FOR SHARING`.

Run the synthetic contract check with:

```bash
scripts/build_sample_descriptive_reporting.sh
```

Do not run the earlier forecast builder against SEC-derived data unless the
project passes a future `GO—forecast` gate.

## Workbook design

The descriptive workbook is organized for a finance reviewer:

- `Descriptive Review` leads with the Q3-to-Q4 2024 bridge, management
  interpretation, a reconciliation check, and a native editable nine-quarter
  consumer transaction revenue chart.
- `Bridge Calculation` exposes the fixed-order volume and calculated-yield
  formulas and residual.
- `Definition Appendix` preserves original and recast Q3/Q4 2023 consumer
  revenue side by side. It quantifies the reporting-definition change rather
  than silently overwriting the original publication vintage.
- `Metric Inputs` contains typed quarterly values, calculated effective yield,
  publication dates, definition families, source IDs, and visible SEC URLs.

The workbook and generated prose remain labeled `DESCRIPTIVE / NOT A
FORECAST`. Calculated effective yield is a proxy, not a reported fee rate or a
causal claim.

The earlier forecast workbook design remains documented below for a future
`GO—forecast` gate.

- `Forecast Review` is the reviewer view. It shows the featured driver-model
  forecast, baseline comparison, exact bridge, aggregate holdout errors, and
  the strongest limitation.
- `Forecast Build` exposes every forecast row and formula-driven signed error,
  absolute error, yield derivation, and volume-then-yield bridge.
- `Metric Inputs` preserves the processed metric rows and provenance fields.

The workbook uses formulas for every calculated result. Missing inputs stay
unavailable rather than becoming zero. The build formulas do not depend on an
audit or status cell.
