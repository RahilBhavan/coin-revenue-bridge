#!/usr/bin/env python3
"""Build a self-contained public case-study folder and compact executive package."""

from __future__ import annotations

import hashlib
import json
import shutil
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FINAL = ROOT / "outputs" / "final-package"
SITE = ROOT / "outputs" / "public-case-study"
EXEC = ROOT / "outputs" / "executive-package"


HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Coinbase consumer transaction revenue bridge</title>
<meta name="description" content="An independent, source-backed strategic-finance case study using Coinbase SEC filings.">
<style>
:root{--navy:#10233f;--blue:#1652f0;--ink:#172b3a;--muted:#526575;--ice:#f4f8fc;--line:#cfd9e5;--green:#087a55;--amber:#9a6700}*{box-sizing:border-box}body{margin:0;font:16px/1.55 Arial,sans-serif;color:var(--ink);background:#fff}a{color:var(--blue)}.wrap{max-width:1080px;margin:auto;padding:0 28px}.bar{height:10px;background:var(--navy)}header{padding:76px 0 52px;background:linear-gradient(135deg,#f7faff,#eaf2ff)}.eyebrow{font-weight:700;color:var(--blue);letter-spacing:.08em;font-size:13px}.status{display:inline-block;margin-top:18px;padding:7px 10px;border:1px solid #e6b94a;background:#fff7d6;color:#7a5100;font-weight:700}h1{font-size:52px;line-height:1.04;max-width:850px;margin:14px 0 20px;color:var(--navy)}h2{font-size:32px;color:var(--navy);margin:0 0 18px}h3{color:var(--navy)}.lede{font-size:21px;max-width:780px;color:var(--muted)}section{padding:64px 0;border-top:1px solid var(--line)}.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}.card{padding:22px;border:1px solid var(--line);background:white}.metric{font-weight:700;font-size:31px;color:var(--navy)}.label{font-size:13px;color:var(--muted)}.two{display:grid;grid-template-columns:1.1fr .9fr;gap:42px;align-items:start}.callout{padding:22px;border-left:5px solid var(--green);background:#e7f8f2}.warning{padding:22px;border-left:5px solid var(--amber);background:#fff4d6}.bars{display:grid;gap:15px}.barrow{display:grid;grid-template-columns:150px 1fr 90px;gap:12px;align-items:center}.track{height:18px;background:#e9eef5}.fill{height:100%;background:var(--blue)}table{width:100%;border-collapse:collapse}th{background:var(--navy);color:#fff;text-align:left}th,td{padding:12px;border:1px solid var(--line)}.actions{display:flex;flex-wrap:wrap;gap:12px;margin-top:24px}.button{display:inline-block;padding:11px 16px;background:var(--blue);color:white;text-decoration:none;font-weight:700}.button.alt{background:white;color:var(--blue);border:1px solid var(--blue)}img{max-width:100%;border:1px solid var(--line)}footer{padding:40px 0;color:var(--muted);font-size:14px;background:var(--ice)}@media(max-width:760px){h1{font-size:37px}.grid{grid-template-columns:1fr 1fr}.two{grid-template-columns:1fr}.barrow{grid-template-columns:110px 1fr 70px}.wrap{padding:0 18px}}
</style></head><body><div class="bar"></div>
<header><div class="wrap"><div class="eyebrow">INDEPENDENT STRATEGIC-FINANCE CASE STUDY</div><h1>The forecast I chose not to publish</h1><p class="lede">Public Coinbase filings supported a useful revenue bridge, but not the predeclared forecast gate. The result is a smaller, inspectable analysis with every limitation visible.</p><div class="status">DESCRIPTIVE / NOT A FORECAST</div><div class="actions"><a class="button" href="decision-memo.pdf">Read the two-page memo</a><a class="button alt" href="revenue-analysis.xlsx">Inspect the workbook</a></div></div></header>
<main>
<section><div class="wrap"><h2>Q3 to Q4 2024</h2><div class="grid"><div class="card"><div class="metric">$863.8M</div><div class="label">reported revenue increase</div></div><div class="card"><div class="metric">$852.9M</div><div class="label">fixed-order volume effect</div></div><div class="card"><div class="metric">$10.9M</div><div class="label">fixed-order yield effect</div></div><div class="card"><div class="metric">$0.0M</div><div class="label">rounded residual</div></div></div></div></section>
<section><div class="wrap two"><div><h2>Why the forecast stopped</h2><p>The design required twelve comparable observations: eight training quarters and four chronological holdouts. The scoped public panel contained nine. A Q1 2024 revenue reclassification and later Trading Volume changes created additional vintage boundaries.</p><div class="warning"><strong>Decision:</strong> reject model-performance claims and use the evidence for a descriptive bridge and planning sensitivities.</div></div><img src="workbook-preview.png" alt="Workbook summary showing the nine-quarter revenue trend and Q3 to Q4 2024 bridge"></div></section>
<section><div class="wrap"><h2>Three valid bridge orders</h2><p>The interaction term moves depending on factor order. The symmetric Shapley method averages both valid orders instead of hiding the choice.</p><div class="bars"><div class="barrow"><strong>Volume first</strong><div class="track"><div class="fill" style="width:98.7%"></div></div><span>$852.9M</span></div><div class="barrow"><strong>Yield first</strong><div class="track"><div class="fill" style="width:99.5%"></div></div><span>$859.9M</span></div><div class="barrow"><strong>Symmetric</strong><div class="track"><div class="fill" style="width:99.1%"></div></div><span>$856.4M</span></div></div><p class="label">Bars show the volume component as a share of the $863.8M change. They do not show causal contribution.</p></div></section>
<section><div class="wrap"><h2>Illustrative planning sensitivities</h2><table><thead><tr><th>Case</th><th>Volume change</th><th>Yield change</th><th>Implied revenue</th><th>Management prompt</th></tr></thead><tbody><tr><td>Downside</td><td>-20%</td><td>-10 bps</td><td>$1,002.5M</td><td>Investigate activity retention and mix.</td></tr><tr><td>Reference</td><td>0%</td><td>0 bps</td><td>$1,347.1M</td><td>Q4 2024 actual reference; not a forecast.</td></tr><tr><td>Upside</td><td>+20%</td><td>+10 bps</td><td>$1,729.3M</td><td>Test operating readiness and mix sustainability.</td></tr></tbody></table><p class="label">These cases are editable mechanical sensitivities. They are not Coinbase guidance, probabilities, or expected outcomes.</p></div></section>
<section><div class="wrap two"><div><h2>Definition control</h2><p>The later Q2 2026 deck restated Q2-Q4 2025 consumer spot volumes below earlier disclosures by $1.5B, $1.6B, and $2.3B. The project preserves both vintages and keeps those periods outside the earlier panel.</p><div class="callout"><strong>Why it matters:</strong> a longer series is not automatically a more comparable series.</div></div><div><h2>Reproducible by design</h2><ul><li>13 frozen SEC sources with SHA-256 hashes</li><li>Formula-driven seven-sheet workbook</li><li>One-command SQL reproduction</li><li>Automated definition, cutoff, duplicate, and bridge checks</li><li>Public AI contribution disclosure</li></ul></div></div></section>
<section><div class="wrap"><h2>Review the evidence</h2><p>The package is designed to be challenged. Start with the memo, inspect formulas in the workbook, then use the reviewer packet to test the strongest objections.</p><div class="actions"><a class="button" href="decision-memo.pdf">Decision memo</a><a class="button alt" href="revenue-analysis.xlsx">Workbook</a><a class="button alt" href="reviewer-packet.pdf">Reviewer packet</a><a class="button alt" href="social-cut.webm">30-second social cut</a><a class="button alt" href="practitioner-review.md">Review protocol</a></div></div></section>
</main><footer><div class="wrap">Independent portfolio analysis based on public SEC filings. No Coinbase endorsement, investment recommendation, causal finding, or forecast-performance claim.</div></footer></body></html>"""


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
    shutil.copy2(source, target)


def manifest(directory: Path) -> None:
    rows = []
    for path in sorted(directory.rglob("*")):
        if path.is_file() and path.name != "manifest.json":
            rows.append({"path": str(path.relative_to(directory)), "bytes": path.stat().st_size, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    (directory / "manifest.json").write_text(json.dumps({"file_count": len(rows), "files": rows}, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    SITE.mkdir(parents=True, exist_ok=True)
    EXEC.mkdir(parents=True, exist_ok=True)
    (SITE / "index.html").write_text(HTML, encoding="utf-8")
    (SITE / "practitioner-review.md").write_text(REVIEW, encoding="utf-8")
    site_files = {
        FINAL / "decision-memo.pdf": SITE / "decision-memo.pdf",
        FINAL / "reviewer-packet.pdf": SITE / "reviewer-packet.pdf",
        FINAL / "revenue-analysis.xlsx": SITE / "revenue-analysis.xlsx",
        FINAL / "workbook-preview.png": SITE / "workbook-preview.png",
        FINAL / "social-cut.webm": SITE / "social-cut.webm",
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
    zip_path = ROOT / "outputs" / "coinbase-strategic-finance-executive-package.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(EXEC.rglob("*")):
            if path.is_file(): archive.write(path, Path("executive-package") / path.relative_to(EXEC))
    print(f"built {SITE}, {EXEC}, and {zip_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
