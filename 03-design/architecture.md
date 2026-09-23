# Data model and analytical architecture

## Flow

`frozen primary documents → source/vintage registry → reviewed metric observations → cutoff-safe forecast runs → results and exact bridge → workbook/memo/demo`

SQLite is the canonical analytical store; CSV snapshots are portable; Excel is the reviewer interface. SQL creates final tables. Workbook formulas independently recompute key numbers rather than hiding logic in a custom application.

## Core tables

### `source_document`

`source_id`, `title`, `url`, `accession_no`, `published_at`, `retrieved_at`, `sha256`, `document_type`, `review_status`.

### `metric_definition`

`definition_id`, `metric_name`, `definition_text`, `valid_from`, `valid_to`, `publication_vintage`, `original_or_recast`, `source_id`, `comparability_notes`.

### `reported_metric_observation`

`observation_id`, `metric_name`, `period_start`, `period_end`, `value_decimal`, `currency`, `scale`, `definition_id`, `source_id`, `published_at`, `evidence_class`, `reviewer_status`.

Uniqueness is `(metric_name, period_end, definition_id, source_id)`. Later recasts create rows; they do not update prior rows.

### `forecast_run`

`run_id`, `target_period`, `information_cutoff`, `model_id`, `training_start`, `training_end`, `definition_family`, `parameter_json`, `code_version`, `created_at`.

### `forecast_result`

`run_id`, `predicted_revenue`, `actual_revenue`, `signed_error`, `absolute_error`, `eligible_for_score`, `exclusion_reason`.

### `variance_bridge`

`run_id`, `forecast_volume`, `actual_volume`, `forecast_yield`, `actual_yield`, `volume_effect`, `yield_effect`, `residual`, `bridge_order`, `rounding_tolerance`.

## Model contract

Let consumer revenue be `R`, consumer volume `V`, and calculated effective yield `y = R / V`.

- Baseline 1: `R_hat[t] = R[t-1]`.
- Baseline 2: `R_hat[t] = R[t-4]` when available.
- Driver model: `R_hat[t] = V_hat[t] × y_hat[t]`.
- First volume forecast: recent-quarter median growth, clipped to a predeclared range set before holdout scoring.
- First yield forecast: trailing four-quarter median effective yield.

Do not fit more than two driver parameters. Realized `V[t]` is forbidden in the ex-ante prediction and permitted only after close for variance analysis.

## Exact bridge

Fixed order, volume then yield:

`volume_effect = (V_actual - V_forecast) × y_forecast`

`yield_effect = V_actual × (y_actual - y_forecast)`

Then `volume_effect + yield_effect = R_actual - R_forecast` algebraically when `R = V × y`. If the selected revenue/volume pair is not complete, add an explicit residual and stop calling the two-factor result exhaustive. Show the alternate ordering in validation because it reallocates the interaction.

## Evaluation

Freeze chronological holdouts before inspecting results. Report every eligible quarter, absolute error, MAE, signed bias, and WAPE. Avoid MAPE. Model selection uses the same holdouts and definition family. A driver-model loss is published, not tuned away.

## Controls

- Cutoff join: `published_at <= information_cutoff`.
- Definition-family join: incompatible vintages fail closed.
- Decimal money and explicit scale/currency.
- Overlap reconciliation across successive five-quarter tables.
- One hand-worked quarter independently checks SQL and workbook.
- Generated narrative may only reference final reviewed tables and citations.

