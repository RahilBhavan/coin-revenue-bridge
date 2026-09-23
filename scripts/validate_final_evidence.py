#!/usr/bin/env python3
"""Emit deterministic, machine-readable validation evidence for the final package."""

from __future__ import annotations

import csv
import hashlib
import json
import sqlite3
import sys
import tempfile
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "final-package"
sys.path.insert(0, str(ROOT / "src"))

from strategic_finance.core import AnalysisError, ingest_csv  # noqa: E402


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    checks = []
    with (ROOT / "artifacts/source-register.csv").open(newline="", encoding="utf-8") as handle:
        sources = list(csv.DictReader(handle))
    mismatches = []
    for source in sources:
        local = ROOT / source["local_path"]
        if not local.exists() or sha256(local) != source["sha256"]:
            mismatches.append(source["source_id"])
    checks.append({"id": "source_hashes", "status": "PASS" if not mismatches else "FAIL", "count": len(sources), "mismatches": mismatches})

    with (ROOT / "data/processed/reported-metric-observations.csv").open(newline="", encoding="utf-8") as handle:
        observations = list(csv.DictReader(handle))
    registered = {row["source_id"] for row in sources}
    unresolved = sorted({row["source_id"] for row in observations} - registered)
    checks.append({"id": "source_resolution", "status": "PASS" if not unresolved else "FAIL", "observation_count": len(observations), "unresolved": unresolved})

    keys = [(r["metric_name"], r["period_end"], r["definition_family"], r["source_id"]) for r in observations]
    checks.append({"id": "duplicate_keys", "status": "PASS" if len(keys) == len(set(keys)) else "FAIL", "unique": len(set(keys)), "rows": len(keys)})

    duplicate_rejected = False
    with tempfile.TemporaryDirectory() as directory:
        duplicate_path = Path(directory) / "duplicate.csv"
        original = (ROOT / "data/processed/reported-metric-observations.csv").read_text(encoding="utf-8")
        duplicate_path.write_text(original + original.splitlines()[1] + "\n", encoding="utf-8")
        connection = sqlite3.connect(":memory:")
        connection.executescript((ROOT / "sql/schema.sql").read_text(encoding="utf-8"))
        try:
            ingest_csv(connection, duplicate_path)
        except AnalysisError as error:
            duplicate_rejected = "duplicate or invalid observation" in str(error)
        finally:
            connection.close()
    checks.append({"id": "duplicate_import_rejection", "status": "PASS" if duplicate_rejected else "FAIL"})

    with (ROOT / "work/real-reporting-inputs/descriptive_bridge.csv").open(newline="", encoding="utf-8") as handle:
        bridge = next(csv.DictReader(handle))
    r0, r1 = Decimal(bridge["from_revenue_mm"]), Decimal(bridge["to_revenue_mm"])
    v0, v1 = Decimal(bridge["from_volume_bn"]), Decimal(bridge["to_volume_bn"])
    y0, y1 = Decimal(bridge["from_yield_pct"]), Decimal(bridge["to_yield_pct"])
    change = r1 - r0
    volume_effect = (v1 - v0) * y0 * Decimal(10)
    yield_effect = v1 * (y1 - y0) * Decimal(10)
    residual = change - volume_effect - yield_effect
    alt_yield = v0 * (y1 - y0) * Decimal(10)
    alt_volume = (v1 - v0) * y1 * Decimal(10)
    checks.append({"id": "bridge_reconciliation", "status": "PASS" if abs(residual) <= Decimal("0.1") else "FAIL", "revenue_change_mm": str(change), "volume_effect_mm": str(volume_effect), "yield_effect_mm": str(yield_effect), "residual_mm": str(residual)})
    checks.append({"id": "alternate_order", "status": "PASS" if abs(change - alt_yield - alt_volume) <= Decimal("0.1") else "FAIL", "yield_first_yield_effect_mm": str(alt_yield), "yield_first_volume_effect_mm": str(alt_volume), "allocation_shift_mm": str(abs(alt_volume - volume_effect))})

    with (ROOT / "work/enhanced-analysis/bridge-attribution.csv").open(newline="", encoding="utf-8") as handle:
        attribution = {row["method"]: row for row in csv.DictReader(handle)}
    shapley = attribution["Symmetric Shapley"]
    shapley_total = Decimal(shapley["volume_effect_mm"]) + Decimal(shapley["yield_effect_mm"])
    checks.append({"id": "symmetric_attribution", "status": "PASS" if abs(shapley_total - change) <= Decimal("0.1") else "FAIL", "volume_effect_mm": shapley["volume_effect_mm"], "yield_effect_mm": shapley["yield_effect_mm"], "residual_mm": shapley["residual_mm"]})

    with (ROOT / "work/enhanced-analysis/planning-scenarios.csv").open(newline="", encoding="utf-8") as handle:
        scenarios = list(csv.DictReader(handle))
    scenario_values = [Decimal(row["implied_revenue_mm"]) for row in scenarios]
    checks.append({"id": "planning_sensitivities", "status": "PASS" if scenario_values == [Decimal("1002.4800"), Decimal("1347.1000"), Decimal("1729.3200")] else "FAIL", "cases": [{"case": row["case"], "implied_revenue_mm": row["implied_revenue_mm"]} for row in scenarios]})

    with (ROOT / "work/enhanced-analysis/definition-reconciliation.csv").open(newline="", encoding="utf-8") as handle:
        reconciliation = list(csv.DictReader(handle))
    changes = [Decimal(row["change_bn"]) for row in reconciliation]
    checks.append({"id": "definition_reconciliation", "status": "PASS" if changes == [Decimal("-1.5"), Decimal("-1.6"), Decimal("-2.3")] else "FAIL", "periods": len(reconciliation), "changes_bn": [str(value) for value in changes]})

    memo = (ROOT / "outputs/descriptive-bridge/descriptive-memo.md").read_text(encoding="utf-8")
    expected_claims = [f"{change:.1f}", f"{volume_effect:.1f}", f"{yield_effect:.1f}", "DESCRIPTIVE / NOT A FORECAST"]
    missing_claims = [claim for claim in expected_claims if claim not in memo]
    checks.append({"id": "memo_claims", "status": "PASS" if not missing_claims else "FAIL", "missing": missing_claims})

    demo = (OUT / "demo.html").read_text(encoding="utf-8") if (OUT / "demo.html").exists() else ""
    required_demo_claims = ["DESCRIPTIVE / NOT A FORECAST", "not an extrapolation", "does not prove management causality", "definition break"]
    missing_demo_claims = [claim for claim in required_demo_claims if claim.lower() not in demo.lower()]
    checks.append({"id": "demo_claim_audit", "status": "PASS" if not missing_demo_claims else "FAIL", "missing": missing_demo_claims})

    site = ROOT / "outputs/public-case-study/index.html"
    site_text = site.read_text(encoding="utf-8") if site.exists() else ""
    checks.append({"id": "public_case_study", "status": "PASS" if "DESCRIPTIVE / NOT A FORECAST" in site_text and "Symmetric" in site_text and "Illustrative planning sensitivities" in site_text else "FAIL"})
    review_protocol = ROOT / "outputs/public-case-study/practitioner-review.md"
    review_text = review_protocol.read_text(encoding="utf-8") if review_protocol.exists() else ""
    checks.append({"id": "human_review_disclosure", "status": "PASS" if "EXTERNAL HUMAN REVIEW NOT YET OBTAINED" in review_text else "FAIL"})

    deliverables = [OUT / name for name in ("decision-memo.pdf", "reviewer-packet.pdf", "demo.webm", "social-cut.webm", "demo.html", "demo-script.md", "ai-contribution.md", "validation-report.md", "overlap-reconciliation.csv", "bridge-attribution.csv", "planning-scenarios.csv", "definition-reconciliation.csv")]
    existing = [{"path": str(p.relative_to(ROOT)), "sha256": sha256(p)} for p in deliverables if p.exists()]
    checks.append({"id": "deliverable_presence", "status": "PASS" if len(existing) == len(deliverables) else "FAIL", "files": existing})
    payload = {"generated_from": "local reviewed artifacts", "checks": checks}
    OUT.mkdir(parents=True, exist_ok=True)
    target = OUT / "validation-evidence.json"
    target.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
