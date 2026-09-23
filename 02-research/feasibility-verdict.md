# Vintage-audit feasibility verdict

Evidence cutoff: **2026-09-20**  
Candidate window: **Q3 2023–Q3 2025**  
Verdict: **PIVOT — build the descriptive variance bridge first; do not claim forecast performance**

## What the audit established

Nine SEC-hosted Coinbase shareholder-letter exhibits were downloaded and hashed. The reviewed long-form file contains the first-reported consumer transaction revenue and consumer trading volume for every quarter in the candidate window, plus the Q3 2023 and Q4 2023 revenue recasts disclosed in Q1 2024. Every observation points to one inspected exhibit in `artifacts/source-register.csv` and retains that exhibit's SEC accession, acceptance timestamp, URL, local hash, units, definition family, and vintage status.

The figures are sufficient for a reproducible historical **descriptive** revenue/volume analysis. They are not sufficient for the planned forecast tournament under its predeclared gate.

## Why this is a PIVOT

The project rule requires at least eight comparable training observations before the first holdout and four chronological holdouts under one definition family. That implies at least twelve comparable quarters. The candidate window contains only nine quarters.

There is also a revenue-definition break at Q1 2024. Coinbase moved Base sequencer and payment-related revenue from `Consumer, net` to `Other transaction revenue` and recast prior periods. The two original-vintage revenue observations before the change—$274.5 million for Q3 2023 and $492.5 million for Q4 2023—are not definition-compatible with later consumer revenue. The Q1 2024 letter supplies comparable recasts of $247.0 million and $468.9 million, respectively, but those values were not knowable at the earlier publication cutoffs. They may be used in a later-vintage descriptive series, never silently substituted into an earlier information set.

Consumer trading volume remains a matched-spot measure through Q3 2025. It excludes derivatives, while consumer transaction revenue can include revenue not directly associated with reported spot volume. Therefore `consumer revenue / consumer volume` is an **effective-yield proxy**, not a fee rate, price, or causal measure. Q4 2025 is outside this panel and must remain quarantined because Coinbase later changed its Trading Volume definition and recast prior periods.

## Allowed first build

Proceed with one clearly labeled descriptive bridge using the post-reclassification revenue family:

- Use the Q1 2024 publication vintage for recast Q3 2023 and Q4 2023 revenue, followed by first-reported Q1 2024–Q3 2025 revenue.
- Pair it with matched-spot consumer volume, disclosing the mismatch between revenue scope and spot-volume scope.
- Calculate effective yield only as `revenue / volume`; retain the source units and use decimal arithmetic.
- Feature Q4 2024 only as an actual-versus-prior-quarter or actual-versus-explicit-planning-assumption bridge. Do not relabel an ex-post comparison as a forecast.
- Show both original and recast pre-Q1-2024 revenue in a definition-change appendix.

## Stop rules and fallback paths

1. **Forecast claims:** STOP unless an expanded vintage-safe panel reaches twelve comparable quarters and passes overlap reconciliation.
2. **Two-factor exhaustive bridge:** STOP if the chosen forecast assumption is not expressed as volume × effective yield; otherwise disclose any residual.
3. **Causal or fee-rate language:** STOP. Use “descriptive effective-yield effect.”
4. **Q4 2025 or later data:** quarantine in a separate definition family until the new volume definition and all recasts are reconciled.
5. **If the reviewer requires original-vintage-only revenue:** use Q1 2024–Q3 2025 only (seven quarters) and keep the artifact descriptive.

## Files produced

- `data/raw/*-shareholder-letter.html`: frozen SEC exhibit copies.
- `data/raw/index-*.html`: filing-index evidence linking accessions to exhibits.
- `data/raw/sec-submissions-cik0001679788.json`: SEC filing metadata snapshot.
- `data/processed/reported-metric-observations.csv`: reviewed long-form observations.
- `data/processed/analytics-ready-metric-observations.csv`: normalized 18-row descriptive series with engine-compatible `published_at`, `currency`, `scale`, and one paired `definition_family`; metric-level definition and vintage fields remain explicit.
- `artifacts/source-register.csv`: source-level provenance and hashes.

No model was fit, no forecast was scored, and no claim of predictive superiority was tested.
