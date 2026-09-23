# Adversarial quality review

## Strongest objections

1. **The model may be tautological.** Revenue divided by volume creates the yield later used to explain revenue. Response: the forecast must use lagged yield and separately forecast volume; realized values appear only in the post-close bridge.
2. **Public consumer volume is incomplete.** Disclosures state some consumer revenue is not directly tied to reported spot volume. Response: call the ratio effective yield, retain a residual when needed, and frame the decision as “investigate mix,” not “change price.”
3. **Too few quarters.** Four holdouts cannot establish durable superiority. Response: publish all cases, use simple baselines, avoid significance claims, and treat failure analysis as a valid outcome.
4. **Definition recasts create leakage.** A later filing can rewrite historical volume. Response: store observations by vintage, score within one definition family, and quarantine Q4 2025 boundary data from the core.
5. **The featured quarter may be cherry-picked.** Q4 2024 is visually dramatic. Response: freeze the featured-quarter selection rationale before viewing model rankings and publish the full holdout table.
6. **A finance reviewer may prefer Excel to architecture.** Response: make Excel the inspectable interface and keep SQLite/SQL as reproducibility support, not the demo centerpiece.
7. **The plan may be too large for a second-priority project.** Response: Milestone 1 is a narrow feasibility packet; stop before workbook polish if the evidence fails.

## Likely failure modes

- publication date mistaken for period end;
- annual totals mixed with quarterly observations;
- millions/billions conversion error;
- original and recast volumes silently combined;
- holdouts altered after inspecting errors;
- realized volume used in an ex-ante forecast;
- interaction effect hidden by bridge ordering;
- a generated memo overstates “pricing” or “management control”;
- dashboard polish precedes source reconciliation.

## Required scope cuts

Cut the multi-line dashboard, macro regression, custom web UI, and x402 case now. If time falls below 20 hours, omit the dashboard entirely. If data comparability fails, switch to Design B. If the descriptive pairing also fails, publish a short “why public data cannot support this bridge” research note and stop.

## Quality verdict

The selected design is professionally defensible **as a plan** because its claims shrink when evidence weakens. It is not yet a validated project. The largest unresolved technical risk is original-vintage quarter coverage; the largest user-specific risk is unknown skill/time capacity.

