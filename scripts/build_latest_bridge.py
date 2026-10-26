#!/usr/bin/env python3
"""Bridge the newest quarter-over-quarter change inside one definition family.

Reads the post-Q4-2025 analytics-ready file, takes the last two consecutive
quarters, and writes the three factor-order allocations (volume first, yield
first, symmetric) to outputs/final-package/latest-bridge.csv. Descriptive only.
"""

import csv
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from strategic_finance.core import (  # noqa: E402
    actual_pair,
    descriptive_bridge,
    ingest_csv,
    symmetric_attribution,
)

SOURCE = ROOT / "data" / "processed" / "analytics-ready-metric-observations-post-2025q4.csv"
TARGET = ROOT / "outputs" / "final-package" / "latest-bridge.csv"
FIELDS = [
    "from_period", "to_period", "definition_family", "method", "from_revenue_mm",
    "to_revenue_mm", "from_volume_bn", "to_volume_bn", "revenue_change_mm",
    "volume_effect_mm", "yield_effect_mm", "residual_mm",
]


def fmt(value, places: int = 3) -> str:
    text = f"{value:.{places}f}"
    return text[1:] if text.startswith("-") and float(text) == 0 else text


def main() -> int:
    connection = sqlite3.connect(":memory:")
    connection.executescript((ROOT / "sql" / "schema.sql").read_text(encoding="utf-8"))
    ingest_csv(connection, SOURCE)
    (family,) = connection.execute("SELECT DISTINCT definition_family FROM reported_metric_observation").fetchone()
    to_period, from_period = [row[0] for row in connection.execute(
        "SELECT DISTINCT period_end FROM reported_metric_observation ORDER BY period_end DESC LIMIT 2")]
    cutoff = connection.execute("SELECT MAX(published_at) FROM reported_metric_observation").fetchone()[0]
    fixed = descriptive_bridge(connection, from_period, to_period, cutoff, family)
    r0, v0 = actual_pair(connection, from_period, family, cutoff)
    r1, v1 = actual_pair(connection, to_period, family, cutoff)
    sym = symmetric_attribution(r0, r1, v0, v1)
    base = {
        "from_period": from_period, "to_period": to_period, "definition_family": family,
        "from_revenue_mm": f"{r0:.3f}", "to_revenue_mm": f"{r1:.3f}",
        "from_volume_bn": f"{v0 / 1000:.1f}", "to_volume_bn": f"{v1 / 1000:.1f}",
        "revenue_change_mm": f"{r1 - r0:.3f}",
    }
    rows = [
        ("Volume first", fixed.volume_effect, fixed.yield_effect, fixed.residual),
        ("Yield first", sym.yield_first_volume, sym.yield_first_yield,
         (r1 - r0) - sym.yield_first_volume - sym.yield_first_yield),
        ("Symmetric Shapley", sym.symmetric_volume, sym.symmetric_yield, sym.residual),
    ]
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    with TARGET.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        for method, volume, yld, residual in rows:
            writer.writerow({**base, "method": method, "volume_effect_mm": fmt(volume),
                             "yield_effect_mm": fmt(yld), "residual_mm": fmt(residual)})
    print(f"wrote {TARGET} ({from_period} -> {to_period}, {family})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
