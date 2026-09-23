#!/usr/bin/env python3
"""Emit a descriptive reported-quarter bridge as JSON or one-row CSV."""

import argparse
import csv
import json
import sqlite3
import sys
from dataclasses import asdict
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from strategic_finance.core import AnalysisError, descriptive_bridge, ingest_csv  # noqa: E402


def _serialize(payload):
    return {key: format(value, "f") if isinstance(value, Decimal) else value for key, value in payload.items()}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--comparison-period", required=True)
    parser.add_argument("--target-period", required=True)
    parser.add_argument("--information-cutoff", required=True)
    parser.add_argument("--definition-family", required=True)
    parser.add_argument("--format", choices=("json", "csv"), default="json")
    args = parser.parse_args()
    try:
        connection = sqlite3.connect(args.database)
        connection.executescript((ROOT / "sql" / "schema.sql").read_text())
        ingest_csv(connection, args.input)
        result = descriptive_bridge(
            connection, args.comparison_period, args.target_period,
            args.information_cutoff, args.definition_family,
        )
    except (AnalysisError, OSError, sqlite3.Error) as error:
        print(f"analysis failed: {error}", file=sys.stderr)
        return 2
    finally:
        if "connection" in locals():
            connection.close()
    payload = _serialize(asdict(result))
    if args.format == "json":
        print(json.dumps(payload, indent=2))
    else:
        writer = csv.DictWriter(sys.stdout, fieldnames=payload.keys(), lineterminator="\n")
        writer.writeheader()
        writer.writerow(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
