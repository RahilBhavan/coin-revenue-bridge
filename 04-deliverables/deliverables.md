# Deliverables and acceptance criteria

Updated 2026-09-20 after the evidence gate produced a **PIVOT — descriptive bridge** verdict. The reviewer-facing package is in `outputs/final-package/`. Forecast-specific outputs are not relabeled as completed; they are superseded where the public evidence did not support them.

| ID | Final artifact | Purpose | Status and evidence |
|---|---|---|---|
| D-01 | `outputs/final-package/decision-memo.pdf` | Two-page FP&A decision memo | **Complete.** Decision, evidence cutoff, reported change, bridge, limits, strongest objection, next investigation, and linked primary sources. |
| D-02 | `outputs/final-package/revenue-analysis.xlsx` | Inspectable reviewer model | **Complete.** Seven sheets, visible formulas, editable planning sensitivities, three bridge attribution methods, nine-quarter native chart, later-definition crosswalk, source provenance, and definition appendix; validator passed. |
| D-03 | `outputs/final-package/reported-metrics.csv` | Frozen long-form dataset | **Complete.** Sources, publication dates, units, definitions, original/recast status, and reviewed evidence locators. |
| D-04 | `outputs/final-package/analysis.sql` | Reproducible transformation | **Complete for the descriptive pivot.** Fixed-order Q3-to-Q4 2024 decomposition from the normalized SQLite table. |
| D-05 | `outputs/final-package/descriptive-bridge.csv` | Honest analytical result | **Superseded after PIVOT.** No real forecast results, holdouts, MAE, bias, or WAPE are claimed. The descriptive bridge is published instead. |
| D-06 | `outputs/final-package/source-register.csv` | Row-level provenance | **Complete.** Thirteen registered sources with SEC accessions, URLs, timestamps, package-local frozen copies, and hashes; all source resolutions passed. |
| D-07 | `outputs/final-package/validation-report.md` | Check evidence | **Complete.** V-01 through V-16 mapped to executed evidence, `PASS`, or honest forecast-only `NOT RUN` status. |
| D-08 | `outputs/final-package/demo.webm` and `demo.html` | Three-minute story | **Complete in verified WebM/HTML formats.** Eight captioned screens, exactly 180 seconds, no unsupported forecast or causal language. MP4 was unavailable in the local encoder stack. |
| D-09 | `outputs/final-package/reviewer-packet.pdf` | Fast critique packet | **Complete.** Two-page challenge packet with method, sources, objections, and reviewer disposition. |
| D-10 | `outputs/final-package/ai-contribution.md` | Ownership record | **Complete.** Tool contribution, unsupported claims, human-review boundary, and reproducibility limit. |
| D-11 | `outputs/public-case-study/index.html` | Public-ready case-study page | **Complete locally.** Self-contained responsive page with downloadable memo, workbook, reviewer packet, and 30-second social cut. Not externally published. |
| D-12 | `outputs/executive-package/` | Compact review set | **Complete.** Five-file executive package plus ZIP, separated from the full audit package. |
| D-13 | `outputs/public-case-study/practitioner-review.md` | External-review protocol | **Complete as a workflow.** Real external human review remains explicitly not obtained. |

## Readiness gate

The package is **ready for practitioner review**, not externally endorsed. Required pivot artifacts exist, critical descriptive checks pass, limitations are prominent, and the captioned demo explains the decision without a script. External feedback has not occurred and is not implied.
