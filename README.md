# Coinbase Strategic Finance case study

Status: **descriptive portfolio package complete; forecast gate not met**  
Planning cutoff: **2026-09-20**  

## Recommendation

Use the package as a **vintage-aware descriptive bridge and planning-sensitivity case study**. The vintage audit found nine comparable quarter pairs, below the predeclared twelve-quarter forecast gate. The final artifact therefore explains the Q3-to-Q4 2024 reported change, shows both ordered bridges and a symmetric Shapley allocation, and provides editable sensitivities without claiming forecast performance.

The Q1 2024 revenue reclassification and later trading-volume changes are preserved as explicit vintages. Q2-Q4 2025 earlier and later volume values are crosswalked, but remain quarantined from the pre-change comparable panel.

## Start here

1. [Public case study](https://coinbase-strategic-finance-case-study.rbhavanzim.chatgpt.site)
2. `outputs/public-case-study/index.html`
3. `outputs/final-package/decision-memo.pdf`
4. `outputs/final-package/revenue-analysis.xlsx`
5. `outputs/final-package/reviewer-packet.pdf`
6. `outputs/coinbase-strategic-finance-executive-package.zip`
7. `outputs/final-package/validation-report.md`
8. [Data feasibility verdict](02-research/feasibility-verdict.md)

## Completion state

The build includes 13 frozen SEC sources, reviewed and normalized CSV data, a Python/SQLite analytical core, 11 automated tests, an exact descriptive bridge, symmetric attribution, editable planning sensitivities, a seven-sheet workbook, two-page PDFs, a deployed public case-study page, and compact executive package. No forecast was fit or scored on the SEC-derived data. External human review remains open.

## Reproduce the current build

The analytical tests and package-local reproduction use Python 3.9+ and the
standard library. The workbook builder additionally uses Node.js 20+ and
`@oai/artifact-tool`; that dependency is supplied by the Codex workspace runtime
and is not vendored in this repository. If it is unavailable, the checked-in
workbook remains inspectable and `outputs/final-package/reproduce.py` still
recomputes the featured bridge using only Python's standard library.

```sh
python3 -m unittest discover -s tests -v
python3 scripts/prepare_descriptive_reporting.py --input data/processed/analytics-ready-metric-observations.csv --output-dir work/real-reporting-inputs --from-period 2024-09-30 --to-period 2024-12-31
python3 scripts/build_enhanced_analysis.py
node scripts/build_descriptive_reporting.mjs --metrics work/real-reporting-inputs/processed_metrics.csv --bridge work/real-reporting-inputs/descriptive_bridge.csv --enhanced-dir work/enhanced-analysis --output-dir outputs/descriptive-bridge --label "DESCRIPTIVE / NOT A FORECAST"
node scripts/validate_descriptive_reporting.mjs --output-dir outputs/descriptive-bridge
python3 scripts/validate_final_evidence.py
python3 outputs/final-package/reproduce.py
```

See `02-research/feasibility-verdict.md` for the PIVOT decision and `outputs/descriptive-bridge/manifest.json` for output hashes and units.

## Boundaries

- x402 is a separate, deferred business case and is not a prerequisite.
- No claim of internal Coinbase data, budgets, pricing, causality, production readiness, hiring eligibility, referral, or business endorsement.
- No live services, wallets, transactions, paid APIs, outreach, or application activity beyond the static public case-study deployment.
- Public-source analysis must respect publication dates and definition vintages.

## Remaining release items

- Obtain independent practitioner review; the protocol exists, but no external
  reviewer has approved the claims.
- Recheck the production site after material content changes. Desktop and mobile
  local rendering passed before the first deployment.
- Use the checked-in 30-second H.264 MP4 for the X rollout; verify the final
  platform upload and captions before publishing.
- Treat arbitrary-machine workbook regeneration as unproven because
  `@oai/artifact-tool` comes from the Codex workspace runtime. The analytical
  core and package-local bridge reproduction do not depend on it.
- Reopen forecasting only after a definition-compatible panel meets the
  predeclared twelve-quarter gate or suitable internal data becomes available.

## Planning package map

| Folder | Contents |
|---|---|
| `01-brief` | decision, scope, audience, risks, open choices |
| `02-research` | feasibility review, source register, preserved prior plans |
| `03-design` | three-design comparison, data model, formulas, architecture |
| `04-deliverables` | artifact contract, demo storyboard, reviewer packet |
| `05-validation` | validation matrix and adversarial review |
| `06-execution` | milestone sequence, effort, dependencies, stop rules |
| `artifacts` | placeholder manifest for future built outputs |
