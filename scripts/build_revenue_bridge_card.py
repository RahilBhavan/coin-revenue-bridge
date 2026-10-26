#!/usr/bin/env python3
"""Render the revenue bridge card (1080x1080) to outputs/revenue-bridge-card/ in the Rahil Design system.

The card is the Q3 to Q4 2024 consumer transaction revenue bridge: start, volume effect, yield effect,
end, each printed in $M to one decimal. Start and end come from descriptive-bridge.csv and the symmetric
Shapley split from bridge-attribution.csv. The script refuses to render unless the printed numbers add up
(483.3 + 856.4 + 7.4 = 1,347.1) and agree with analytics-ready-metrics.csv.

The page is authored at 390x390 CSS px with 22px labels and a 48px title, the phone-feed floors of
Rahil Design (18px labels in a 326px feed box), then screenshotted at 1080/390 so the PNG is 1080x1080.
Colours and fonts are the tokens and bundled fonts in scripts/card-fonts/rahil/. Per-card checks come from
rahil-design's social_bars.py (RAHIL_DESIGN_SCRIPTS, default: the hub's skill folder), so the same
in-page gate runs: font sizes, overflow, fonts drawn, glyph coverage, contrast and hidden-text tricks.

    uv run --with playwright==1.63.0 --with fonttools --with pillow --with numpy \
        python3 scripts/build_revenue_bridge_card.py

Writes the square PNG, card.html, alt-text.txt, feed-360.png, feed-390.png (the card scaled into a phone
feed box), brief.json (input for rahil-design's `design_check.py feed`) and manifest.json (SHA-256 of
every artifact). Exits 1 if any check fails. Rendering twice gives identical bytes.
"""
import base64
import csv
import hashlib
import html
import json
import os
import sys
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PKG = ROOT / "outputs/final-package"
OUT_DIR = ROOT / "outputs/revenue-bridge-card"
RAHIL = ROOT / "scripts/card-fonts/rahil"
DESIGN_SCRIPTS = Path(
    os.environ.get("RAHIL_DESIGN_SCRIPTS", "/home/rahil/.t3/projects/main/.agents/skills/rahil-design/scripts")
)

SIZE, OUT_PX, LABEL_PX, TITLE_PX = 390, 1080, 22, 48
FEED_BOXES = {"feed-360": (360, 326), "feed-390": (390, 356)}  # frame width, card width inside it
ONE = Decimal("0.1")
BRIDGE_ID = "2024-09-30_to_2024-12-31"
SOURCE_IDS = ("OBS-2024Q3-REV-ORIG", "OBS-2024Q4-REV-ORIG")
SHAPLEY = "Shapley: average of both orders."
MIN_BAR_PX = 2  # the yield effect is 0.5% of the scale; keep it visible as a hairline, not 0px


def fmt_value(text):
    whole, _, frac = text.partition(".")
    return f"{int(whole):,}" + (f".{frac}" if frac else "")


def money(value):
    return f"${fmt_value(str(value))}M"


def month_day_year(iso):
    y, m, d = iso.split("-")
    names = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()
    return f"{names[int(m) - 1]} {int(d)}, {y}"


def load_figures():
    """Return the four bridge values (Decimal, one decimal) and the data date (latest filing used)."""
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
    return f"Volume: {money(fig['volume'])} of {money(fig['volume'] + fig['yield'])}"


def footer_text(fig):
    return f"Source: Coinbase SEC filings. Data as of {month_day_year(fig['as_of'])}."


def alt_text(fig):
    """One paragraph that says what the card shows, in the card's own words and numbers."""
    return (
        f"Bar chart of Coinbase consumer transaction revenue in $M, Q3 to Q4 2024. Title: {title_text(fig)}. "
        f"Q3 2024 revenue was {money(fig['start'])}. The volume effect added {money(fig['volume'])}, highlighted in "
        f"yellow, and the yield effect added {money(fig['yield'])}, a hairline-thin bar, so the two effects make up the "
        f"{money(fig['volume'] + fig['yield'])} increase to {money(fig['end'])} in Q4 2024. {SHAPLEY} {footer_text(fig)}"
    )


