#!/usr/bin/env python3
"""Reproduce the published descriptive bridge from package-local files."""

from __future__ import annotations

import csv
import sqlite3
from decimal import Decimal
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def main() -> int:
    connection = sqlite3.connect(":memory:")
    connection.executescript((ROOT / "schema.sql").read_text(encoding="utf-8"))
    with (ROOT / "analytics-ready-metrics.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    columns = list(rows[0])
    placeholders = ", ".join("?" for _ in columns)
    names = ", ".join(columns)
    connection.executemany(
        f"INSERT INTO reported_metric_observation ({names}) VALUES ({placeholders})",
        [[row[name] for name in columns] for row in rows],
    )
    result = connection.execute((ROOT / "analysis.sql").read_text(encoding="utf-8")).fetchone()
    labels = ("revenue_change_mm", "volume_effect_mm", "effective_yield_effect_mm", "residual_mm")
    values = dict(zip(labels, (Decimal(str(value)) for value in result)))
    for label in labels:
        print(f"{label}={values[label]:.1f}")
    if abs(values["residual_mm"]) > Decimal("0.1"):
        raise SystemExit("FAIL: residual exceeds $0.1M")
    print("PASS: bridge reconciles within $0.1M")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
