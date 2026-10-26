#!/usr/bin/env python3
"""Render the revenue bridge card (landscape 1024x640 and square 1024x1024) to outputs/revenue-bridge-card/.

The bars are the Q3 to Q4 2024 consumer transaction revenue bridge: start, volume effect, yield
effect, end. Start and end come from descriptive-bridge.csv and the symmetric Shapley split from
bridge-attribution.csv, both printed to one decimal in $M. The script refuses to render unless the
printed numbers add up (483.3 + 856.4 + 7.4 = 1,347.1).

Needs Python 3.9+ and Chromium (CHROMIUM, default "chromium"). It checks, in the rendered page, that
no text is under 26px, that the Shapley line sits above the chart on one line, that the footer is one
line, that every bar label carries "$" and "M", and that nothing overflows or overlaps. It checks the
PNG sizes, writes alt-text.txt and manifest.json (SHA-256 of each PNG), and exits 1 if any check fails.
"""
import csv
import hashlib
import html
import json
import re
import struct
import sys
import tempfile
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

from build_no_forecast_card import chromium, font_face, fmt_value, month_day_year

ROOT = Path(__file__).resolve().parent.parent
PKG = ROOT / "outputs/final-package"
OUT_DIR = ROOT / "outputs/revenue-bridge-card"

NAVY = "#0B1F4B"
RED = "#C8102E"
WIDTH = 1024
MIN_PX = 26
ONE = Decimal("0.1")

TITLE = "Volume drove ${volume}M of Coinbase’s ${total}M revenue jump"
SHAPLEY = "Shapley split: each driver’s average effect across both orders."
BRIDGE_ID = "2024-09-30_to_2024-12-31"
SOURCE_IDS = ("OBS-2024Q3-REV-ORIG", "OBS-2024Q4-REV-ORIG")

# name -> (height px, title px, plot height px, padding px)
CARDS = {"landscape": (640, 40, 286, 32), "square": (1024, 54, 580, 48)}


def money(value):
    return f"${fmt_value(str(value))}M"


def load_figures():
    """Return the four bridge values (Decimal, one decimal) and the data date."""
    with open(PKG / "descriptive-bridge.csv", newline="") as f:
        bridge = next(r for r in csv.DictReader(f) if r["comparison_id"] == BRIDGE_ID)
    with open(PKG / "bridge-attribution.csv", newline="") as f:
        shapley = next(r for r in csv.DictReader(f) if r["method"] == "Symmetric Shapley")
    with open(PKG / "analytics-ready-metrics.csv", newline="") as f:
        rows = {r["observation_id"]: r for r in csv.DictReader(f)}
    start = Decimal(bridge["from_revenue_mm"]).quantize(ONE, ROUND_HALF_UP)
    end = Decimal(bridge["to_revenue_mm"]).quantize(ONE, ROUND_HALF_UP)
    volume = Decimal(shapley["volume_effect_mm"]).quantize(ONE, ROUND_HALF_UP)
    yield_ = Decimal(shapley["yield_effect_mm"]).quantize(ONE, ROUND_HALF_UP)
    if start + volume + yield_ != end:
        raise SystemExit(f"printed numbers do not add up: {start} + {volume} + {yield_} != {end}")
    if rows[SOURCE_IDS[0]]["value_decimal"] != str(start) or rows[SOURCE_IDS[1]]["value_decimal"] != str(end):
        raise SystemExit("bridge endpoints disagree with analytics-ready-metrics.csv")
    as_of = max(rows[i]["published_at"] for i in SOURCE_IDS)[:10]
    return {"start": start, "volume": volume, "yield": yield_, "end": end, "as_of": as_of}


def title_text(fig):
    return TITLE.format(volume=fmt_value(str(fig["volume"])), total=fmt_value(str(fig["volume"] + fig["yield"])))


def alt_text(fig):
    return (
        f"Waterfall chart of Coinbase consumer transaction revenue in $M: {money(fig['start'])} in Q3 2024, "
        f"plus a {money(fig['volume'])} volume effect (highlighted in red), plus a {money(fig['yield'])} yield "
        f"effect, equals {money(fig['end'])} in Q4 2024. {SHAPLEY}"
    )


def footer_text(fig):
    return f"Source: Coinbase SEC filings, Q3 and Q4 2024. Data as of {month_day_year(fig['as_of'])}."


def bars(fig):
    """(label, base, size, value text, highlighted) for each waterfall step, in $M."""
    s, v, y, e = (float(fig[k]) for k in ("start", "volume", "yield", "end"))
    return [
        ("Q3 2024", 0, s, money(fig["start"]), False),
        ("Volume", s, v, "+" + money(fig["volume"]), True),
        ("Yield", s + v, y, "+" + money(fig["yield"]), False),
        ("Q4 2024", 0, e, money(fig["end"]), False),
    ]


