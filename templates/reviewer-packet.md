# Coinbase Strategic Finance reviewer packet

**{{STATUS_LABEL}}**  
**Featured period:** {{FEATURED_PERIOD}}  
**Information cutoff:** {{INFORMATION_CUTOFF}}

## Review in two minutes

| Item | Result |
|---|---:|
| Driver forecast | ${{DRIVER_FORECAST_MM}}m |
| Prior-quarter baseline | ${{BASELINE_FORECAST_MM}}m |
| Actual revenue | ${{ACTUAL_REVENUE_MM}}m |
| Driver forecast variance | ${{TOTAL_VARIANCE_MM}}m |
| Volume effect | ${{VOLUME_EFFECT_MM}}m |
| Effective-yield effect | ${{YIELD_EFFECT_MM}}m |
| Bridge residual | ${{BRIDGE_RESIDUAL_MM}}m |

## Method

1. Forecast information is limited to records available on or before the stated cutoff.
2. The workbook compares prior-quarter, prior-year, and volume-times-yield models.
3. Holdout errors remain visible for every eligible model and period.
4. The bridge uses a fixed volume-then-yield order and exposes any residual.

## Evidence labels

- **Reported:** source observations supplied in `processed_metrics.csv`.
- **Calculated:** effective yield, errors, aggregate metrics, and bridge effects.
- **Assumed:** forecast volume and forecast effective yield supplied by the analytical pipeline.

## Definition and limitation note

All rows in this package use definition family `{{DEFINITION_FAMILY}}`.
{{LIMITATION_TEXT}}

## Critique question

What additional evidence would you require before changing the effective-yield assumption?

