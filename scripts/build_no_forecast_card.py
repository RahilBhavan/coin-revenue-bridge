#!/usr/bin/env python3
"""Render the no-forecast chart card (landscape and square) from analytics-ready-metrics.csv.

Needs Python 3.9+ and a Chromium binary (CHROMIUM, default "chromium"). The bar values are read
from the CSV and printed as stored; nothing is recomputed. The script also checks, in the
rendered page, that no text is under 26px, that the definition footer is one 28px line, and
that nothing overflows. It exits 1 if any check fails.
"""
import base64
import csv
import html
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = ROOT / "outputs/final-package/analytics-ready-metrics.csv"
FONT_DIR = ROOT / "scripts/card-fonts"
OUT_DIR = ROOT / "outputs/no-forecast-card"

NAVY = "#0B1F4B"
RED = "#C8102E"
WIDTH = 1024
MIN_PX = 26

TITLE = "Nine comparable quarters are too few to forecast"
DEFINITION = "Only these 9 quarters share one Coinbase definition, incl. restated 2023."
ALT = (
    "Only these 9 quarters share one Coinbase definition, including Q3-Q4 2023 as restated "
    "in Q1 2024; Coinbase later redefined trading volume."
)
METRIC = "consumer_transaction_revenue"

# name -> (height px, title px, chart area px)
CARDS = {"landscape": (576, 40, 232), "square": (1024, 56, 520)}


def load_rows():
    with open(CSV_PATH, newline="") as f:
        rows = list(csv.DictReader(f))
    bars = [r for r in rows if r["metric_name"] == METRIC]
    bars.sort(key=lambda r: r["period"])
    as_of = max(r["published_at"] for r in rows)[:10]
    return bars, as_of


def font_face(family, weight, name):
    data = base64.b64encode((FONT_DIR / name).read_bytes()).decode()
    return (
        f"@font-face{{font-family:'{family}';font-weight:{weight};"
        f"src:url(data:font/woff2;base64,{data}) format('woff2')}}"
    )


def fmt_value(text):
    whole, _, frac = text.partition(".")
    return f"{int(whole):,}" + (f".{frac}" if frac else "")


def quarter_label(period):
    year, q = period.split("-")
    return f"{q} ’{year[2:]}"


def month_day_year(iso):
    y, m, d = iso.split("-")
    names = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()
    return f"{names[int(m) - 1]} {int(d)}, {y}"


