# Realistic first build

## Milestone 1 — feasibility packet (8–12 focused hours)

Goal: decide whether Design A survives before building a workbook.

1. Acquire and hash candidate SEC filing exhibits (2–3h).
2. Build the source and definition registry (2h).
3. Hand-enter and double-check consumer revenue/volume observations (2–3h).
4. Run overlap, unit, and vintage checks (1–2h).
5. Freeze candidate holdouts and write a one-page feasibility verdict (1–2h).

Exit: either `GO—forecast`, `PIVOT—descriptive bridge`, or `STOP—insufficient comparable data`, with evidence. This is the strongest first milestone because it retires the project's dominant risk and still yields a useful research artifact.

## Milestone 2 — analytical core (10–14 hours)

- Create SQLite schema and cutoff-safe SQL.
- Implement two baselines and one driver model.
- Freeze all parameters before scoring.
- Produce holdout results and exact bridge.
- Reconcile one quarter by hand.

## Milestone 3 — reviewer package (10–12 hours)

- Build compact Excel workbook from frozen outputs.
- Draft two-page memo and AI contribution record.
- Execute validation matrix and repair or narrow claims.
- Create two-page reviewer packet and record three-minute demo.

Estimated total: **28–38 focused hours**, excluding external feedback. This is a planning estimate.

## Dependencies

Required: browser access to SEC public filings; local SQLite; spreadsheet software that writes `.xlsx`; a scripting language already available locally; PDF export; screen recording. Prefer standard-library or existing-environment tools. Do not add production dependencies. Exact commands belong in implementation after environment inspection.

Optional: charting library already present; external practitioner feedback. Not required: Coinbase account, CDP, API keys, wallet, paid data, live market feed, Base, or x402.

## Execution sequence and checkpoints

Each milestone ends in an inspectable artifact and a go/pivot/stop decision. Do not begin presentation polish before the feasibility gate.

