#!/usr/bin/env python3
"""Reproduce one cutoff-safe forecast and exact bridge as JSON on stdout."""

import argparse
import json
import sqlite3
import sys
from dataclasses import asdict
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from strategic_finance.core import (  # noqa: E402
    AnalysisError,
    actual_pair,
    compute_bridge,
    forecast_target,
    ingest_csv,
)


def _json_default(value):
    if isinstance(value, Decimal):
        return format(value, "f")
    raise TypeError(f"cannot serialize {type(value).__name__}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--target-period", required=True)
    parser.add_argument("--information-cutoff", required=True)
    parser.add_argument("--definition-family", required=True)
    args = parser.parse_args()
    try:
        connection = sqlite3.connect(args.database)
        connection.executescript((ROOT / "sql" / "schema.sql").read_text())
        ingest_csv(connection, args.input)
        forecast = forecast_target(
            connection,
            args.target_period,
            args.information_cutoff,
            args.definition_family,
        )
        actual_revenue, actual_volume = actual_pair(
            connection, args.target_period, args.definition_family
        )
        bridge = compute_bridge(
            forecast.forecast_volume,
            actual_volume,
            forecast.forecast_yield,
            actual_revenue,
        )
    except (AnalysisError, OSError, sqlite3.Error) as error:
        print(f"analysis failed: {error}", file=sys.stderr)
        return 2
    finally:
        if "connection" in locals():
            connection.close()
    print(json.dumps({"forecast": asdict(forecast), "bridge": asdict(bridge)}, default=_json_default, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
