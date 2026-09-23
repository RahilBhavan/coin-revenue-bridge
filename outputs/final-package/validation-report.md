# Validation report

**Run date:** 2026-09-20  
**Scope:** public-data descriptive bridge and final-package claims  
**Overall verdict:** **PASS for a descriptive portfolio artifact; NOT RUN for forecast-performance gates.**  
**Required label:** **DESCRIPTIVE / NOT A FORECAST**

The evidence gate changed the deliverable. Only nine comparable paired quarters were available against a predeclared twelve-quarter minimum, so no production forecast was fit or scored. Forecast-only checks remain visible below as `NOT RUN`; they were not silently deleted or converted into passes.

## Requirement matrix

| ID | Status | Evidence |
|---|---|---|
| V-01 | PASS | `python3 scripts/validate_final_evidence.py` recomputed SHA-256 for all 13 registered local sources and resolved all 20 reviewed observation rows to a registered `source_id`; zero mismatches or unresolved IDs. The source register now includes the 2025 10-K, Q4 2025 shareholder letter, and Q2 2026 earnings deck used for the later-definition crosswalk. |
| V-02 | PASS | `scripts/reconcile_overlap_tables.py` parsed the table-based SEC exhibits and reconciled 16 repeated metric-period-definition groups across successive five-quarter tables; every difference was zero. The three older image-layout exhibits are excluded from table parsing, while their original/recast distinction remains preserved in the reviewed dataset and workbook appendix. Evidence: `overlap-reconciliation.csv`. |
| V-03 | PASS | `python3 -m unittest discover -s tests -v`; `test_cutoff_and_lag_only_forecast` and `test_definition_family_and_post_cutoff_rows_fail_closed` passed, including exclusion of post-cutoff data in the synthetic forecast fixture. |
| V-04 | PASS | Same suite; incompatible definition families fail closed. The real descriptive panel uses one explicit paired family, while original/recast revenue definitions remain separate upstream. |
| V-05 | PASS | `python3 scripts/descriptive_bridge.py --database /tmp/coinbase-final-validation.sqlite --input data/processed/analytics-ready-metric-observations.csv --comparison-period 2024-09-30 --target-period 2024-12-31 --information-cutoff 2025-02-13 --definition-family PAIR-REV-POST2024Q1-VOL-SPOT-PRE2025Q4 --format json` returned revenue change 863.8, volume effect 852.8823529, yield effect 10.9176471, and residual effectively zero. Independent Decimal arithmetic in `validate_final_evidence.py` matches. |
| V-06 | PASS | The command above and `node scripts/validate_descriptive_reporting.mjs --output-dir outputs/descriptive-bridge` both passed reconciliation within the workbook’s $0.1M tolerance. This is an actual-to-prior-quarter descriptive bridge, not actual-minus-forecast. |
| V-07 | NOT RUN | No real forecast was built after the feasibility pivot. Realized Q4 volume is intentionally an input to the historical descriptive comparison; it is not presented as an ex-ante forecast input. |
| V-08 | NOT RUN | The real panel failed the ≥12 comparable-quarter gate, so there are no frozen eligible holdouts or model tournament. |
| V-09 | NOT RUN | No real forecast result rows or published MAE/bias/WAPE exist. Formula behavior is covered only by the passing synthetic unit test `test_scores_use_literal_expected_formulas`; that is not portfolio performance evidence. |
| V-10 | NOT RUN | No production volume forecast exists to perturb. The project makes no directional sensitivity claim from the synthetic fixture. |
| V-11 | PASS | `validate_final_evidence.py` recomputed both ordered bridges and the symmetric Shapley allocation. Volume-first is $852.9M/$10.9M, yield-first is $859.9M/$3.9M, and the symmetric split is $856.4M/$7.4M. Every method reconciles to $863.8M. |
| V-12 | PASS | Unit tests `test_missing_and_zero_volume_fail_safely` and `test_analytics_ready_data_allows_only_labeled_descriptive_bridge` passed. Zero or missing volume fails instead of creating a proxy. |
| V-13 | PASS | `validate_final_evidence.py` confirmed 20 unique current observation keys and created a temporary duplicated input; `ingest_csv` rejected it with `AnalysisError`. No production file was changed. |
| V-14 | PASS | `validate_final_evidence.py` matched the memo’s 863.8, 852.9, and 10.9 claims and required label to independently recomputed values. Workbook validator also checked memo/reviewer labels and formulas. |
| V-15 | PASS | A clean isolated copy was assembled from source/data/scripts with a fresh output directory. All 11 tests passed; the reporting inputs and enhanced analyses regenerated; the seven-sheet workbook rebuilt; and the validator passed. This proves clean-workspace reproduction with the declared bundled runtime, not portability to arbitrary machines. |
| V-16 | PASS | Automated string audit found the required descriptive label and explicit non-extrapolation, non-causality, and definition-break language in `demo.html`. Manual review confirmed no internal-data, production, causal, or forecast-performance claim. |

## Executed commands and observed results

```text
python3 scripts/build_captioned_demo.py
→ built outputs/final-package/demo.html (180 seconds)

python3 -m unittest discover -s tests -v
→ 11 tests passed, including symmetric attribution and planning sensitivity checks; exit 0

node scripts/validate_descriptive_reporting.mjs --output-dir outputs/descriptive-bridge
→ PASS: manifest checksums/units, seven worksheets, visible status, reconciliation,
  formula/error scan, native trend chart, symmetric attribution, planning sensitivities,
  later-definition crosswalk, provenance, and memo/reviewer labels; exit 0

python3 scripts/descriptive_bridge.py [arguments shown in V-05]
→ descriptive bridge JSON; 863.8 = 852.8823529 + 10.9176471 + ~0; exit 0

python3 scripts/validate_final_evidence.py
→ source hashes, source resolution, duplicate controls, bridge arithmetic,
  symmetric attribution, planning sensitivities, definition reconciliation,
  memo/demo claims, public case study, and package hashes passed; exit 0

python3 scripts/reconcile_overlap_tables.py
→ 16 repeated metric-period-definition groups reconciled with zero differences; exit 0

Playwright-bundled ffmpeg + frame streaming scripts
→ demo.webm is 180 seconds and social-cut.webm is 30 seconds; both VP8 1280×720
```

The original runtime lacked a system FFmpeg and the Swift/SDK mismatch prevented native MP4 encoding, so the first verified deliverables were VP8 WebM files. On 2026-09-22, system FFmpeg 9.0.2 with `libx264` produced a 30-second, 1280×720, yuv420p H.264 MP4. `ffprobe` confirmed the codec, dimensions, pixel format, duration, and file size.

## Hash evidence

Machine-readable results and final-package SHA-256 values are in `validation-evidence.json`. The authoritative current workbook hash is recorded in `package-manifest.json`; it is recomputed whenever the package is assembled, avoiding a stale duplicated hash in this narrative report.

## Remaining review risks

1. Clean-workspace reproduction passed with the declared bundled runtime; portability to arbitrary machines remains unproven.
2. The effective-yield proxy combines consumer revenue with reported spot volume even though disclosures say some revenue is not directly associated with that volume.
3. Bridge component allocation is path-dependent; the symmetric Shapley view reduces presentation dependence but does not create causal evidence.
4. The Q2-Q4 2025 volume vintages are crosswalked, but they remain incompatible with the earlier panel and should not be silently spliced into it.
5. The practitioner-review protocol is complete, but real external human review has not yet been obtained.
6. The public case-study site is deploy-ready but has not been published, and browser visual preview was blocked by local URL policy; static structure and links were validated locally.
