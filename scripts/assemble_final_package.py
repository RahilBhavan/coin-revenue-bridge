#!/usr/bin/env python3
"""Assemble the reviewer-facing project package and checksum manifest."""

from __future__ import annotations

import hashlib
import json
import shutil
import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "final-package"
COPIES = {
    ROOT / "outputs/descriptive-bridge/descriptive-revenue-bridge.xlsx": OUT / "revenue-analysis.xlsx",
    ROOT / "outputs/descriptive-bridge/descriptive-review.png": OUT / "workbook-preview.png",
    ROOT / "data/processed/reported-metric-observations.csv": OUT / "reported-metrics.csv",
    ROOT / "data/processed/analytics-ready-metric-observations.csv": OUT / "analytics-ready-metrics.csv",
    ROOT / "sql/descriptive_bridge.sql": OUT / "analysis.sql",
    ROOT / "sql/final_package_schema.sql": OUT / "schema.sql",
    ROOT / "scripts/reproduce_final_analysis.py": OUT / "reproduce.py",
    ROOT / "work/real-reporting-inputs/descriptive_bridge.csv": OUT / "descriptive-bridge.csv",
    ROOT / "work/enhanced-analysis/bridge-attribution.csv": OUT / "bridge-attribution.csv",
    ROOT / "work/enhanced-analysis/planning-scenarios.csv": OUT / "planning-scenarios.csv",
    ROOT / "work/enhanced-analysis/definition-reconciliation.csv": OUT / "definition-reconciliation.csv",
    ROOT / "outputs/descriptive-bridge/planning-sensitivity.png": OUT / "planning-sensitivity.png",
    ROOT / "outputs/descriptive-bridge/bridge-attribution.png": OUT / "bridge-attribution.png",
    ROOT / "outputs/descriptive-bridge/definition-reconciliation.png": OUT / "definition-reconciliation.png",
}


README = """# Coinbase revenue bridge: analysis package

Status: **DESCRIPTIVE / NOT A FORECAST**  
Evidence cutoff: **September 20, 2026**

## Decision

Use the Q3-to-Q4 2024 consumer transaction revenue bridge and editable planning sensitivities as decision-support diagnostics. Do not present a forecasting or causal-performance claim. The public panel contains nine comparable quarters, below the predeclared twelve-quarter gate.

## Start here

1. `decision-memo.pdf` - two-page decision and evidence boundary.
2. `revenue-analysis.xlsx` - inspectable seven-sheet model with trend, sensitivities, three attribution methods, definition crosswalks, and sources.
3. `reviewer-packet.pdf` - two-page challenge packet.
4. `demo.webm` or `demo.html` - three-minute captioned walkthrough.
5. `social-cut.mp4` - 30-second captioned H.264 social preview.
6. `validation-report.md` - executed V-01 through V-16 checks and limitations.

## Reproducibility files

- `reported-metrics.csv` - reviewed long-form source observations.
- `analytics-ready-metrics.csv` - normalized descriptive series.
- `descriptive-bridge.csv` - workbook bridge input.
- `bridge-attribution.csv` - volume-first, yield-first, and symmetric allocations.
- `planning-scenarios.csv` - editable illustrative sensitivity inputs and outputs.
- `definition-reconciliation.csv` - Q2-Q4 2025 earlier-versus-later volume vintages.
- `analysis.sql` - fixed-order SQL decomposition.
- `schema.sql` and `reproduce.py` - package-local executable reproduction path.
- `source-register.csv` - SEC accessions, URLs, timestamps, package-local paths, and SHA-256 hashes.
- `raw-sources/` - frozen SEC source documents covered by the source register.
- `overlap-reconciliation.csv` - repeated-quarter reconciliation across SEC tables.
- `ai-contribution.md` - tool contribution and human-review boundary.
- `package-manifest.json` - artifact hashes and sizes.

## Claim boundary

The $863.8M reported revenue increase is decomposed algebraically into an $852.9M volume effect and $10.9M calculated effective-yield effect under a fixed volume-first order. Effective yield is a proxy, not a reported fee rate or causal driver. Reversing bridge order reallocates about $7.0M while preserving the total.

The symmetric Shapley allocation averages both valid factor orders, assigning $856.4M to volume and $7.4M to calculated yield. The planning cases are mechanical sensitivities around Q4 2024 actuals, not management guidance, assigned probabilities, or expected outcomes.

## One-command reproduction

From this directory, run `python3 reproduce.py`. The script loads `analytics-ready-metrics.csv` into an in-memory SQLite database using `schema.sql`, executes `analysis.sql`, prints the bridge, and checks that the residual is within $0.1M.
"""


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    for source, target in COPIES.items():
        if not source.exists():
            raise FileNotFoundError(source)
        target.write_bytes(source.read_bytes())
    raw_out = OUT / "raw-sources"
    raw_out.mkdir(exist_ok=True)
    with (ROOT / "artifacts/source-register.csv").open(newline="", encoding="utf-8") as handle:
        source_rows = list(csv.DictReader(handle))
        fieldnames = list(source_rows[0])
    for row in source_rows:
        frozen_source = ROOT / row["local_path"]
        frozen_target = raw_out / frozen_source.name
        if not frozen_source.exists():
            raise FileNotFoundError(frozen_source)
        frozen_target.write_bytes(frozen_source.read_bytes())
        row["local_path"] = f"raw-sources/{frozen_source.name}"
    with (OUT / "source-register.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(source_rows)
    (OUT / "README.md").write_text(README, encoding="utf-8")
    files = []
    for path in sorted(OUT.rglob("*")):
        if not path.is_file() or path.name == "package-manifest.json":
            continue
        files.append({
            "path": str(path.relative_to(OUT)),
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
        })
    manifest = {
        "schema_version": "1.0",
        "status": "DESCRIPTIVE / NOT A FORECAST",
        "evidence_cutoff": "2026-09-20",
        "file_count": len(files),
        "files": files,
    }
    (OUT / "package-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"assembled {len(files)} files in {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