def build_html(name, fig):
    height, title_px, plot_px, pad = CARDS[name]
    steps = bars(fig)
    top = max(base + size for _, base, size, _, _ in steps)
    k = plot_px / top
    n = len(steps)
    cols, links = [], []
    for i, (label, base, size, text, hi) in enumerate(steps):
        cols.append(
            f'<div class="col{" hi" if hi else ""}">'
            f'<span class="val" style="bottom:{(base + size) * k + 6:.2f}px">{html.escape(text)}</span>'
            f'<div class="bar" style="bottom:{base * k:.2f}px;height:{max(size * k, 1):.2f}px"></div>'
            f'<span class="q">{label}</span></div>'
        )
        if i < n - 1:  # thin level line from this bar's running total to the next bar
            links.append(
                f'<div class="link" style="left:calc({(i + 0.85) * 100 / n:.3f}%);width:calc({0.3 * 100 / n:.3f}%);'
                f'bottom:{(base + size) * k:.2f}px"></div>'
            )
    source = footer_text(fig)
    title = title_text(fig)
    alt = alt_text(fig)
    fonts = (
        font_face("Roboto Slab", 700, "roboto-slab-latin-700-normal.woff2")
        + font_face("Archivo", 400, "archivo-latin-400-normal.woff2")
        + font_face("Archivo", 600, "archivo-latin-600-normal.woff2")
    )
    big = name == "square"
    return f"""<!doctype html><html lang="en"><meta charset="utf-8"><title>{html.escape(title)}</title>
<style>{fonts}
*{{box-sizing:border-box;margin:0}}
html,body{{width:{WIDTH}px;height:{height}px;background:#fff;color:{NAVY};overflow:hidden}}
.card{{width:{WIDTH}px;height:{height}px;padding:{pad}px {pad}px {pad - 8}px;display:flex;flex-direction:column;
  font:400 {MIN_PX}px/1.25 Archivo,sans-serif}}
h1{{font:700 {title_px}px/1.15 'Roboto Slab',serif;letter-spacing:-.01em}}
.def{{font-weight:600;font-size:28px;white-space:nowrap;margin-top:{18 if big else 10}px}}
.plot{{position:relative;height:{plot_px + (56 if big else 52)}px;margin-top:{16 if big else 6}px;padding-top:{56 if big else 52}px;border-bottom:3px solid {NAVY}}}
.plot-in{{position:absolute;left:0;right:0;bottom:0;height:{plot_px}px}}
.col{{position:absolute;top:0;bottom:0;width:{100 / n:.3f}%;}}
{"".join(f".col:nth-child({i + 1}){{left:{i * 100 / n:.3f}%}}" for i in range(n))}
.bar{{position:absolute;left:15%;width:70%;background:{NAVY}}}
.hi .bar{{background:{RED}}}
.val{{position:absolute;left:0;right:0;text-align:center;font-weight:600;font-size:{34 if big else 32}px;white-space:nowrap;line-height:1.1}}
.hi .val{{color:{RED}}}
.link{{position:absolute;height:2px;background:{NAVY};opacity:.55}}
.q{{position:absolute;top:100%;left:0;right:0;text-align:center;margin-top:8px;font-weight:600;font-size:28px;white-space:nowrap}}
.hi .q{{color:{RED}}}
.foot{{margin-top:auto;font-size:{MIN_PX}px;white-space:nowrap}}
.qpad{{height:{28 * 1.25 + 8:.0f}px;margin-top:{4 if big else 2}px}}
</style>
<div class="card" role="img" aria-label="{html.escape(alt)}">
<h1>{html.escape(title)}</h1>
<div class="def">{html.escape(SHAPLEY)}</div>
<div class="plot"><div class="plot-in">{"".join(cols)}{"".join(links)}</div></div>
<div class="qpad"></div>
<div class="foot">{html.escape(source)}</div>
</div>
<script>
document.fonts.ready.then(()=>{{
  const out={{minPx:99,fonts:[],issues:[]}};
  const card=document.querySelector('.card');
  const w=document.createTreeWalker(card,NodeFilter.SHOW_TEXT);
  for(let n;n=w.nextNode();){{
    if(!n.textContent.trim())continue;
    const el=n.parentElement,cs=getComputedStyle(el);
    out.minPx=Math.min(out.minPx,parseFloat(cs.fontSize));
    const f=cs.fontFamily.split(',')[0].replace(/['"]/g,'');
    if(!out.fonts.includes(f))out.fonts.push(f);
    if(el.scrollWidth>el.clientWidth+1)out.issues.push('overflow-x: '+n.textContent);
  }}
  const lines=sel=>{{const r=document.createRange();r.selectNodeContents(document.querySelector(sel));
    return new Set([...r.getClientRects()].map(q=>Math.round(q.top))).size;}};
  out.defLines=lines('.def');out.footLines=lines('.foot');
  out.defText=document.querySelector('.def').textContent;out.footText=document.querySelector('.foot').textContent;
  out.defBeforeChart=document.querySelector('.def').getBoundingClientRect().bottom<=document.querySelector('.plot').getBoundingClientRect().top;
  out.vals=[...document.querySelectorAll('.val')].map(e=>e.textContent);
  const cb=card.getBoundingClientRect();
  card.querySelectorAll('*').forEach(e=>{{const b=e.getBoundingClientRect();
    if(b.right>cb.right+0.5||b.bottom>cb.bottom+0.5||b.left<-0.5||b.top<-0.5)out.issues.push('outside card: '+e.className+' '+e.textContent.slice(0,20));}});
  const labels=[...document.querySelectorAll('.val,.q,.def,.foot,h1')].map(e=>[e,e.getBoundingClientRect()]);
  for(let i=0;i<labels.length;i++)for(let j=i+1;j<labels.length;j++){{const a=labels[i][1],b=labels[j][1];
    if(a.left<b.right&&b.left<a.right&&a.top<b.bottom&&b.top<a.bottom)out.issues.push('overlap '+labels[i][0].className+'/'+labels[j][0].className);}}
  const bs=[...document.querySelectorAll('.bar')].map(e=>e.getBoundingClientRect());
  const vs=[...document.querySelectorAll('.val')].map(e=>e.getBoundingClientRect());
  bs.forEach((b,i)=>{{if(vs[i].bottom>b.top+0.5)out.issues.push('label touches bar '+i);}});
  const q=document.querySelector('.q').getBoundingClientRect(),ft=document.querySelector('.foot').getBoundingClientRect();
  if(q.bottom>ft.top)out.issues.push('axis labels overlap footer');
  out.fontsLoaded=['700 20px "Roboto Slab"','400 20px Archivo','600 20px Archivo'].every(s=>document.fonts.check(s));
  document.title='CHECK:'+JSON.stringify(out);
}});
</script></html>"""


