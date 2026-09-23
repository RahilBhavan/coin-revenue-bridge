# Coinbase Strategic Finance reviewer packet

**SAMPLE / NOT FOR SHARING**  
**Featured period:** 2024-12-31  
**Information cutoff:** 2024-11-15

## Review in two minutes

| Item | Result |
|---|---:|
| Driver forecast | $1360.0m |
| Prior-quarter baseline | $1180.0m |
| Actual revenue | $1400.0m |
| Driver forecast variance | $40.0m |
| Volume effect | $34.9m |
| Effective-yield effect | $5.1m |
| Bridge residual | $0.0m |

## Method

1. Forecast information is limited to records available on or before the stated cutoff.
2. The workbook compares prior-quarter, prior-year, and volume-times-yield models.
3. Holdout errors remain visible for every eligible model and period.
4. The bridge uses a fixed volume-then-yield order and exposes any residual.

## Evidence labels

- **Reported:** source observations supplied in `processed_metrics.csv`.
- **Calculated:** effective yield, errors, aggregate metrics, and bridge effects.
- **Assumed:** forecast volume and forecast effective yield supplied by the analytical pipeline.

## Definition and limitation note

All rows in this package use definition family `synthetic_v1`.
All values are synthetic fixtures and must not be cited as Coinbase results.

## Critique question

What additional evidence would you require before changing the effective-yield assumption?

