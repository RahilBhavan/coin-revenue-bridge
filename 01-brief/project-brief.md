# Project brief

## Decision and audience

Primary audience: an FP&A practitioner or finance reviewer with three to five minutes. The artifact must answer a planning decision, not showcase a dashboard.

**Decision:** after comparing an ex-ante forecast with reported actuals, should the next forecast retain its volume-growth assumption, revise its effective-yield assumption, or request more evidence about product/customer mix before changing either?

**Featured case candidate:** forecast Q4 2024 consumer transaction revenue using only information published by the forecast cutoff. The exact cutoff will be set to the last calendar day before the first in-quarter public observation used by the model; if only quarterly filings are used, use 2024-09-30 and no Q4 actuals. A stricter pre-quarter planning cutoff can be chosen during the build and must be applied consistently.

## Why this is the strongest design

- It exercises core strategic-finance work: revenue forecasting, variance analysis, macro/crypto drivers, spreadsheet modeling, SQL/BI, and responsible use of an agentic coding tool.
- It produces a real finance judgment: what assumption to investigate next.
- Public filings expose consumer revenue and volume, but also reveal the exact limitation that makes the exercise interesting: revenue is not solely driven by reported spot volume, and definitions change.
- A simple model and an honest failure analysis are more defensible than complex coefficients fit to a small quarterly sample.

## Hypotheses

1. A lagged, driver-based model using forecast volume and trailing effective revenue per volume is more decision-useful than a naive baseline even if it does not win every error metric.
2. The forecast miss can be exactly decomposed into volume and effective-yield effects under a stated ordering.
3. Definition-vintage controls materially change which quarters may be compared.

These are hypotheses, not findings.

## Scope

Included: one revenue line; original-vintage public filings; roughly 8–12 usable quarters if supported; 4 chronological holdouts if available; two naive baselines; one driver model; exact bridge; compact workbook; reproducible SQL; two-page memo; three-minute demo; reviewer packet.

Excluded: internal forecasts, causal econometrics, machine learning, intraday market data, customer-level analysis, product profitability, resource-allocation dollars, live dashboards, x402, deployment, and outreach.

## Rigor and stop rule

Rigor is high because look-ahead leakage and metric recasts can make a weak model appear strong. If fewer than four comparable holdouts survive the vintage audit, remove claims about comparative predictive performance. Deliver a descriptive case study plus a documented feasibility failure; do not expand to weak third-party data to preserve the original claim.

