#!/usr/bin/env python3
"""Build symmetric bridge, planning sensitivities, and definition crosswalk."""

from __future__ import annotations

import csv
from decimal import Decimal
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "work" / "enhanced-analysis"


def write_csv(name: str, fields: list[str], rows: list[dict[str, str]]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / name).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    with (ROOT / "work/real-reporting-inputs/descriptive_bridge.csv").open(newline="", encoding="utf-8") as handle:
        bridge = next(csv.DictReader(handle))
    r0, r1 = Decimal(bridge["from_revenue_mm"]), Decimal(bridge["to_revenue_mm"])
    v0, v1 = Decimal(bridge["from_volume_bn"]), Decimal(bridge["to_volume_bn"])
    y0 = r0 / v0 / Decimal(1000)
    y1 = r1 / v1 / Decimal(1000)
    change = r1 - r0
    volume_first = (v1 - v0) * y0 * Decimal(1000)
    yield_second = v1 * (y1 - y0) * Decimal(1000)
    yield_first = v0 * (y1 - y0) * Decimal(1000)
    volume_second = (v1 - v0) * y1 * Decimal(1000)
    shapley_volume = (volume_first + volume_second) / Decimal(2)
    shapley_yield = (yield_first + yield_second) / Decimal(2)
    bridge_rows = [
        {"method": "Volume first", "volume_effect_mm": f"{volume_first:.6f}", "yield_effect_mm": f"{yield_second:.6f}", "total_change_mm": f"{change:.6f}", "residual_mm": f"{change-volume_first-yield_second:.6f}", "interpretation": "Move volume at starting yield; then yield at ending volume."},
        {"method": "Yield first", "volume_effect_mm": f"{volume_second:.6f}", "yield_effect_mm": f"{yield_first:.6f}", "total_change_mm": f"{change:.6f}", "residual_mm": f"{change-volume_second-yield_first:.6f}", "interpretation": "Move yield at starting volume; then volume at ending yield."},
        {"method": "Symmetric Shapley", "volume_effect_mm": f"{shapley_volume:.6f}", "yield_effect_mm": f"{shapley_yield:.6f}", "total_change_mm": f"{change:.6f}", "residual_mm": f"{change-shapley_volume-shapley_yield:.6f}", "interpretation": "Average both valid orders to split the interaction term symmetrically."},
    ]
    write_csv("bridge-attribution.csv", list(bridge_rows[0]), bridge_rows)

    cases = [
        ("Downside", Decimal("-0.20"), Decimal("-0.0010"), "Investigate activity retention and customer/asset mix."),
        ("Reference", Decimal("0.00"), Decimal("0.0000"), "Reference case equals Q4 2024 actual inputs; it is not a forecast."),
        ("Upside", Decimal("0.20"), Decimal("0.0010"), "Test operating readiness and mix sustainability."),
    ]
    scenario_rows = []
    for name, volume_delta, yield_delta, action in cases:
        volume = v1 * (Decimal(1) + volume_delta)
        effective_yield = y1 + yield_delta
        revenue = volume * effective_yield * Decimal(1000)
        scenario_rows.append({
            "case": name,
            "volume_delta_pct": f"{volume_delta:.4f}",
            "yield_delta_pp": f"{yield_delta:.4f}",
            "volume_bn": f"{volume:.4f}",
            "effective_yield_pct": f"{effective_yield:.8f}",
            "implied_revenue_mm": f"{revenue:.4f}",
            "revenue_delta_mm": f"{revenue-r1:.4f}",
            "decision_prompt": action,
            "claim_boundary": "Illustrative sensitivity; not management guidance or a probability-weighted forecast.",
        })
    write_csv("planning-scenarios.csv", list(scenario_rows[0]), scenario_rows)

    reconciliation_rows = [
        {"period": "2025-Q2", "earlier_reported_volume_bn": "43.0", "later_recast_volume_bn": "41.5", "change_bn": "-1.5", "change_pct": "-0.03488372", "earlier_source_id": "SRC-Q2-2025", "later_source_id": "SRC-Q2-2026-DECK", "definition_note": "Later deck adjusts the series for stablecoin activity; do not splice into the pre-Q4 2025 panel."},
        {"period": "2025-Q3", "earlier_reported_volume_bn": "59.0", "later_recast_volume_bn": "57.4", "change_bn": "-1.6", "change_pct": "-0.02711864", "earlier_source_id": "SRC-Q3-2025", "later_source_id": "SRC-Q2-2026-DECK", "definition_note": "Later deck adjusts the series for stablecoin activity; preserve both vintages."},
        {"period": "2025-Q4", "earlier_reported_volume_bn": "56.0", "later_recast_volume_bn": "53.7", "change_bn": "-2.3", "change_pct": "-0.04107143", "earlier_source_id": "SRC-Q4-2025", "later_source_id": "SRC-Q2-2026-DECK", "definition_note": "Q4 letter used the routed-volume definition; the later deck made a further stablecoin adjustment."},
    ]
    write_csv("definition-reconciliation.csv", list(reconciliation_rows[0]), reconciliation_rows)
    print(f"wrote enhanced analysis files to {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
