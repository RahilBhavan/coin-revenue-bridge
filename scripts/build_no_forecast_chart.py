#!/usr/bin/env python3
"""Build the "Needed 12 quarters. Got 9. So no forecast." post images.

Reads the quarter count, the 12-quarter gate and the reclassification quarter
from the repo (README.md, outputs/final-package/validation-report.md and
outputs/final-package/analytics-ready-metrics.csv), renders a landscape
(1024x576) and a square (1024x1024) image at 2x with headless Chromium, and
writes the alt text. Python standard library only; needs a Chromium binary.

    python3 scripts/build_no_forecast_chart.py
"""
import argparse
import base64
import csv
import json
import re
import shutil
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FONT_DIR = ROOT / "scripts" / "assets" / "fonts"
README = ROOT / "README.md"
VALIDATION = ROOT / "outputs" / "final-package" / "validation-report.md"
METRICS = ROOT / "outputs" / "final-package" / "analytics-ready-metrics.csv"

NAVY = "#0a2463"
RED = "#c8102e"
MIN_TEXT_PX = 26
SCALE = 2
FORMATS = {"landscape": (1024, 576), "square": (1024, 1024)}
NUMBER_WORDS = {w: i for i, w in enumerate(
    "zero one two three four five six seven eight nine ten eleven twelve".split())}


def number(word):
    return NUMBER_WORDS[word.lower()]


def find(pattern, text, source):
    match = re.search(pattern, text, re.S)
    if not match:
        sys.exit(f"{source}: no match for {pattern!r}")
    return match


def load_facts():
    readme = README.read_text(encoding="utf-8")
    validation = VALIDATION.read_text(encoding="utf-8")

    gate = find(r"at least (\w+) comparable quarters \((\w+) to train, (\w+) to test\)"
                r"\. The public filings support (\w+) under one definition", readme, "README")
    required, train, test, supported = (number(g) for g in gate.groups())
    reclass = find(r"reclassified consumer revenue in (Q\d) (\d{4})", readme, "README")
    title = find(r"^# COIN revenue bridge: (Q\d) to (Q\d) (\d{4})", readme, "README")
    repo = find(r"github\.com/([\w-]+/[\w.-]+)/actions", readme, "README").group(1)
    gate_v = find(r"Only (\w+) comparable paired quarters .*? predeclared (\w+)-quarter minimum",
                  validation, "validation-report.md")

    with METRICS.open(newline="", encoding="utf-8") as handle:
        periods = list(dict.fromkeys(row["period"] for row in csv.DictReader(handle)))
    quarters = []
    for period in periods:
        year, quarter = period.split("-")
        quarters.append(f"{quarter} '{year[2:]}")

    if train + test != required:
        sys.exit(f"README gate {train}+{test} does not equal {required}")
    if number(gate_v.group(1)) != supported or number(gate_v.group(2)) != required:
        sys.exit("validation-report.md gate disagrees with README")
    if len(quarters) != supported:
        sys.exit(f"{METRICS.name} has {len(quarters)} quarters; README says {supported}")

    return {
        "required": required, "train": train, "test": test, "have": supported,
        "quarters": quarters,
        "reclass": f"{reclass.group(1)} {reclass.group(2)}",
        "bridge": f"{title.group(1)}-to-{title.group(2)} {title.group(3)}",
        "repo": repo,
    }


