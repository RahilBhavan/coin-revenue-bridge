# Design system: coin-revenue-bridge cards

Rules for the chart cards this repo renders (`scripts/build_no_forecast_card.py`, `scripts/build_revenue_bridge_card.py`). They govern these cards only, not the case study site in `dist/`.

> **Open conflict, not resolved here.** Rahil's shared public system, `rahil-design` 3.3.1, uses charcoal, white and yellow with Anton and IBM Plex Sans, and says social cards have no navy title panels. These cards follow the navy, red, Roboto Slab and Archivo spec from the Grok Bot requests (cr-f1104bec, cr-50cbb41e), as PR #8 did. Until Rahil decides which system governs, every card from this repo is a **review draft: design review pending**.

## Colour

| Role | Value | Use |
|---|---|---|
| Navy | `#0B1F4B` | Base series, text, axis lines |
| Red | `#C8102E` | The single highlighted series, and its label |
| White | `#FFFFFF` | Card background |

Red marks one series per card, the one the title names. Everything else is navy. No other colours, gradients, shadows or gridlines.

## Type

- Titles: Roboto Slab Bold. Landscape 40px, square 54px.
- Everything else: Archivo, 600 for values, labels and the definition line, 400 for the footer.
- Every piece of text is at least **26px on a 1024px-wide card**. The script measures this in the rendered page and fails below 26px.
- Fonts are embedded from `scripts/card-fonts/` (licenses alongside). No other family may render.

## Formats

- Landscape: 1024 x 640.
- Square: 1024 x 1024.
- The no-forecast card predates this rule and is still 1024 x 576 landscape.

## Content

- **Title states the takeaway** with the number in it, for example "Volume drove $856.4M of Coinbase's $863.8M revenue jump". It is not a topic label.
- **Every number carries its unit.** Bar labels read `$483.3M`, `+$856.4M`, `+$7.4M`, `$1,347.1M`.
- **Define the one term the reader may not know**, in one plain line placed above the chart. The revenue bridge card defines "Shapley split".
- **Footer**: one line with the source and the date the data was published. The date comes from the data rows the card draws, not from the day of rendering.
- Bars start at zero. A bar's length is its value, so a very small effect stays small: the $7.4M yield effect is about one pixel tall and the label carries the number.
- Numbers are read from the repo's CSVs and printed to one decimal. A card must not render if its printed parts do not add up to its printed total.

## Alt text

`alt-text.txt` and the card's `aria-label` carry the same words. It names the chart type, every number with its unit, the highlighted series and the term definition. It must match the card, so change both together.

## Verification

Each build script checks the rendered page (minimum text size, one-line definition and footer, units on every label, no overflow or overlap, only the two fonts), checks the PNG dimensions, and writes `manifest.json` with each PNG's SHA-256. Rendering twice gives identical hashes.

Before calling a card finished, also look at it at phone feed size (about 356px wide). At that size 26px text is about 9px, which is below the `rahil-design` 3.3.1 feed floor of 18px, so the definition line and footer fail that floor by design of this spec. Larger text needs a shorter definition or a shorter footer, or a decision to relax this spec.
