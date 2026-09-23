#!/usr/bin/env python3
"""Render deterministic 1280×720 captioned PNG frames for the evidence demo."""

from __future__ import annotations

import csv
import textwrap
from decimal import Decimal
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
FRAME_DIR = ROOT / "work" / "demo-frames"
FONT = Path("/System/Library/Fonts/Supplemental/Arial.ttf")
FONT_BOLD = Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf")


def font(size: int, bold: bool = False):
    return ImageFont.truetype(str(FONT_BOLD if bold else FONT), size)


def wrapped(draw, xy, text, size, width, color, bold=False, spacing=10):
    chars = max(12, int(width / (size * .54)))
    draw.multiline_text(xy, textwrap.fill(text, chars), font=font(size, bold), fill=color, spacing=spacing)


def base(kicker: str, title: str, caption: str):
    image = Image.new("RGB", (1280, 720), "#071021")
    draw = ImageDraw.Draw(image)
    draw.ellipse((930, -250, 1450, 270), fill="#102a56")
    draw.text((74, 48), kicker.upper(), font=font(17, True), fill="#5de4ff")
    wrapped(draw, (74, 88), title, 54, 1080, "#eef3ff", True, 8)
    draw.rectangle((0, 692, 1280, 720), fill="#1652f0")
    draw.rectangle((74, 615, 1206, 682), fill="#040a15")
    wrapped(draw, (98, 630), caption, 20, 1080, "#eef3ff", False, 4)
    return image, draw


def card(draw, box, label, value, color="#5de4ff", note=""):
    draw.rounded_rectangle(box, 18, fill="#101d35", outline="#294067", width=2)
    x0, y0, x1, _ = box
    draw.text((x0 + 24, y0 + 22), label, font=font(18, True), fill="#aebbd4")
    draw.text((x0 + 24, y0 + 65), value, font=font(39, True), fill=color)
    if note:
        wrapped(draw, (x0 + 24, y0 + 122), note, 16, x1 - x0 - 48, "#aebbd4", False, 4)


