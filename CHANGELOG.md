# Changelog

## Unreleased

- Froze the Q1 2026 earnings deck and the Q1 and Q2 2026 Forms 10-Q, with a refreshed SEC submissions index. The source register now holds 17 documents and the observation ledger 30 rows.
- Added the post-Q4-2025 volume family (Q2 2025 to Q2 2026, five quarters) as a separate analytics-ready file. Coinbase redefined trading volume in Q4 2025 and again in Q2 2026, and stopped reporting it as a key metric from Q2 2026, so these quarters are not added to the earlier nine.
- `comparable_quarter_count` and `scripts/forecast_gate.py` report the real comparable-quarter count per definition family (9 of 12, gate closed). The refusal message in forecast mode now includes the count.
- `scripts/build_latest_bridge.py` writes the Q1 to Q2 2026 bridge to `outputs/final-package/latest-bridge.csv`; the case study site has a new section for it.
- The validator gains `forecast_gate` and `latest_bridge` checks (17 in total). The suite has 18 tests.
- Not rebuilt: the workbook (its builder is not in this repo), the PDFs (they need a macOS font) and the demo videos. They still cover Q3 to Q4 2024.
- `scripts/build_no_forecast_card.py` renders the no-forecast chart card (landscape 1024x576, square 1024x1024) to `outputs/no-forecast-card/` from `analytics-ready-metrics.csv`, with alt text in `alt-text.txt`. It checks type size, the one-line 28px definition footer, and overflow in the rendered page. Fonts (Roboto Slab, Archivo) are in `scripts/card-fonts/` with their licenses.
- `scripts/build_revenue_bridge_card.py` renders the Q3 to Q4 2024 revenue bridge card (landscape 1024x640, square 1024x1024) to `outputs/revenue-bridge-card/`. Every bar label carries `$M`, a one-line Shapley split definition sits above the chart, and the footer gives source and data date. Numbers are unchanged (483.3 + 856.4 + 7.4 = 1,347.1) and come from `descriptive-bridge.csv` and `bridge-attribution.csv`. `manifest.json` records each PNG's SHA-256. Review draft: design review pending.
- `DESIGN.md` records the card design system and flags its conflict with `rahil-design` 3.3.1.

## v1.1.0 (2026-09-23)

- `validate_final_evidence.py` now exits 1 when any check fails, and skips the checks that need gitignored prep inputs with the command to run first.
- The validator checks that the live page and `dist/` show the headline numbers from the final-package CSVs.
- Site, PDFs, and footers are branded as independent analysis of public filings, with no Coinbase endorsement implied.
- The demo video's opening caption now reads "Independent analysis · Public evidence", and the videos were re-rendered.
- `scrub_workbook_metadata.py` sets the workbook's theme names to Office and its document authorship to the project author.
- The repository is renamed to `coin-revenue-bridge`; links, badges, and the executive package ZIP name follow.
- The site gets link-preview tags, a favicon, and a social card; the README gets a screenshot and related projects.
- `scripts/encode_demo_videos.sh` records the ffmpeg commands for the demo videos.
- PDFs and the executive ZIP use fixed timestamps, so rebuilding leaves the tree unchanged.
- A weekly link check and Dependabot updates for GitHub Actions.
