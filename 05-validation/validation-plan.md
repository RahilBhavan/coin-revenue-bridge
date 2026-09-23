# Validation plan

No checks below have been run against a built model. They are acceptance contracts.

| ID | Check | Expected result | Severity |
|---|---|---|---|
| V-01 | Every metric row resolves to document, table/section, and hash | 100% | Critical |
| V-02 | Overlapping quarters from successive letters agree within stated rounding | All agree or exception blocks use | Critical |
| V-03 | Cutoff query injects a known post-cutoff row | Row excluded | Critical |
| V-04 | Original and recast definition IDs are joined | Incompatible join fails | Critical |
| V-05 | Featured quarter recomputed by hand | SQL and workbook equal within $0.1m or declared tighter tolerance | Critical |
| V-06 | Bridge sum | Components plus residual equal actual minus forecast within $0.1m | Critical |
| V-07 | Realized target-quarter volume searched in forecast inputs | Zero occurrences | Critical |
| V-08 | Holdout coverage | Every frozen eligible holdout shown for all models | Critical |
| V-09 | Metrics recomputed from result rows | MAE, bias, WAPE match published values | High |
| V-10 | Worsening forecast-volume error under fixed yield | Direction behaves algebraically | High |
| V-11 | Alternate bridge order | Total unchanged; allocation difference disclosed | High |
| V-12 | Zero/blank volume | Validation error, no divide-by-zero proxy | High |
| V-13 | Duplicate observation key | Import rejected or quarantined | High |
| V-14 | Memo numeric claims compared with final tables | 100% match | Critical |
| V-15 | Reproduction from clean local checkout | Artifacts regenerate with documented commands | Critical |
| V-16 | Demo claims audit | No causal, internal-data, or production claims | High |

## Verdict vocabulary

Use only `PASS`, `FAIL`, `NOT RUN`, or `INCONCLUSIVE`. A failed critical check blocks “ready to share.” If a check is inapplicable after a scope cut, record why; do not delete it silently.

