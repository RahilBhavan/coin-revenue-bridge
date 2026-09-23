# Changelog

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
