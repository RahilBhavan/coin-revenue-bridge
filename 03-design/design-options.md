# Three designs compared

Scores are planning judgments from 1 (weak) to 5 (strong), not validated results. Weights: strategic-finance fit 30%, decision usefulness 25%, data defensibility 20%, build feasibility 15%, distinctiveness 10%.

| Design | Fit | Decision | Data | Build | Distinctive | Weighted | Verdict |
|---|---:|---:|---:|---:|---:|---:|---|
| A. Vintage-aware forecast + exact bridge | 5 | 5 | 4 | 4 | 5 | 4.65 | **Select, conditional on vintage audit** |
| B. Descriptive revenue bridge only | 4 | 4 | 5 | 5 | 3 | 4.25 | Evidence fallback |
| C. Multi-line macro dashboard | 5 | 3 | 2 | 2 | 3 | 3.25 | Reject for first build |

## A. Vintage-aware forecast and bridge

Compare two naive baselines with one driver forecast, then explain a featured miss. It best exercises forecasting, variance analysis, Excel, SQL, and judgment. The design risks leakage, overclaiming, and too few observations; strict vintage gates contain those risks.

## B. Descriptive bridge

Begin after actuals are published. Explain quarter-over-quarter consumer transaction revenue change using reported consumer volume and a calculated effective-yield proxy. It is highly reproducible and survives a short dataset, but demonstrates less ex-ante planning skill. Use it if four clean holdouts are unavailable.

## C. Multi-line macro dashboard

Forecast consumer, institutional, stablecoin, and subscription revenue from crypto prices, volatility, rates, and market capitalization. It looks broad but creates mismatched definitions, lag/vintage problems, collinearity, and a false sense of statistical depth. It also shifts attention from a decision to visualization. Defer until one line is defensible.

## Why x402 is absent

An x402 API pricing case is a separate product-economics decision. Combining it with historical forecasting produces two audiences, two evidence systems, and an incoherent demo. It can be designed later if practitioner feedback specifically asks for payments economics.

