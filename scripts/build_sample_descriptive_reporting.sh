#!/usr/bin/env bash
set -euo pipefail
project_root="$(cd "$(dirname "$0")/.." && pwd)"
node_bin="${NODE_BIN:-node}"
"$node_bin" "$project_root/scripts/build_descriptive_reporting.mjs" \
  --metrics "$project_root/reporting/fixtures/processed_metrics.csv" \
  --bridge "$project_root/reporting/fixtures/descriptive_bridge.csv" \
  --output-dir "$project_root/reporting/descriptive-sample-output" \
  --label "SAMPLE / NOT FOR SHARING"
"$node_bin" "$project_root/scripts/validate_descriptive_reporting.mjs" \
  --output-dir "$project_root/reporting/descriptive-sample-output"
