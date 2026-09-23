# Three-minute demo script

**Format:** captioned 1280×720 WebM video and self-contained HTML, 3:00, no narration required  
**Run:** play `demo.webm`, or open `demo.html` for an interactive version. The HTML auto-advances; Space pauses; arrow keys move between frames.  
**Status:** **DESCRIPTIVE / NOT A FORECAST**

The original build used a Playwright-bundled FFmpeg binary to encode the eight reviewed caption frames as a 180-second VP8 WebM after the native Swift encoder failed. A system FFmpeg with H.264 support later became available and produced a verified 30-second, 1280×720 H.264 MP4 social cut. The WebM and interactive HTML remain the full three-minute walkthrough. All media uses reviewed local inputs and has no network dependency.

## Storyboard and optional talk track

| Time | Screen | Optional talk track |
|---:|---|---|
| 0:00–0:15 | Explain the change | “This began as a forecasting project. The evidence gate forced a better choice: explain a reported change without pretending we had enough history to validate a forecast.” |
| 0:15–0:38 | Evidence before output | “Thirteen SEC sources were frozen and hashed. But the predeclared forecast gate required twelve comparable quarters: eight for training and four holdouts. Only nine exist in the scoped panel.” |
| 0:38–1:05 | Definition control | “There is a revenue-definition break at Q1 2024, a routed-volume change in Q4 2025, and a later stablecoin adjustment. Original and recast observations are kept as distinct vintages; Q2–Q4 2025 volume changes are crosswalked and quarantined.” |
| 1:05–1:32 | Historical trend | “The comparable series is volatile, peaking in Q4 2024. This is a historical view, not an extrapolation.” |
| 1:32–2:05 | Q3→Q4 2024 bridge | “Consumer transaction revenue increased $863.8 million. Under the disclosed volume-first identity, $852.9 million is associated with volume and $10.9 million with the effective-yield proxy. The residual rounds to zero.” |
| 2:05–2:28 | Planning layer | “The editable downside, reference, and upside cases test volume and yield assumptions without assigning probabilities. They are sensitivities, not guidance or expected outcomes.” |
| 2:28–2:49 | Strongest objection | “Bridge allocation is order-dependent. The workbook shows volume-first, yield-first, and a symmetric Shapley split. Every method preserves the total; none proves causality.” |
| 2:49–3:00 | Verdict | “The result is a small, inspectable finance artifact whose claims are bounded by the evidence. It is descriptive, not a forecast.” |

## Live-demo checklist

1. Start in a browser at normal zoom and full screen.
2. Let the 180-second sequence autoplay or use arrow keys to shorten discussion.
3. If challenged on a number, open `revenue-analysis.xlsx` and show the `Bridge Calculation` sheet.
4. If challenged on provenance, open `source-register.csv` and match the quarter to its SEC accession and SHA-256; the frozen filings are in `raw-sources/`.
5. End on the visible **DESCRIPTIVE / NOT A FORECAST** label.

## Claims intentionally excluded

- no forecast accuracy or model-superiority claim;
- no causal claim;
- no claim that effective yield is Coinbase’s fee rate;
- no claim that public volume covers every revenue-generating activity;
- no claim about current openings, hiring outcomes, or production use.
