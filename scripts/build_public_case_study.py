#!/usr/bin/env python3
"""Build a self-contained public case-study folder and compact executive package."""

from __future__ import annotations

import csv
import hashlib
import json
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FINAL = ROOT / "outputs" / "final-package"
SITE = ROOT / "outputs" / "public-case-study"
EXEC = ROOT / "outputs" / "executive-package"


REVIEW = """# Practitioner review protocol

Status: **EXTERNAL HUMAN REVIEW NOT YET OBTAINED**

This package is ready to send to two independent reviewers. Do not relabel this status until named humans have returned written feedback.

## FP&A practitioner review

Ask the reviewer to answer:

1. Does the bridge improve a management conversation without implying causality?
2. Are the planning sensitivities useful, clearly editable, and sufficiently separated from forecasting?
3. Which decision threshold or management action is missing?
4. Is the executive summary concise enough for a finance leader?
5. Accept, revise, or reject. Explain the single most important reason.

## Accounting or data-governance review

Ask the reviewer to answer:

1. Are original and recast vintages distinguishable and correctly sourced?
2. Is the Q2-Q4 2025 definition crosswalk adequate to justify quarantine?
3. Are any periods, metrics, or units silently mixed?
4. Can every published number be traced to a frozen source or formula?
5. Accept, revise, or reject. Explain the single most important reason.

## Evidence to retain

Record reviewer name, role, review date, document version/hash, disposition, findings, and implemented changes. Preserve disagreements rather than converting them into an artificial consensus.
"""


def copy(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(source.read_bytes())


def manifest(directory: Path) -> None:
    rows = []
    for path in sorted(directory.rglob("*")):
        if path.is_file() and path.name != "manifest.json":
            rows.append({"path": str(path.relative_to(directory)), "bytes": path.stat().st_size, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    (directory / "manifest.json").write_text(json.dumps({"file_count": len(rows), "files": rows}, indent=2) + "\n", encoding="utf-8")


def money(value: str) -> str:
    return f"${float(value):,.1f}M"


def render_html() -> str:
    with (FINAL / "bridge-attribution.csv").open(newline="", encoding="utf-8") as handle:
        rows = {row["method"]: row for row in csv.DictReader(handle)}
    first, yield_first, shapley = rows["Volume first"], rows["Yield first"], rows["Symmetric Shapley"]
    values = {
        "@@TOTAL@@": money(first["total_change_mm"]),
        "@@VOL_FIRST@@": money(first["volume_effect_mm"]),
        "@@YIELD_FIRST@@": money(first["yield_effect_mm"]),
        "@@VOL_YIELD_FIRST@@": money(yield_first["volume_effect_mm"]),
        "@@YIELD_YIELD_FIRST@@": money(yield_first["yield_effect_mm"]),
        "@@VOL_SHAPLEY@@": money(shapley["volume_effect_mm"]),
        "@@YIELD_SHAPLEY@@": money(shapley["yield_effect_mm"]),
    }
    html = (ROOT / "scripts" / "public_case_study.html").read_text(encoding="utf-8")
    for token, value in values.items():
        html = html.replace(token, value)
    return html


def main() -> int:
    SITE.mkdir(parents=True, exist_ok=True)
    EXEC.mkdir(parents=True, exist_ok=True)
    (SITE / "index.html").write_text(render_html(), encoding="utf-8")
    (SITE / "practitioner-review.md").write_text(REVIEW, encoding="utf-8")
    site_files = {
        FINAL / "decision-memo.pdf": SITE / "decision-memo.pdf",
        FINAL / "reviewer-packet.pdf": SITE / "reviewer-packet.pdf",
        FINAL / "revenue-analysis.xlsx": SITE / "revenue-analysis.xlsx",
        FINAL / "workbook-preview.png": SITE / "workbook-preview.png",
        FINAL / "social-cut.webm": SITE / "social-cut.webm",
        FINAL / "social-cut.mp4": SITE / "social-cut.mp4",
    }
    for source, target in site_files.items(): copy(source, target)
    manifest(SITE)

    (EXEC / "README.md").write_text("# Executive review package\n\nStart with `decision-memo.pdf`, then inspect `revenue-analysis.xlsx`. Use `reviewer-packet.pdf` and `practitioner-review.md` to challenge the work. The analysis is descriptive and the planning cases are illustrative sensitivities, not forecasts.\n", encoding="utf-8")
    executive_files = {
        FINAL / "decision-memo.pdf": EXEC / "decision-memo.pdf",
        FINAL / "reviewer-packet.pdf": EXEC / "reviewer-packet.pdf",
        FINAL / "revenue-analysis.xlsx": EXEC / "revenue-analysis.xlsx",
        SITE / "practitioner-review.md": EXEC / "practitioner-review.md",
    }
    for source, target in executive_files.items(): copy(source, target)
    manifest(EXEC)
    zip_path = ROOT / "outputs" / "coin-revenue-bridge-executive-package.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(EXEC.rglob("*")):
            if path.is_file():
                # Fixed timestamp keeps the ZIP byte-identical across rebuilds.
                info = zipfile.ZipInfo(str(Path("executive-package") / path.relative_to(EXEC)), date_time=(2026, 9, 20, 0, 0, 0))
                info.external_attr = 0o644 << 16
                archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED)
    print(f"built {SITE}, {EXEC}, and {zip_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