def data_vintage():
    """Date and short sha of the last commit that changed the quarterly data."""
    out = subprocess.run(
        ["git", "log", "-1", "--format=%cs %h", "--",
         str(METRICS.relative_to(ROOT)), "data/processed/analytics-ready-metric-observations.csv"],
        cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
    if len(out) != 2:
        sys.exit("git log found no commit for the data files; pass --as-of and --sha")
    return out[0], out[1]


def font_face(family, weight, filename):
    data = base64.b64encode((FONT_DIR / filename).read_bytes()).decode()
    return (f"@font-face{{font-family:'{family}';font-weight:{weight};"
            f"src:url(data:font/ttf;base64,{data}) format('truetype')}}")


CSS = """
*{box-sizing:border-box;margin:0;padding:0}
html,body{width:var(--w);height:var(--h);background:#fff;overflow:hidden}
body{display:flex;flex-direction:column;justify-content:space-between;
  padding:var(--pad);gap:var(--gap-l);color:var(--navy);font-family:'Archivo',sans-serif;font-weight:400;
  -webkit-font-smoothing:antialiased}
h1{font-family:'Roboto Slab',serif;font-weight:700;font-size:var(--t-title);line-height:1.12;
  letter-spacing:-0.005em}
.sub{margin-top:var(--gap-s);font-size:var(--t-body);line-height:1.3}
.boxes{display:grid;grid-template-columns:repeat(var(--cols),1fr);grid-auto-rows:1fr;gap:var(--box-gap)}
.box{display:flex;flex-direction:var(--label-dir);gap:var(--label-gap);align-items:center;justify-content:center;
  min-height:var(--box-h);border:var(--bw) solid var(--navy);background:var(--navy);color:#fff;
  font-weight:600;font-size:var(--t-label);line-height:1.1;text-align:center}
.box.missing{background:#fff;border:var(--bw) dashed var(--red)}
.key{display:flex;flex-wrap:wrap;column-gap:var(--gap-m);row-gap:4px;margin-top:var(--gap-s);
  font-size:var(--t-body);line-height:1.2}
.key span{display:inline-flex;align-items:center;gap:10px}
.sw{display:inline-block;width:var(--t-body);height:var(--t-body);background:var(--navy);
  border:3px solid var(--navy)}
.sw.missing{background:#fff;border:3px dashed var(--red)}
.key .m{color:var(--red)}
.gate{font-weight:600;font-size:var(--t-gate);line-height:1.2}
.why{margin-top:var(--gap-s);font-size:var(--t-body);line-height:1.3}
.foot{font-size:var(--t-foot);line-height:1.2;white-space:nowrap}
.chart{flex:var(--chart-flex);display:flex;flex-direction:column;justify-content:center}
.chart .boxes{flex:var(--grid-flex)}
.notes{margin-top:var(--gap-s)}
"""

VARS = {
    "landscape": {"pad": "30px 36px", "t-title": "46px", "t-body": "26px", "t-label": "26px",
                  "t-gate": "28px", "t-foot": "26px", "gap-s": "8px", "gap-m": "30px", "gap-l": "12px", "label-dir": "column", "label-gap": "0px", "box-gap": "6px",
                  "box-h": "78px", "bw": "3px", "cols": "12", "chart-flex": "0 0 auto",
                  "grid-flex": "0 0 auto"},
    "square": {"pad": "52px 44px", "t-title": "68px", "t-body": "32px", "t-label": "42px",
               "t-gate": "40px", "t-foot": "26px", "gap-s": "20px", "gap-m": "40px", "gap-l": "40px", "label-dir": "row", "label-gap": "0.3em", "box-gap": "18px",
               "box-h": "0px", "bw": "4px", "cols": "4", "chart-flex": "1 1 auto",
               "grid-flex": "1 1 auto"},
}

CHECK_JS = """
(async () => {
  await document.fonts.ready;
  const out = {fonts: [...document.fonts].map(f => [f.family, f.weight, f.status]),
               sizes: [], overflow: [], lines: {}};
  const css = getComputedStyle(document.documentElement);
  const W = parseFloat(css.getPropertyValue('--w')), H = parseFloat(css.getPropertyValue('--h'));
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  for (let n; (n = walker.nextNode());) {
    if (!n.textContent.trim() || ['SCRIPT', 'STYLE', 'TITLE'].includes(n.parentElement.tagName)) continue;
    const el = n.parentElement, cs = getComputedStyle(el);
    out.sizes.push([n.textContent.trim(), parseFloat(cs.fontSize), cs.fontFamily.split(',')[0]]);
    const range = document.createRange(); range.selectNodeContents(n);
    const t = range.getBoundingClientRect();
    const c = (el.closest('.box') || el).getBoundingClientRect();
    if (t.left < c.left - 0.5 || t.right > c.right + 0.5 || t.left < 24 || t.right > W - 24 || t.top < 24 || t.bottom > H - 24)
      out.overflow.push([n.textContent.trim(), Math.round(t.left), Math.round(t.right),
                         Math.round(t.top), Math.round(t.bottom)]);
  }
  for (const el of document.querySelectorAll('[data-role]')) {
    const lh = parseFloat(getComputedStyle(el).lineHeight);
    out.lines[el.dataset.role] = Math.round(el.getBoundingClientRect().height / lh);
  }
  const b = document.querySelector('.foot').getBoundingClientRect();
  const first = document.querySelector('h1').getBoundingClientRect();
  out.footBottom = b.bottom; out.titleTop = first.top; out.height = H;
  const pre = document.createElement('pre'); pre.id = 'report';
  pre.textContent = JSON.stringify(out); document.body.appendChild(pre);
})();
"""


def build_html(fmt, facts, footer, check=False):
    width, height = FORMATS[fmt]
    variables = {"w": f"{width}px", "h": f"{height}px", "navy": NAVY, "red": RED, **VARS[fmt]}
    root = ";".join(f"--{k}:{v}" for k, v in variables.items())
    faces = (font_face("Roboto Slab", 700, "RobotoSlab-Bold.ttf")
             + font_face("Archivo", 400, "Archivo-Regular.ttf")
             + font_face("Archivo", 600, "Archivo-SemiBold.ttf"))

    def box(label, missing=False):
        if missing:
            return '<div class="box missing"></div>'
        q, yr = label.split(" ")
        return f'<div class="box"><span class="part">{q}</span> <span class="part">{yr}</span></div>'

    boxes = "".join(box(q) for q in facts["quarters"]) \
        + "".join(box("", True) for _ in range(facts["required"] - facts["have"]))
    missing_n = facts["required"] - facts["have"]
    title_a = f"Needed {facts['required']} quarters."
    title_b = f"Got {facts['have']}. So no forecast."
    sub = (f"This repo publishes a {facts['bridge']} revenue bridge "
           f"(a descriptive breakdown), not a forecast.")
    why = (f"{facts['reclass']}: Coinbase reclassified consumer revenue, so a longer series "
           f"would mix incompatible numbers.")
    gate = f"{facts['required']} required ({facts['train']} train / {facts['test']} test)"
    title_html = (f'{title_a}<br>{title_b}' if fmt == "square" else f'{title_a} {title_b}')
    script = f"<script>{CHECK_JS}</script>" if check else ""
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<title>Needed {facts['required']} quarters. Got {facts['have']}. So no forecast.</title>
<style>{faces}:root{{{root}}}{CSS}</style></head>
<body class="{fmt}">
<header><h1 data-role="title">{title_html}</h1>
<p class="sub" data-role="sub">{sub}</p></header>
<section class="chart"><div class="boxes">{boxes}</div>
<div class="key"><span><i class="sw"></i>{facts['have']} comparable quarters</span>
<span class="m"><i class="sw missing"></i>{missing_n} missing</span></div>
<div class="notes"><p class="gate" data-role="gate">{gate}</p>
<p class="why" data-role="why">{why}</p></div></section>
<footer class="foot" data-role="foot">{footer}</footer>{script}</body></html>"""


def chromium_bin(explicit):
    for name in ([explicit] if explicit else []) + ["chromium", "chromium-browser", "google-chrome"]:
        found = shutil.which(name)
        if found:
            return found
    sys.exit("Chromium not found; pass --chromium")


def chromium(binary, *args):
    # swiftshader and a throwaway profile keep headless screenshots from hanging
    with tempfile.TemporaryDirectory(prefix="chromium-profile-") as profile:
        return subprocess.run(
            [binary, "--headless=new", f"--user-data-dir={profile}", "--no-sandbox",
             "--use-gl=swiftshader", "--no-first-run", "--disable-background-networking",
             "--disable-dev-shm-usage", "--hide-scrollbars", *args],
            capture_output=True, text=True, timeout=90)


def check_layout(binary, fmt, html_path):
    width, height = FORMATS[fmt]
    result = chromium(binary, f"--window-size={width},{height}", "--virtual-time-budget=4000",
                      "--dump-dom", html_path.as_uri())
    match = re.search(r'<pre id="report">(.*?)</pre>', result.stdout, re.S)
    if not match:
        sys.exit(f"{fmt}: layout check produced no report\n{result.stderr[-500:]}")
    report = json.loads(match.group(1).replace("&quot;", '"').replace("&amp;", "&")
                        .replace("&lt;", "<").replace("&gt;", ">"))
    problems = []
    unloaded = [f for f in report["fonts"] if f[2] != "loaded"]
    if unloaded or len(report["fonts"]) != 3:
        problems.append(f"fonts not loaded: {report['fonts']}")
    small = [s for s in report["sizes"] if s[1] < MIN_TEXT_PX]
    if small:
        problems.append(f"text under {MIN_TEXT_PX}px: {small}")
    families = {s[2].strip("'\"") for s in report["sizes"]}
    if not families <= {"Roboto Slab", "Archivo"}:
        problems.append(f"unexpected font family: {families}")
    if report["overflow"]:
        problems.append(f"overflow: {report['overflow']}")
    if report["lines"]["foot"] != 1:
        problems.append("footer wraps")
    if fmt == "landscape" and report["lines"]["title"] != 1:
        problems.append("title wraps")
    if fmt == "square" and report["lines"]["title"] != 2:
        problems.append("square title is not two lines")
    if problems:
        sys.exit(f"{fmt} layout check failed:\n  " + "\n  ".join(problems))
    sizes = sorted({s[1] for s in report["sizes"]})
    print(f"{fmt}: fonts loaded, text sizes {sizes} px, no overflow")


def png_size(path):
    with path.open("rb") as handle:
        head = handle.read(24)
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        sys.exit(f"{path} is not a PNG")
    return struct.unpack(">II", head[16:24])


def alt_text(facts, footer):
    quarters = ", ".join(facts["quarters"][:-1]) + f" and {facts['quarters'][-1]}"
    missing = facts["required"] - facts["have"]
    return (
        f"Chart titled \"Needed {facts['required']} quarters. Got {facts['have']}. So no forecast.\" "
        f"It shows {facts['required']} quarter boxes. {facts['have']} filled navy boxes are the "
        f"comparable quarters, labeled {quarters}. {missing} red dashed boxes are the missing "
        f"quarters. A note says {facts['required']} are required ({facts['train']} train / "
        f"{facts['test']} test), and that Coinbase reclassified consumer revenue in {facts['reclass']}, "
        f"so a longer series would mix incompatible numbers. The subtitle says the repo publishes a "
        f"{facts['bridge']} revenue bridge, a descriptive breakdown, not a forecast. "
        f"Footer: {footer}.\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out-dir", type=Path, default=ROOT / "docs")
    parser.add_argument("--chromium")
    parser.add_argument("--as-of", help="override the data date (YYYY-MM-DD)")
    parser.add_argument("--sha", help="override the short sha")
    args = parser.parse_args()

    facts = load_facts()
    date, sha = (args.as_of, args.sha) if args.as_of and args.sha else data_vintage()
    footer = f"github.com/{facts['repo']} · Data as of {date} ({sha})"
    binary = chromium_bin(args.chromium)
    args.out_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="no-forecast-chart-") as tmp:
        for fmt, (width, height) in FORMATS.items():
            check_path = Path(tmp) / f"{fmt}-check.html"
            check_path.write_text(build_html(fmt, facts, footer, check=True), encoding="utf-8")
            check_layout(binary, fmt, check_path)

            page = Path(tmp) / f"{fmt}.html"
            page.write_text(build_html(fmt, facts, footer), encoding="utf-8")
            target = args.out_dir / f"no-forecast-chart-{fmt}.png"
            shot = chromium(binary, f"--window-size={width},{height}",
                            f"--force-device-scale-factor={SCALE}",
                            f"--screenshot={target}", page.as_uri())
            if not target.exists():
                sys.exit(f"{fmt}: screenshot failed\n{shot.stderr[-500:]}")
            got = png_size(target)
            if got != (width * SCALE, height * SCALE):
                sys.exit(f"{fmt}: expected {width * SCALE}x{height * SCALE}, got {got[0]}x{got[1]}")
            print(f"wrote {target} {got[0]}x{got[1]}")

    alt = args.out_dir / "no-forecast-chart-alt.txt"
    alt.write_text(alt_text(facts, footer), encoding="utf-8")
    print(f"wrote {alt}")


if __name__ == "__main__":
    main()