def build_html(name, bars, as_of):
    height, title_px, chart_px = CARDS[name]
    top = max(float(b["value_decimal"]) for b in bars)
    cols = []
    for b in bars:
        v = float(b["value_decimal"])
        restated = b["vintage_status"] == "recast"
        cols.append(
            f'<div class="col{" re" if restated else ""}">'
            f'<span class="val">{fmt_value(b["value_decimal"])}</span>'
            f'<div class="bar" style="height:{v / top * chart_px:.2f}px"></div>'
            f'<span class="q">{quarter_label(b["period"])}</span></div>'
        )
    n_restated = sum(1 for b in bars if b["vintage_status"] == "recast")
    restated_row = (
        f'<div class="restated" style="width:calc({n_restated} * 100% / {len(bars)})">'
        f"<span>restated</span></div>"
    )
    source = f"Source: Coinbase SEC filings. Data as of {month_day_year(as_of)}."
    fonts = (
        font_face("Roboto Slab", 700, "roboto-slab-latin-700-normal.woff2")
        + font_face("Archivo", 400, "archivo-latin-400-normal.woff2")
        + font_face("Archivo", 600, "archivo-latin-600-normal.woff2")
    )
    pad = 48 if name == "square" else 40
    return f"""<!doctype html><html lang="en"><meta charset="utf-8"><title>{html.escape(TITLE)}</title>
<style>{fonts}
*{{box-sizing:border-box;margin:0}}
html,body{{width:{WIDTH}px;height:{height}px;background:#fff;color:{NAVY};overflow:hidden}}
.card{{width:{WIDTH}px;height:{height}px;padding:{pad}px {pad}px {pad - 8}px;display:flex;flex-direction:column;
  font:400 {MIN_PX}px/1.25 Archivo,sans-serif}}
h1{{font:700 {title_px}px/1.15 'Roboto Slab',serif;letter-spacing:-.01em}}
.cap{{font-weight:600;margin-top:{20 if name == "square" else 10}px;color:{RED}}}
.chart{{flex:1;display:flex;flex-direction:column;justify-content:flex-end;min-height:0}}
.cols{{display:flex;align-items:flex-end;border-bottom:3px solid {NAVY}}}
.col{{flex:1;display:flex;flex-direction:column;align-items:center;position:relative}}
.val{{font-weight:600;letter-spacing:-.02em;white-space:nowrap;margin-bottom:4px}}
.bar{{width:70%;background:{NAVY}}}
.re .bar{{background:{RED}}}
.q{{position:absolute;top:100%;margin-top:6px;white-space:nowrap}}
.qrow{{height:{MIN_PX + 12}px}}
.restated{{margin-top:{MIN_PX + 14}px;border-top:3px solid {RED};text-align:center;color:{RED};font-weight:600;padding-top:2px}}
.foot{{margin-top:{18 if name == "square" else 8}px}}
.def{{font-size:28px;font-weight:600;white-space:nowrap}}
.src{{font-size:{MIN_PX}px;margin-top:2px;white-space:nowrap}}
</style>
<div class="card" role="img" aria-label="{html.escape(ALT)}">
<h1>{html.escape(TITLE)}</h1>
<div class="cap">Consumer transaction revenue, $M</div>
<div class="chart"><div class="cols">{"".join(cols)}</div>{restated_row}</div>
<div class="foot"><div class="def">{html.escape(DEFINITION)}</div><div class="src">{html.escape(source)}</div></div>
</div>
<script>
document.fonts.ready.then(()=>{{
  const out={{minPx:99,fonts:[],issues:[]}};
  const w=document.createTreeWalker(document.querySelector('.card'),NodeFilter.SHOW_TEXT);
  for(let n;n=w.nextNode();){{
    if(!n.textContent.trim())continue;
    const el=n.parentElement,cs=getComputedStyle(el);
    out.minPx=Math.min(out.minPx,parseFloat(cs.fontSize));
    const f=cs.fontFamily.split(',')[0].replace(/['"]/g,'');
    if(!out.fonts.includes(f))out.fonts.push(f);
    if(el.scrollWidth>el.clientWidth+1)out.issues.push('overflow-x: '+n.textContent);
  }}
  const d=document.querySelector('.def'),r=document.createRange();r.selectNodeContents(d);
  out.defLines=r.getClientRects().length;out.defPx=parseFloat(getComputedStyle(d).fontSize);
  out.defText=d.textContent;out.defRight=Math.round(d.getBoundingClientRect().left+r.getBoundingClientRect().width);
  const card=document.querySelector('.card').getBoundingClientRect();
  document.querySelectorAll('.card *').forEach(e=>{{const b=e.getBoundingClientRect();
    if(b.right>card.right+0.5||b.bottom>card.bottom+0.5||b.left<-0.5||b.top<-0.5)out.issues.push('outside card: '+e.className+' '+e.textContent.slice(0,20));}});
  const labels=[...document.querySelectorAll('.val,.q')].map(e=>e.getBoundingClientRect());
  for(let i=0;i<labels.length;i++)for(let j=i+1;j<labels.length;j++){{const a=labels[i],b=labels[j];
    if(a.left<b.right&&b.left<a.right&&a.top<b.bottom&&b.top<a.bottom)out.issues.push('labels overlap '+i+'/'+j);}}
  const fb=document.querySelector('.foot').getBoundingClientRect(),cb=document.querySelector('.restated').getBoundingClientRect();
  if(cb.bottom>fb.top)out.issues.push('chart overlaps footer');
  out.fontsLoaded=['700 20px "Roboto Slab"','400 20px Archivo','600 20px Archivo'].every(s=>document.fonts.check(s));
  document.title='CHECK:'+JSON.stringify(out);
}});
</script></html>"""


def chromium(*args):
    # These flags avoid hangs seen with the default GPU path and with user flag files
    # (extensions, Wayland); a throwaway profile keeps it apart from any running browser.
    with tempfile.TemporaryDirectory(prefix="nf-chromium-") as profile:
        return subprocess.run(
            [os.environ.get("CHROMIUM", "chromium"), "--headless", "--no-sandbox", "--disable-gpu",
             "--disable-gpu-compositing", "--use-gl=disabled", "--disable-extensions",
             "--run-all-compositor-stages-before-draw", "--hide-scrollbars",
             "--force-device-scale-factor=1", f"--user-data-dir={profile}", *args],
            capture_output=True, text=True, timeout=60,
        )


def check(page_path):
    dom = chromium("--virtual-time-budget=5000", "--dump-dom", f"file://{page_path}").stdout
    m = re.search(r"<title>CHECK:(.*?)</title>", dom, re.S)
    if not m:
        return None
    return json.loads(html.unescape(m.group(1)))


def main():
    bars, as_of = load_rows()
    if len(bars) != 9:
        sys.exit(f"expected 9 quarters of {METRIC}, found {len(bars)}")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "alt-text.txt").write_text(ALT + "\n")
    failed = False
    with tempfile.TemporaryDirectory(prefix="nf-card-") as tmp:
        for name, (height, _, _) in CARDS.items():
            page = Path(tmp) / f"{name}.html"
            page.write_text(build_html(name, bars, as_of))
            res = check(page)
            ok = (
                res is not None and res["minPx"] >= MIN_PX and res["defLines"] == 1
                and res["defPx"] == 28 and res["defText"] == DEFINITION and res["defRight"] <= WIDTH - 40
                and not res["issues"] and res["fontsLoaded"]
                and set(res["fonts"]) == {"Roboto Slab", "Archivo"}
            )
            print(f"{name}: {'PASS' if ok else 'FAIL'} {json.dumps(res)}")
            failed |= not ok
            png = OUT_DIR / f"no-forecast-card-{name}.png"
            png.unlink(missing_ok=True)
            chromium("--virtual-time-budget=5000", f"--window-size={WIDTH},{height}", f"--screenshot={png}", f"file://{page}")
            if not png.exists():
                sys.exit(f"chromium did not write {png}")
            print(f"wrote {png.relative_to(ROOT)}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
