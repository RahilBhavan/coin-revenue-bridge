#!/usr/bin/env python3
"""Reconcile repeated quarterly consumer metrics across frozen SEC exhibits."""

from __future__ import annotations

import csv
import re
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUTPUT = ROOT / "outputs" / "final-package" / "overlap-reconciliation.csv"
FILES = sorted(RAW.glob("q*-20*-shareholder-letter.html"))
QUARTER = re.compile(r"Q([1-4])[’']?(\d{2})")


def normalize_period(label: object) -> str | None:
    match = QUARTER.search(str(label))
    if not match:
        return None
    quarter, year = int(match.group(1)), 2000 + int(match.group(2))
    month_day = {1: (3, 31), 2: (6, 30), 3: (9, 30), 4: (12, 31)}[quarter]
    return f"{year:04d}-{month_day[0]:02d}-{month_day[1]:02d}"


def rows_as_text(table: pd.DataFrame) -> list[list[str]]:
    return [["" if pd.isna(value) else str(value).strip() for value in row] for row in table.values.tolist()]


def extract(table: pd.DataFrame, header_marker: str, value_marker: str) -> list[tuple[str, Decimal]]:
    rows = rows_as_text(table)
    header_index = next((i for i, row in enumerate(rows) if any(header_marker in cell for cell in row)), None)
    if header_index is None:
        return []
    value_index = next((i for i, row in enumerate(rows[header_index + 1 :], header_index + 1) if any(cell.startswith(value_marker) for cell in row)), None)
    if value_index is None:
        return []
    result = []
    for header, value in zip(rows[header_index], rows[value_index]):
        period = normalize_period(header)
        if period is None:
            continue
        if not value or value in {"-", "—", "nan"}:
            continue
        try:
            result.append((period, Decimal(value.replace(",", ""))))
        except Exception as error:
            raise ValueError(f"non-numeric value {value!r} for {period}") from error
    return result


def revenue_family(path: Path) -> str:
    return "REV-PRE-2024Q1" if path.name in {"q3-2023-shareholder-letter.html", "q4-2023-shareholder-letter.html"} else "REV-POST-2024Q1"


def main() -> int:
    occurrences: dict[tuple[str, str, str], dict[str, Decimal]] = defaultdict(dict)
    skipped = []
    for path in FILES:
        if path.name == "q4-2025-shareholder-letter.html":
            skipped.append(path.name)
            continue
        try:
            tables = pd.read_html(path, flavor="lxml")
        except ValueError:
            skipped.append(path.name)
            continue
        revenue = next((extract(table, "TOTAL REVENUE", "Consumer, net") for table in tables if extract(table, "TOTAL REVENUE", "Consumer, net")), [])
        volume = next((extract(table, "TRADING VOLUME ($B)", "Consumer") for table in tables if extract(table, "TRADING VOLUME ($B)", "Consumer")), [])
        if not revenue or not volume:
            raise ValueError(f"consumer revenue/volume table missing in {path.name}")
        for period, value in revenue:
            key = ("consumer_transaction_revenue", period, revenue_family(path))
            existing = occurrences[key].get(path.name)
            if existing is not None and existing != value:
                raise ValueError(f"conflicting repeated value inside {path.name}: {key}")
            occurrences[key][path.name] = value
        for period, value in volume:
            key = ("consumer_trading_volume", period, "VOL-SPOT-MATCHED-PRE-2025Q4")
            existing = occurrences[key].get(path.name)
            if existing is not None and existing != value:
                raise ValueError(f"conflicting repeated value inside {path.name}: {key}")
            occurrences[key][path.name] = value

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    failed = []
    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        fields = ["metric_name", "period_end", "definition_family", "occurrence_count", "minimum", "maximum", "difference", "sources", "status"]
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for (metric, period, family), source_values in sorted(occurrences.items()):
            values = list(source_values.items())
            if len(values) < 2:
                continue
            numbers = [value for _, value in values]
            difference = max(numbers) - min(numbers)
            status = "PASS" if abs(difference) <= Decimal("0.1") else "FAIL"
            if status == "FAIL":
                failed.append((metric, period, family, difference))
            writer.writerow({
                "metric_name": metric,
                "period_end": period,
                "definition_family": family,
                "occurrence_count": len(values),
                "minimum": min(numbers),
                "maximum": max(numbers),
                "difference": difference,
                "sources": "|".join(source for source, _ in values),
                "status": status,
            })
    if len(FILES) - len(skipped) < 5:
        raise SystemExit(f"too few table-based exhibits parsed; skipped {skipped}")
    if failed:
        raise SystemExit(f"overlap reconciliation failed: {failed}")
    print(f"PASS: {len(occurrences)} metric-period-definition groups inspected; repeated groups written to {OUTPUT}; separately handled or image-layout exhibits excluded: {','.join(skipped)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
