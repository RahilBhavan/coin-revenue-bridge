#!/usr/bin/env python3
"""Prepare the SEC-derived descriptive workbook inputs without forecasting."""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from decimal import Decimal
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--from-period", required=True)
    parser.add_argument("--to-period", required=True)
    args = parser.parse_args()

    with args.input.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    by_period: dict[str, dict[str, dict[str, str]]] = defaultdict(dict)
    for row in rows:
        if row.get("analysis_use") != "descriptive_only":
            raise ValueError("SEC-derived reporting input must be descriptive_only")
        by_period[row["period_end"]][row["metric_name"]] = row

    required = {"consumer_transaction_revenue", "consumer_trading_volume"}
    if any(set(metrics) != required for metrics in by_period.values()):
        raise ValueError("every period must have exactly one revenue and volume row")
    for period in (args.from_period, args.to_period):
        if period not in by_period:
            raise ValueError(f"missing requested period: {period}")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    metrics_path = args.output_dir / "processed_metrics.csv"
    with metrics_path.open("w", newline="", encoding="utf-8") as handle:
        fields = [
            "period_end", "consumer_transaction_revenue_mm",
            "consumer_trading_volume_bn", "published_at", "definition_family",
            "evidence_label", "source_reference",
        ]
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for period in sorted(by_period):
            revenue = by_period[period]["consumer_transaction_revenue"]
            volume = by_period[period]["consumer_trading_volume"]
            if revenue["currency"] != "USD" or revenue["scale"] != "millions":
                raise ValueError(f"unexpected revenue unit for {period}")
            if volume["currency"] != "USD" or volume["scale"] != "billions":
                raise ValueError(f"unexpected volume unit for {period}")
            if revenue["definition_family"] != volume["definition_family"]:
                raise ValueError(f"definition-family mismatch for {period}")
            writer.writerow({
                "period_end": period,
                "consumer_transaction_revenue_mm": revenue["value_decimal"],
                "consumer_trading_volume_bn": volume["value_decimal"],
                "published_at": max(revenue["published_at"], volume["published_at"]),
                "definition_family": revenue["definition_family"],
                "evidence_label": "reported/recast public filing values; descriptive only",
                "source_reference": f"{revenue['source_id']}|{volume['source_id']}",
            })

    from_rows = by_period[args.from_period]
    to_rows = by_period[args.to_period]
    from_revenue = Decimal(from_rows["consumer_transaction_revenue"]["value_decimal"])
    to_revenue = Decimal(to_rows["consumer_transaction_revenue"]["value_decimal"])
    from_volume = Decimal(from_rows["consumer_trading_volume"]["value_decimal"])
    to_volume = Decimal(to_rows["consumer_trading_volume"]["value_decimal"])
    family = from_rows["consumer_transaction_revenue"]["definition_family"]
    if family != to_rows["consumer_transaction_revenue"]["definition_family"]:
        raise ValueError("requested bridge crosses definition families")

    bridge_path = args.output_dir / "descriptive_bridge.csv"
    with bridge_path.open("w", newline="", encoding="utf-8") as handle:
        fields = [
            "comparison_id", "from_period", "to_period", "from_revenue_mm",
            "to_revenue_mm", "from_volume_bn", "to_volume_bn", "from_yield_pct",
            "to_yield_pct", "definition_family", "evidence_label", "source_reference",
        ]
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerow({
            "comparison_id": f"{args.from_period}_to_{args.to_period}",
            "from_period": args.from_period,
            "to_period": args.to_period,
            "from_revenue_mm": str(from_revenue),
            "to_revenue_mm": str(to_revenue),
            "from_volume_bn": str(from_volume),
            "to_volume_bn": str(to_volume),
            "from_yield_pct": str(from_revenue / from_volume / Decimal(10)),
            "to_yield_pct": str(to_revenue / to_volume / Decimal(10)),
            "definition_family": family,
            "evidence_label": "descriptive calculation from reported/recast public filing values",
            "source_reference": "source-register.csv",
        })
    print(metrics_path)
    print(bridge_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