def check(page_path):
    dom = chromium("--virtual-time-budget=5000", "--dump-dom", f"file://{page_path}").stdout
    m = re.search(r"<title>CHECK:(.*?)</title>", dom, re.S)
    return json.loads(html.unescape(m.group(1))) if m else None


def png_size(path):
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise SystemExit(f"{path} is not a PNG")
    return struct.unpack(">II", data[16:24])


def passes(res, fig):
    expected_vals = [t for _, _, _, t, _ in bars(fig)]
    return (
        res is not None and res["minPx"] >= MIN_PX and res["defLines"] == 1 and res["footLines"] == 1
        and res["defText"] == SHAPLEY and res["footText"] == footer_text(fig) and res["defBeforeChart"]
        and res["vals"] == expected_vals and all(re.fullmatch(r"\+?\$[\d,]+\.\dM", v) for v in res["vals"])
        and not res["issues"] and res["fontsLoaded"] and set(res["fonts"]) == {"Roboto Slab", "Archivo"}
    )


def main():
    fig = load_figures()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    alt = alt_text(fig)
    (OUT_DIR / "alt-text.txt").write_text(alt + "\n")
    failed, files = False, {}
    with tempfile.TemporaryDirectory(prefix="rb-card-") as tmp:
        for name, (height, *_rest) in CARDS.items():
            page = Path(tmp) / f"{name}.html"
            page.write_text(build_html(name, fig))
            res = check(page)
            ok = passes(res, fig)
            png = OUT_DIR / f"revenue-bridge-card-{name}.png"
            png.unlink(missing_ok=True)
            chromium("--virtual-time-budget=5000", f"--window-size={WIDTH},{height}", f"--screenshot={png}", f"file://{page}")
            if not png.exists():
                sys.exit(f"chromium did not write {png}")
            size = png_size(png)
            ok = ok and size == (WIDTH, height)
            print(f"{name}: {'PASS' if ok else 'FAIL'} {size[0]}x{size[1]} {json.dumps(res)}")
            failed |= not ok
            files[png.name] = {
                "width": size[0], "height": size[1],
                "sha256": hashlib.sha256(png.read_bytes()).hexdigest(),
            }
    manifest = {
        "script": "scripts/build_revenue_bridge_card.py",
        "design_review": "pending: navy/red, Roboto Slab and Archivo follow the request, not rahil-design 3.3.1; see DESIGN.md",
        "numbers_usd_mm": {k: str(fig[k]) for k in ("start", "volume", "yield", "end")},
        "title": title_text(fig),
        "shapley_line": SHAPLEY,
        "footer": footer_text(fig),
        "alt_text": alt,
        "files": files,
    }
    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    for n, f in files.items():
        print(f"{f['sha256']}  {n}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
