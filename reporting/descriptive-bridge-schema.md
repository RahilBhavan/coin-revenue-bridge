# Descriptive bridge input contract

Use this path after a `PIVOT—descriptive bridge` feasibility verdict. It does
not accept, calculate, or imply a forecast.

`descriptive_bridge.csv` contains one row per chronological comparison:

`comparison_id,from_period,to_period,from_revenue_mm,to_revenue_mm,from_volume_bn,to_volume_bn,from_yield_pct,to_yield_pct,definition_family,evidence_label,source_reference`

- Revenue is USD millions.
- Volume is USD billions.
- Yield is percentage points, so `1.75` means 1.75%.
- `from_yield_pct` and `to_yield_pct` must equal revenue divided by volume
  after unit conversion, within the upstream declared tolerance.
- Both periods must use the same definition family. Split incompatible
  definition vintages upstream rather than forcing a bridge.
- Evidence labels identify reported, calculated, assumed, or synthetic values.

The fixed-order descriptive bridge is:

`volume effect = (to volume - from volume) × from yield`

`yield effect = to volume × (to yield - from yield)`

`residual = revenue change - volume effect - yield effect`

The factor `1,000` converts USD billions to USD millions. This decomposition
describes an algebraic change and does not establish causality.

Build command once SEC-derived inputs are ready:

```bash
node scripts/build_descriptive_reporting.mjs \
  --metrics path/to/processed_metrics.csv \
  --bridge path/to/descriptive_bridge.csv \
  --output-dir path/to/output \
  --label "DESCRIPTIVE / NOT A FORECAST"
```

Use `--label "SAMPLE / NOT FOR SHARING"` only with synthetic fixture data.

The generated workbook also reads the checked-in reviewed observation register
and source register to populate the reporting-definition appendix and source
URLs. The real build requires all nine comparable quarters in the
processed metrics input. Fixture builds may use a shorter series to test the
generation path.
