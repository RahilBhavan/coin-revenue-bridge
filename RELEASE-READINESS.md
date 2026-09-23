# Release readiness

Last validated: **2026-09-23**

## Ready

- 13 unit tests pass.
- The descriptive workbook rebuilds with seven expected sheets and passes its
  formula, unit, provenance, label, sensitivity, and reconciliation checks.
- All 15 final-evidence checks pass, including 13 frozen-source hashes, 20
  source-resolved observations, duplicate rejection, bridge arithmetic,
  definition reconciliation, public-page structure and headline numbers,
  deliverable presence, and human-review disclosure.
- The repository scan found no credential files or common committed-token
  patterns.
- Generated caches, machine-local dependencies, workbook inspection scratch
  files, and regenerable intermediate assets are excluded by `.gitignore`.

## Intentionally incomplete

- Forecast accuracy and model-comparison checks are **NOT RUN** because the
  evidence gate failed and no real forecast was built.
- External practitioner review is pending.
- GitHub Pages publishes `dist/` to
  `https://rahilbhavan.github.io/coinbase-strategic-finance/`.
- A 30-second 1280×720 H.264 MP4 is verified and ready for an upload test.
- Desktop and 390×844 mobile browser rendering passed. The mobile sensitivity
  table scrolls within its container without widening the page; all linked
  controls are present, the workbook image loads with alt text, and the browser
  console has no warnings or errors.
- Workbook regeneration depends on the Codex-provided `@oai/artifact-tool`.
  Package-local bridge reproduction uses only Python's standard library.

## Executed validation commands

```text
python3 -m unittest discover -s tests -v
→ 13 tests passed; exit 0

python3 scripts/prepare_descriptive_reporting.py [...]
python3 scripts/build_enhanced_analysis.py
node scripts/build_descriptive_reporting.mjs [...]
node scripts/validate_descriptive_reporting.mjs --output-dir outputs/descriptive-bridge
→ workbook rebuilt; 12 reporting checks passed; exit 0

python3 scripts/validate_final_evidence.py
→ 15 evidence checks passed; exit 0
```

## Publication rule

GitHub publication does not change the claim boundary. Keep
**DESCRIPTIVE / NOT A FORECAST** visible, retain the AI contribution record,
and do not represent pending human review as complete.
