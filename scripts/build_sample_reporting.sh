#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "$0")/.." && pwd)"
node_bin="${NODE_BIN:-node}"

"$node_bin" "$project_root/scripts/build_reporting.mjs" \
  --metrics "$project_root/reporting/fixtures/processed_metrics.csv" \
  --forecasts "$project_root/reporting/fixtures/forecast_results.csv" \
  --output-dir "$project_root/reporting/sample-output" \
  --label "SAMPLE / NOT FOR SHARING"

"$node_bin" "$project_root/scripts/validate_reporting.mjs" \
  --output-dir "$project_root/reporting/sample-output"
