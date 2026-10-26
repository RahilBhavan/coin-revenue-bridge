#!/usr/bin/env python3
"""Report the pre-set forecast gate from the analytics-ready data files.

Counts the longest run of consecutive quarters that have both metrics under a
single definition family, for every family in data/processed. Quarters from
different families are never added together. Prints JSON and, with
--write, writes outputs/final-package/forecast-gate.csv. Exit code 0 when the
report is printed; --require-open exits 1 while the gate is closed.
"""

import argparse
import csv
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from strategic_finance.core import (  # noqa: E402
    comparable_quarter_count,
    forecast_gate,
    ingest_csv,
)


def gate_report(root: Path = ROOT) -> dict:
    counts, spans = {}, {}
    for path in sorted((root / "data" / "processed").glob("analytics-ready-metric-observations*.csv")):
        connection = sqlite3.connect(":memory:")
        connection.executescript((root / "sql" / "schema.sql").read_text(encoding="utf-8"))
        ingest_csv(connection, path)
        for (family,) in connection.execute(
            "SELECT DISTINCT definition_family FROM reported_metric_observation"
        ).fetchall():
            counts[family] = comparable_quarter_count(connection, family)
            first, last = connection.execute(
                "SELECT MIN(period_end), MAX(period_end) FROM reported_metric_observation "
                "WHERE definition_family = ?", (family,),
            ).fetchone()
            spans[family] = (first, last, path.name)
        connection.close()
    report = forecast_gate(counts)
    report["spans"] = {family: {"first": a, "last": b, "file": f} for family, (a, b, f) in spans.items()}
    return report


def all_periods(root: Path = ROOT) -> int:
    periods = set()
    for path in sorted((root / "data" / "processed").glob("analytics-ready-metric-observations*.csv")):
        with path.open(newline="", encoding="utf-8") as handle:
            periods.update(row["period_end"] for row in csv.DictReader(handle))
    return len(periods)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="write outputs/final-package/forecast-gate.csv")
    parser.add_argument("--require-open", action="store_true")
    args = parser.parse_args()
    report = gate_report()
    report["quarters_with_any_data"] = all_periods()
    report["note"] = (
        "quarters_with_any_data spans incompatible volume definitions and is not a "
        "comparable count; the gate uses comparable_quarters only."
    )
    print(json.dumps(report, indent=2))
    if args.write:
        target = ROOT / "outputs" / "final-package" / "forecast-gate.csv"
        with target.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle, lineterminator="\n")
            writer.writerow(["definition_family", "first_period_end", "last_period_end", "comparable_quarters", "required_quarters", "gate_open"])
            for family, count in sorted(report["by_family"].items(), key=lambda item: -item[1]):
                span = report["spans"][family]
                writer.writerow([family, span["first"], span["last"], count, report["required_quarters"], str(count >= report["required_quarters"]).lower()])
    if args.require_open and not report["gate_open"]:
        print(f"gate closed: {report['comparable_quarters']} of {report['required_quarters']} comparable quarters", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
