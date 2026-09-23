# Data candidate and feasibility review

Reviewed 2026-09-20. This is a planning-level inspection of public primary sources, not a completed extraction or reconciliation.

## Concrete candidate

Build a quarterly panel whose grain is **one metric × one quarter × one publication vintage**. Initial candidate window: Q3 2023 through Q3 2025 from contemporaneous Coinbase shareholder letters filed as SEC exhibits. Featured quarter: Q4 2024. Candidate fields:

- consumer transaction revenue, USD millions;
- consumer trading volume, USD billions;
- total transaction revenue and total trading volume as cross-checks;
- document publication/filing timestamp;
- stated metric definition and vintage;
- original/recast flag;
- revenue-to-volume ratio calculated, never reported as “fee rate.”

## Feasibility findings

**Feasible for a bounded first build:** SEC-filed shareholder letters expose quarter tables with consumer transaction revenue and consumer trading volume. The Q4 2024 filing reports Q4 2023 through Q4 2024 revenue rows, while Q3 2024 reports five-quarter trading-volume tables. The Q3 2025 letter continues the consumer series.

**Material comparability risk:** Coinbase's 2025 10-K says that in Q4 2025 Trading Volume was redefined to include half the value of certain off-platform-routed spot trades and prior periods were recast. Original and recast values must not be silently mixed. The same filing and later 2026 disclosure show the operating metric continues to evolve.

**Interpretation risk:** the Q2 2024 shareholder letter explicitly says consumer transaction revenue outperformed trading volume partly because some revenue was not directly associated with reported spot trading volume. Therefore `consumer revenue / consumer volume` is an effective yield proxy, not a pure price, fee rate, or causal measure.

**Sample limitation:** a 2023–2025 quarterly panel is small. Four holdouts may be possible, but only after checking every publication and definition. It cannot support broad claims of predictive superiority.

## Acquisition procedure for the future build

1. Download only SEC-hosted filing exhibits or Coinbase Investor Relations documents that can be tied to an SEC filing.
2. Save the original file, retrieval timestamp, accession number, SHA-256, and source URL.
3. Enter values once into `reported_metric_observation`; a second pass checks units, signs, and table headings.
4. Record the exact publication timestamp. A forecast run joins only observations whose `published_at <= information_cutoff`.
5. Preserve original and recast observations as separate rows. Never overwrite.
6. Reconcile overlapping five-quarter tables; differences create a blocking exception until explained.

## Go/no-go gate

Proceed with forecasting only if there are at least 8 comparable training observations before the first holdout and at least 4 chronological holdouts under one definition family. Otherwise use Design B, the descriptive bridge. This threshold is a project rule, not a statistical guarantee.

## Source limitations

The official Coinbase careers page previously triggered browser admin-policy verification. This plan does not bypass, proxy, or infer around that restriction. The supplied posting extract remains historical role evidence; current availability and full eligibility are unverified.

