# Coinbase revenue bridge: analysis package

Status: **DESCRIPTIVE / NOT A FORECAST**  
Evidence cutoff: **September 20, 2026**

## Decision

Use the Q3-to-Q4 2024 consumer transaction revenue bridge and editable planning sensitivities as decision-support diagnostics. Do not present a forecasting or causal-performance claim. The public panel contains nine comparable quarters, below the predeclared twelve-quarter gate.

## Start here

1. `decision-memo.pdf` - two-page decision and evidence boundary.
2. `revenue-analysis.xlsx` - inspectable seven-sheet model with trend, sensitivities, three attribution methods, definition crosswalks, and sources.
3. `reviewer-packet.pdf` - two-page challenge packet.
4. `demo.webm` or `demo.html` - three-minute captioned walkthrough.
5. `social-cut.mp4` - 30-second captioned H.264 social preview.
6. `validation-report.md` - executed V-01 through V-16 checks and limitations.

## Reproducibility files

- `reported-metrics.csv` - reviewed long-form source observations.
- `analytics-ready-metrics.csv` - normalized descriptive series.
- `descriptive-bridge.csv` - workbook bridge input.
- `bridge-attribution.csv` - volume-first, yield-first, and symmetric allocations.
- `planning-scenarios.csv` - editable illustrative sensitivity inputs and outputs.
- `definition-reconciliation.csv` - Q2-Q4 2025 earlier-versus-later volume vintages.
- `analysis.sql` - fixed-order SQL decomposition.
- `schema.sql` and `reproduce.py` - package-local executable reproduction path.
- `source-register.csv` - SEC accessions, URLs, timestamps, package-local paths, and SHA-256 hashes.
- `raw-sources/` - frozen SEC source documents covered by the source register.
- `overlap-reconciliation.csv` - repeated-quarter reconciliation across SEC tables.
- `ai-contribution.md` - tool contribution and human-review boundary.
- `package-manifest.json` - artifact hashes and sizes.

## Claim boundary

The $863.8M reported revenue increase is decomposed algebraically into an $852.9M volume effect and $10.9M calculated effective-yield effect under a fixed volume-first order. Effective yield is a proxy, not a reported fee rate or causal driver. Reversing bridge order reallocates about $7.0M while preserving the total.

The symmetric Shapley allocation averages both valid factor orders, assigning $856.4M to volume and $7.4M to calculated yield. The planning cases are mechanical sensitivities around Q4 2024 actuals, not management guidance, assigned probabilities, or expected outcomes.

## One-command reproduction

From this directory, run `python3 reproduce.py`. The script loads `analytics-ready-metrics.csv` into an in-memory SQLite database using `schema.sql`, executes `analysis.sql`, prints the bridge, and checks that the residual is within $0.1M.