def steps(fig):
    """(label, offset $M, size $M, value text, highlighted) for each waterfall row."""
    s, v, y, e = (float(fig[k]) for k in ("start", "volume", "yield", "end"))
    return [
        ("Q3 2024", 0.0, s, money(fig["start"]), False),
        ("Volume", s, v, "+" + money(fig["volume"]), True),
        ("Yield", s + v, y, "+" + money(fig["yield"]), False),
        ("Q4 2024", 0.0, e, money(fig["end"]), False),
    ]


def card_html(fig):
    tokens = json.loads((RAHIL / "tokens.json").read_text())
    c, ch = tokens["color"], tokens["chart"]
    font = lambda n: base64.b64encode((RAHIL / n).read_bytes()).decode()
    rows = []
    top = max(off + size for _, off, size, _, _ in steps(fig))
    for label, off, size, text, hi in steps(fig):
        left, width = 100 * off / top, 100 * size / top
        cls = "bar hi" if hi else "bar"
        rows.append(
            f'<div class="row"><div class="line"><span>{html.escape(label)}</span><span>{html.escape(text)}</span></div>'
            f'<div class="track"><span class="{cls}" style="margin-left:{left:.3f}%;width:max({MIN_BAR_PX}px,{width:.3f}%)"></span></div></div>'
        )
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{html.escape(title_text(fig))}</title><style>
@font-face{{font-family:'Rahil Display';src:url(data:font/ttf;base64,{font('Anton-Regular.ttf')})}}
@font-face{{font-family:'Rahil Plex';src:url(data:font/ttf;base64,{font('IBMPlexSans-Regular.ttf')})}}
@font-face{{font-family:'Rahil Plex';font-weight:600;src:url(data:font/ttf;base64,{font('IBMPlexSans-SemiBold.ttf')})}}
*{{box-sizing:border-box}}html,body{{margin:0}}
body{{width:{SIZE}px;height:{SIZE}px;background:{c['canvas']};color:{c['ink']};font-family:'Rahil Plex',sans-serif}}
article{{width:{SIZE}px;height:{SIZE}px;padding:20px;display:grid;grid-template-rows:auto auto minmax(0,1fr) auto;gap:8px}}
h1{{font:{TITLE_PX}px/1.0 'Rahil Display',sans-serif;margin:0;text-transform:uppercase;overflow-wrap:anywhere}}
.def{{margin:0;font-size:{LABEL_PX}px;line-height:1.15;color:{c['secondary']};white-space:nowrap}}
.figure{{background:{c['figure-surface']};color:{c['figure-ink']};border-radius:{tokens['radius_panel_px']}px;padding:8px 12px;display:flex;
flex-direction:column;justify-content:space-between;font-size:{LABEL_PX}px;line-height:1;font-variant-numeric:tabular-nums}}
.line{{display:flex;justify-content:space-between;white-space:nowrap}}
.track{{display:block;height:8px;margin-top:2px}}
.bar{{display:block;height:8px;background:{ch['series-3']}}}
.bar.hi{{background:{ch['highlight']};outline:2px solid {ch['series-1']};outline-offset:-2px}}
.source{{margin:0;font-size:{LABEL_PX}px;line-height:1.15;color:{c['secondary']}}}
</style></head><body><article><h1>{html.escape(title_text(fig))}</h1>
<p class="def">{html.escape(SHAPLEY)}</p>
<div class="figure">{''.join(rows)}</div>
<p class="source">{'<br>'.join(html.escape(part) for part in footer_text(fig).split('. ', 1))}</p></article></body></html>"""


def load_design_scripts():
    if not (DESIGN_SCRIPTS / "social_bars.py").exists():
        raise SystemExit(f"rahil-design scripts not found at {DESIGN_SCRIPTS}; set RAHIL_DESIGN_SCRIPTS")
    sys.path.insert(0, str(DESIGN_SCRIPTS))
    import social_bars
    return social_bars


def render(sb, html_path, png_path):
    """Screenshot the 390px page at 1080/390 device scale (a 1080x1080 PNG) and return its measurements."""
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=True, executable_path=str(sb.FIREFOX))
        page = browser.new_page(viewport={"width": SIZE, "height": SIZE}, device_scale_factor=OUT_PX / SIZE)
        page.goto(Path(html_path).resolve().as_uri())
        page.evaluate("document.fonts.ready")
        page.wait_for_timeout(300)
        measured = page.evaluate(sb.MEASURE)
        measured["definition_lines"] = page.evaluate(
            "Math.round(document.querySelector('.def').getBoundingClientRect().height / "
            "parseFloat(getComputedStyle(document.querySelector('.def')).lineHeight))")
        measured["source_lines"] = page.evaluate(
            "Math.round(document.querySelector('.source').getBoundingClientRect().height / "
            "parseFloat(getComputedStyle(document.querySelector('.source')).lineHeight))")
        page.screenshot(path=str(png_path))
        browser.close()
    return measured


def feed_frames(png, out_dir):
    """Scale the card into the feed box of a 360px and a 390px phone and save each frame (1x CSS px)."""
    from PIL import Image
    canvas = tuple(int(json.loads((RAHIL / "tokens.json").read_text())["color"]["canvas"][i:i + 2], 16) for i in (1, 3, 5))
    card = Image.open(png).convert("RGB")
    for name, (frame, box) in FEED_BOXES.items():
        image = Image.new("RGB", (frame, frame), canvas)
        image.paste(card.resize((box, box), Image.BILINEAR), ((frame - box) // 2, (frame - box) // 2))
        image.save(out_dir / f"{name}.png")


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    fig = load_figures()
    sb = load_design_scripts()
    out = OUT_DIR
    out.mkdir(parents=True, exist_ok=True)
    markup = card_html(fig)
    (out / "card.html").write_text(markup)
    png = out / "revenue-bridge-card-square.png"
    m = render(sb, out / "card.html", png)

    sizes = [px for _, px in m["sizes"]]
    errors = [f"overflow: {o}" for o in m["overflow"]] + [f"font {f!r} is not a token font" for f in set(m["fonts"])]
    errors += [f"no glyph for {g}; spell it out" for g in sb.missing_glyphs(m["glyphs"])] + sb.face_errors(m["faces"])
    errors += [f"text below {LABEL_PX}px"] * (min(sizes) < LABEL_PX)
    errors += [f"title wraps to {m['title_lines']} lines, not 2"] * (m["title_lines"] != 2)
    errors += [f"definition wraps to {m['definition_lines']} lines"] * (m["definition_lines"] != 1)
    errors += [f"source note wraps to {m['source_lines']} lines, not 2"] * (m["source_lines"] != 2)
    for label, _, _, text, _ in steps(fig):
        errors += [f"bar label {text!r} lacks $ or M"] * (not (text.lstrip("+").startswith("$") and text.endswith("M")))
    from PIL import Image
    errors += [f"PNG is {Image.open(png).size}, not {OUT_PX}x{OUT_PX}"] * (Image.open(png).size != (OUT_PX, OUT_PX))
    feed_frames(png, out)

    alt = alt_text(fig)
    (out / "alt-text.txt").write_text(alt + "\n")
    tokens = json.loads((RAHIL / "tokens.json").read_text())
    brief = {
        "id": "revenue-bridge-card", "title": title_text(fig), "system_version": tokens["version"], "accents": 1,
        "accent_meaning": "title-value",
        "encodings": [{"mark": "bar", "baseline": 0, "scale_max": float(fig["end"])}],
        "sizes_checked": [f"{SIZE}x{SIZE}"],
        "feed_frames": {name: f"{box}px card in a {frame}px phone frame" for name, (frame, box) in FEED_BOXES.items()},
        "measurement_basis": "canvas", "measured_by": "build_revenue_bridge_card/social_bars MEASURE (firefox)",
        "min_label_px": min(sizes), "point_px": max(sizes), "title_lines": m["title_lines"],
        "overflow": m["overflow"], "source": footer_text(fig), "alt": alt,
    }
    (out / "brief.json").write_text(json.dumps(brief, indent=2) + "\n")
    manifest = {
        "design_system": f"rahil-design {tokens['version']} (tokens.json sha256 {tokens['tokens_json_sha256']})",
        "review_status": "design review pending",
        "authored_px": SIZE, "output_px": OUT_PX,
        "artifacts": {n: sha256(out / n) for n in (
            "revenue-bridge-card-square.png", "card.html", "feed-360.png", "feed-390.png", "alt-text.txt", "brief.json")},
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"{png}: labels {min(sizes)}px, title {max(sizes)}px, {m['title_lines']} title lines; " + ("; ".join(errors) or "ok"))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