def main():
    with (ROOT / "work/real-reporting-inputs/processed_metrics.csv").open(newline="", encoding="utf-8") as handle:
        metrics = list(csv.DictReader(handle))
    with (ROOT / "work/real-reporting-inputs/descriptive_bridge.csv").open(newline="", encoding="utf-8") as handle:
        row = next(csv.DictReader(handle))
    r0, r1 = Decimal(row["from_revenue_mm"]), Decimal(row["to_revenue_mm"])
    v0, v1 = Decimal(row["from_volume_bn"]), Decimal(row["to_volume_bn"])
    y0, y1 = Decimal(row["from_yield_pct"]), Decimal(row["to_yield_pct"])
    change = r1 - r0
    vol = (v1 - v0) * y0 * Decimal(10)
    yld = v1 * (y1 - y0) * Decimal(10)
    alt_vol = (v1 - v0) * y1 * Decimal(10)
    alt_yld = v0 * (y1 - y0) * Decimal(10)
    shapley_vol = (vol + alt_vol) / Decimal(2)
    shapley_yld = (yld + alt_yld) / Decimal(2)

    frames = []
    im, d = base("Strategic Finance · public evidence", "Explain the change.\nDon’t invent a forecast.", "The public evidence supported a narrower—and more defensible—decision tool.")
    d.rounded_rectangle((74, 410, 535, 475), 10, outline="#ffc857", width=3); d.text((94, 427), "DESCRIPTIVE / NOT A FORECAST", font=font(22, True), fill="#ffc857"); frames.append(im)

    im, d = base("1 · Evidence before output", "Thirteen SEC sources. Every source frozen and hashed.", "The twelve-quarter forecast gate failed, so no forecast accuracy is claimed.")
    card(d, (74, 280, 410, 495), "REGISTERED SOURCES", "13", note="Frozen local SEC copies")
    card(d, (440, 280, 776, 495), "SOURCE OBSERVATIONS", "20", note="Original and recast vintages")
    card(d, (806, 280, 1206, 495), "FORECAST GATE", "9 / 12", "#ffc857", "Not enough comparable quarters")
    frames.append(im)

    im, d = base("2 · Definition control", "Definition changes are part of the model.", "Original and recast values stay distinct. Later quarters are crosswalked and quarantined.")
    card(d, (74, 250, 430, 480), "ORIGINAL Q3 ’23", "$274.5M", "#ff6b79", "Included Base and payments-related revenue")
    card(d, (462, 250, 818, 480), "RECAST Q3 ’23", "$247.0M", "#5de4ff", "Post-reclassification presentation")
    card(d, (850, 250, 1206, 480), "Q2–Q4 ’25 RECASTS", "-$1.5B to -$2.3B", "#ffc857", "Later volume vintages")
    frames.append(im)

    im, d = base("3 · Historical trend", "Consumer transaction revenue is volatile.", "This is a historical view, not an extrapolation. USD millions; comparable recast series.")
    vals = [Decimal(x["consumer_transaction_revenue_mm"]) for x in metrics]; labels = [x["period_end"][:7] for x in metrics]; maximum=max(vals)
    pts=[]
    for i,value in enumerate(vals):
        x=100+i*1080/(len(vals)-1); y=520-float(value/maximum)*250; pts.append((x,y))
    d.line(pts, fill="#5de4ff", width=6, joint="curve")
    for i,(x,y) in enumerate(pts):
        d.ellipse((x-6,y-6,x+6,y+6), fill="#ffc857"); d.text((x-29,540), labels[i], font=font(12), fill="#aebbd4")
    frames.append(im)

    im, d = base("4 · Q3 → Q4 2024 bridge", f"+${change:.1f}M reported revenue change", "Under the disclosed volume-first identity, $852.9M is associated with volume and $10.9M with effective yield.")
    card(d, (74, 260, 430, 505), "VOLUME-ASSOCIATED", f"${vol:.1f}M", "#5de4ff", f"{vol/change*100:.1f}% of the change")
    card(d, (462, 260, 818, 505), "EFFECTIVE-YIELD", f"${yld:.1f}M", "#ffc857", "Calculated proxy—not a fee rate")
    card(d, (850, 260, 1206, 505), "ROUNDED RESIDUAL", "$0.0M", "#eef3ff", "Reconciles within $0.1M")
    frames.append(im)

    im, d = base("5 · Planning layer", "Test assumptions.\nDo not assign fake probabilities.", "These are editable sensitivities, not Coinbase guidance or expected outcomes.")
    card(d, (74, 260, 430, 495), "DOWNSIDE", "$1,002.5M", "#ff6b79", "-20% volume; -10 bps yield")
    card(d, (462, 260, 818, 495), "REFERENCE", "$1,347.1M", "#5de4ff", "Q4 2024 actual inputs")
    card(d, (850, 260, 1206, 495), "UPSIDE", "$1,729.3M", "#ffc857", "+20% volume; +10 bps yield"); frames.append(im)

    im, d = base("6 · Strongest objection", "The allocation depends on bridge order.", "Changing the order moves about $7.0M between components while leaving the $863.8M total unchanged.")
    card(d, (74, 260, 430, 495), "VOLUME-FIRST", f"${vol:.1f}M", "#5de4ff", "volume effect")
    card(d, (462, 260, 818, 495), "YIELD-FIRST", f"${alt_vol:.1f}M", "#71a0ff", "volume effect")
    card(d, (850, 260, 1206, 495), "SYMMETRIC SHAPLEY", f"${shapley_vol:.1f}M", "#ffc857", f"Volume; yield ${shapley_yld:.1f}M")
    frames.append(im)

    im, d = base("Verdict", "A small model with\nstrong epistemics.", "Reproducible, auditable, decision-useful—and bounded by what public evidence can support.")
    d.rounded_rectangle((74, 410, 535, 475), 10, outline="#ffc857", width=3); d.text((94, 427), "DESCRIPTIVE / NOT A FORECAST", font=font(22, True), fill="#ffc857"); frames.append(im)

    FRAME_DIR.mkdir(parents=True, exist_ok=True)
    for index, image in enumerate(frames, 1):
        image.save(FRAME_DIR / f"slide-{index:02d}.png", optimize=True)
    print(f"rendered {len(frames)} frames to {FRAME_DIR}")


if __name__ == "__main__":
    main()
