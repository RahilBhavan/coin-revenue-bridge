# Coinbase consumer revenue bridge, Q3 to Q4 2024

[![ci](https://github.com/RahilBhavan/coinbase-strategic-finance/actions/workflows/ci.yml/badge.svg)](https://github.com/RahilBhavan/coinbase-strategic-finance/actions/workflows/ci.yml)
[![license: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
**Live case study: https://rahilbhavan.github.io/coinbase-strategic-finance/**

A source-backed bridge that splits Coinbase's Q3 to Q4 2024 consumer transaction revenue change into volume and effective-yield effects, built only from public SEC filings.

## The answer

Consumer transaction revenue rose **$863.8M**, from $483.3M in Q3 2024 to $1,347.1M in Q4 2024, while consumer spot volume rose from $34B to $94B. Volume drove almost all of it. The split depends on factor order, so the analysis shows all three valid views:

| Bridge method | Volume effect | Effective-yield effect | Total |
|---|---:|---:|---:|
| Volume first | $852.9M | $10.9M | $863.8M |
| Yield first | $859.9M | $3.9M | $863.8M |
| Symmetric Shapley | $856.4M | $7.4M | $863.8M |

Each view reconciles to the reported change with a $0.0M rounded residual. Effective yield is consumer revenue divided by consumer spot volume. It is a proxy, not Coinbase's fee rate.

Planning sensitivities around the Q4 2024 actuals:

| Case | Volume change | Yield change | Implied revenue |
|---|---:|---:|---:|
| Downside | -20% | -10 bps | $1,002.5M |
| Reference (Q4 2024 actual) | 0% | 0 bps | $1,347.1M |
| Upside | +20% | +10 bps | $1,729.3M |

These are mechanical sensitivities, not guidance, probabilities, or forecasts.

## Why there is no forecast

The design set a gate before looking at results: at least twelve comparable quarters (eight to train, four to test). The public filings support nine under one definition. Coinbase reclassified consumer revenue in Q1 2024 and later redefined trading volume, so a longer series would mix incompatible numbers. The project reports the bridge and publishes no forecast.

## What's in it

- [Live case study](https://rahilbhavan.github.io/coinbase-strategic-finance/), also in [`dist/`](dist/index.html)
- [Two-page decision memo (PDF)](outputs/final-package/decision-memo.pdf)
- [Seven-sheet workbook (XLSX)](outputs/final-package/revenue-analysis.xlsx), formula-driven
- [Reviewer packet (PDF)](outputs/final-package/reviewer-packet.pdf), the strongest objections and how to test them
- [Executive package (ZIP)](outputs/coinbase-strategic-finance-executive-package.zip): memo, workbook, reviewer packet, review protocol
- [Validation report](outputs/final-package/validation-report.md) and [machine-readable evidence](outputs/final-package/validation-evidence.json)

## How it's built

- `data/raw/`: 13 frozen source documents, each with a SHA-256 hash in `artifacts/source-register.csv`.
- `data/processed/`: reviewed metric observations, one row per metric, quarter, and publication vintage. Original and recast values stay as separate rows.
- `src/strategic_finance/` and `sql/`: a Python and SQLite core that enforces information cutoffs and definition families and computes the bridges with decimal arithmetic.
- `scripts/`: builders for the workbook, PDFs, and site, plus the evidence validator.
- `outputs/final-package/`: the reviewer package, with a standalone `reproduce.py` that recomputes the bridge from package-local files.

## Run it

Python 3.9 or later, standard library only:

```sh
python3 -m unittest discover -s tests
python3 outputs/final-package/reproduce.py
python3 scripts/prepare_descriptive_reporting.py --input data/processed/analytics-ready-metric-observations.csv --output-dir work/real-reporting-inputs --from-period 2024-09-30 --to-period 2024-12-31
python3 scripts/build_enhanced_analysis.py
python3 scripts/validate_final_evidence.py
```

`validate_final_evidence.py` exits 1 if any check fails. Without the two prep steps it skips the checks that need their outputs and prints the command to run.

Optional: rebuild and check the workbook. These two steps need Node.js 20 or later and `@oai/artifact-tool`, which comes from a private Codex runtime and is not in this repository. The checked-in workbook stays inspectable without them.

```sh
node scripts/build_descriptive_reporting.mjs --metrics work/real-reporting-inputs/processed_metrics.csv --bridge work/real-reporting-inputs/descriptive_bridge.csv --enhanced-dir work/enhanced-analysis --output-dir outputs/descriptive-bridge --label "DESCRIPTIVE / NOT A FORECAST"
node scripts/validate_descriptive_reporting.mjs --output-dir outputs/descriptive-bridge
```

## Sources

`data/raw/` holds 13 public documents: ten Coinbase shareholder letters (Q3 2023 to Q4 2025) filed as SEC 8-K exhibits, the 2025 Form 10-K, the Q2 2026 earnings deck, and the SEC submissions index for Coinbase Global, Inc. It also keeps the EDGAR filing index page for nine of the letters. All come from SEC EDGAR, and `artifacts/source-register.csv` lists the URL, accession number, and hash for each registered document. They are Coinbase's documents, reproduced here for verification. The MIT license covers this project's code and analysis, not these third-party filings.

## Scope and limits

- Independent analysis of public filings. Not affiliated with or endorsed by Coinbase, and uses no internal Coinbase data.
- Descriptive only: the bridge explains a reported change. It makes no causal claim, forecast, or investment recommendation.
- Consumer spot volume excludes derivatives, and some consumer revenue does not tie to spot volume, so effective yield is a proxy.
- No external practitioner has reviewed the work yet. The [review protocol](outputs/public-case-study/practitioner-review.md) states this.

## Project documents

- [Project brief](01-brief/project-brief.md) and [open decisions](01-brief/open-decisions.md)
- [Data feasibility](02-research/data-feasibility.md), [feasibility verdict](02-research/feasibility-verdict.md), [source register](02-research/source-register.md)
- [Design options](03-design/design-options.md) and [architecture](03-design/architecture.md)
- [Deliverables](04-deliverables/deliverables.md), [validation plan](05-validation/validation-plan.md), [adversarial review](05-validation/adversarial-review.md)
- [Artifact manifest](artifacts/manifest.md), [decision log](decisions.tsv), [release readiness](RELEASE-READINESS.md), [AI contribution record](outputs/final-package/ai-contribution.md)
