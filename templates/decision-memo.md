# Coinbase Strategic Finance forecast review

**{{STATUS_LABEL}}**  
**Information cutoff:** {{INFORMATION_CUTOFF}}  
**Featured period:** {{FEATURED_PERIOD}}

## Decision

Use the driver model as a transparent planning reference only after it clears
the cutoff, definition-vintage, and source-reconciliation gates. For this
{{ARTIFACT_TYPE}} build, the model forecast is **${{DRIVER_FORECAST_MM}} million**
against **${{ACTUAL_REVENUE_MM}} million** actual revenue. The prior-quarter
baseline forecast is **${{BASELINE_FORECAST_MM}} million**.

## What changed

The exact volume-then-yield bridge attributes **${{VOLUME_EFFECT_MM}} million**
to volume and **${{YIELD_EFFECT_MM}} million** to calculated effective yield.
The components reconcile to the **${{TOTAL_VARIANCE_MM}} million** forecast
variance, subject to the workbook's displayed rounding tolerance.

## Holdout evidence

Across {{DRIVER_HOLDOUT_COUNT}} eligible driver-model holdouts, mean absolute
error is **${{DRIVER_MAE_MM}} million**, signed bias is
**${{DRIVER_BIAS_MM}} million**, and WAPE is **{{DRIVER_WAPE_PCT}}%**.

## Recommendation and strongest objection

Keep the prior-quarter baseline in every review. Advance the driver model only
if it adds decision value without weakening cutoff discipline or definition
comparability. The strongest objection is that calculated effective yield is a
proxy, not a reported causal driver, and the small historical sample cannot
establish stability.

## Evidence boundary

This document is generated from the two CSV inputs listed in the accompanying
manifest. Values labeled as calculated are not reported Coinbase metrics.
{{LIMITATION_TEXT}}

