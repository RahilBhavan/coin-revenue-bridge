#!/usr/bin/env python3
"""Build the self-contained, timed HTML demo from reviewed CSV inputs."""

from __future__ import annotations

import csv
import html
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "final-package"
METRICS = ROOT / "work" / "real-reporting-inputs" / "processed_metrics.csv"
BRIDGE = ROOT / "work" / "real-reporting-inputs" / "descriptive_bridge.csv"


def esc(value: object) -> str:
    return html.escape(str(value))


def main() -> None:
    with METRICS.open(newline="", encoding="utf-8") as handle:
        metrics = list(csv.DictReader(handle))
    with BRIDGE.open(newline="", encoding="utf-8") as handle:
        row = next(csv.DictReader(handle))

    revenue = [Decimal(r["consumer_transaction_revenue_mm"]) for r in metrics]
    volume = [Decimal(r["consumer_trading_volume_bn"]) for r in metrics]
    labels = [r["period_end"][:7] for r in metrics]
    width, height, pad = 920, 300, 46
    maximum = max(revenue)
    points = []
    for index, value in enumerate(revenue):
        x = pad + index * (width - pad * 2) / (len(revenue) - 1)
        y = height - pad - float(value / maximum) * (height - pad * 2)
        points.append((x, y))
    polyline = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
    dots = "".join(
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5"><title>{esc(labels[i])}: ${revenue[i]:,.1f}M</title></circle>'
        for i, (x, y) in enumerate(points)
    )
    xlabels = "".join(
        f'<text x="{x:.1f}" y="282" text-anchor="middle">{esc(labels[i])}</text>'
        for i, (x, _) in enumerate(points)
    )

    r0, r1 = Decimal(row["from_revenue_mm"]), Decimal(row["to_revenue_mm"])
    v0, v1 = Decimal(row["from_volume_bn"]), Decimal(row["to_volume_bn"])
    y0, y1 = Decimal(row["from_yield_pct"]), Decimal(row["to_yield_pct"])
    change = r1 - r0
    volume_effect = (v1 - v0) * y0 * Decimal(10)
    yield_effect = v1 * (y1 - y0) * Decimal(10)
    alt_yield = v0 * (y1 - y0) * Decimal(10)
    alt_volume = (v1 - v0) * y1 * Decimal(10)
    allocation_shift = abs(volume_effect - alt_volume)
    shapley_volume = (volume_effect + alt_volume) / Decimal(2)
    shapley_yield = (yield_effect + alt_yield) / Decimal(2)

    document = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Coinbase Strategic Finance — three-minute evidence demo</title>
<style>
:root{{--ink:#eef3ff;--muted:#aebbd4;--blue:#1652f0;--cyan:#5de4ff;--gold:#ffc857;--bg:#071021;--panel:#101d35;--red:#ff6b79}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--bg);color:var(--ink);font:18px/1.45 Inter,ui-sans-serif,system-ui,-apple-system,sans-serif;overflow:hidden}}
.slide{{position:absolute;inset:0;padding:6vh 7vw 13vh;opacity:0;transform:translateY(16px);transition:.55s ease;pointer-events:none;background:radial-gradient(circle at 85% 15%,#17366b66,transparent 35%),var(--bg)}}
.slide.active{{opacity:1;transform:none;pointer-events:auto}} .eyebrow{{color:var(--cyan);font-weight:800;letter-spacing:.16em;text-transform:uppercase;font-size:.72rem}}
h1{{font-size:clamp(2.8rem,6vw,6.2rem);line-height:.96;max-width:1100px;margin:.25em 0}} h2{{font-size:clamp(2.2rem,4.2vw,4.5rem);line-height:1.05;margin:.2em 0 .5em;max-width:1100px}}
.lede{{font-size:clamp(1.25rem,2.2vw,2rem);max-width:980px;color:var(--muted)}} .label{{display:inline-block;padding:.5rem .75rem;border:2px solid var(--gold);color:var(--gold);font-weight:900;letter-spacing:.08em}}
.grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:1.3rem;max-width:1100px}} .card{{background:var(--panel);border:1px solid #294067;border-radius:18px;padding:1.25rem}}
.num{{font-size:clamp(2rem,4vw,4rem);font-weight:850;letter-spacing:-.04em}} .blue{{color:#71a0ff}} .cyan{{color:var(--cyan)}} .gold{{color:var(--gold)}} .red{{color:var(--red)}}
.chart{{max-width:1050px;background:#0d1a30;border-radius:18px;padding:1rem}} svg{{width:100%;height:auto}} svg polyline{{fill:none;stroke:var(--cyan);stroke-width:5}} svg circle{{fill:var(--gold)}} svg text{{fill:var(--muted);font-size:12px}}
.bar{{height:36px;border-radius:9px;margin:.75rem 0;background:#1f3151;overflow:hidden}} .bar span{{height:100%;display:block;background:linear-gradient(90deg,var(--blue),var(--cyan))}} .bar.yield span{{background:var(--gold)}}
.caption{{position:absolute;left:7vw;right:7vw;bottom:5vh;padding:1rem 1.2rem;background:#000b;border-left:5px solid var(--cyan);font-size:clamp(.95rem,1.5vw,1.3rem)}}
#chrome{{position:fixed;left:0;right:0;bottom:0;height:8px;background:#23324e;z-index:20}} #progress{{height:100%;width:0;background:linear-gradient(90deg,var(--blue),var(--cyan))}}
#controls{{position:fixed;right:2vw;top:2vh;z-index:30;display:flex;gap:.5rem}} button{{background:#132543;color:var(--ink);border:1px solid #39527c;border-radius:999px;padding:.55rem .8rem;cursor:pointer}} button:hover{{background:#1c3762}}
.small{{font-size:.9rem;color:var(--muted)}} .callout{{border-left:6px solid var(--gold);padding:1rem 1.3rem;background:#ffc85713;max-width:980px;font-size:1.35rem}} .equation{{font:700 clamp(1.3rem,2.5vw,2.4rem)/1.3 ui-monospace,SFMono-Regular,monospace}}
@media(max-width:800px){{.grid{{grid-template-columns:1fr}}.slide{{overflow:auto;padding-bottom:18vh}}}}
</style></head><body>
<div id="controls"><button id="prev" aria-label="Previous slide">←</button><button id="play">Pause</button><button id="next" aria-label="Next slide">→</button></div>
<section class="slide active" data-seconds="15"><div class="eyebrow">Strategic Finance · Public evidence · 2026-09-20 cutoff</div><h1>Explain the change.<br><span class="cyan">Don’t invent a forecast.</span></h1><p class="lede">A reproducible revenue bridge built only after the evidence gate rejected a forecast tournament.</p><div class="label">DESCRIPTIVE / NOT A FORECAST</div><div class="caption">The project began with a forecasting ambition. The public evidence supported a narrower—and more defensible—decision tool.</div></section>
<section class="slide" data-seconds="23"><div class="eyebrow">1 · Evidence before output</div><h2>Thirteen SEC sources.<br>Every source frozen and hashed.</h2><div class="grid"><div class="card"><div class="num blue">13</div>registered SEC sources</div><div class="card"><div class="num cyan">20</div>vintage-aware source observations</div><div class="card"><div class="num gold">9 / 12</div>comparable quarters versus gate</div></div><p class="callout">Forecast gate: ≥8 training observations + ≥4 chronological holdouts = ≥12 comparable quarters. Available: 9.</p><div class="caption">The evidence cutoff is September 20, 2026. The twelve-quarter forecast gate failed, so no forecast accuracy is claimed.</div></section>
<section class="slide" data-seconds="27"><div class="eyebrow">2 · Definition control</div><h2>Each definition break is part of the model.</h2><div class="grid"><div class="card"><b>Original Q3 ’23 revenue</b><div class="num red">$274.5M</div>included Base and payments-related revenue</div><div class="card"><b>Recast Q3 ’23 revenue</b><div class="num cyan">$247.0M</div>post-reclassification presentation</div><div class="card"><b>Later volume vintages</b><div class="num gold">-$1.5B to -$2.3B</div>Q2-Q4 2025 recast differences</div></div><p class="small">Later periods are crosswalked and preserved, but still quarantined from the pre-change panel.</p><div class="caption">Original and recast values remain distinct. A longer series is not automatically a more comparable series.</div></section>
<section class="slide" data-seconds="27"><div class="eyebrow">3 · What the evidence shows</div><h2>Consumer transaction revenue is volatile.</h2><div class="chart"><svg viewBox="0 0 {width} {height}" role="img" aria-label="Quarterly consumer transaction revenue trend"><polyline points="{polyline}"/>{dots}{xlabels}</svg></div><p class="small">USD millions · Q3 2023–Q3 2025 · recast pre-2024 revenue used for comparability</p><div class="caption">Revenue rose sharply into Q4 2024, then declined. The chart is a historical trend, not an extrapolation.</div></section>
<section class="slide" data-seconds="33"><div class="eyebrow">4 · Featured bridge · Q3 → Q4 2024</div><h2><span class="gold">+${change:,.1f}M</span> reported revenue change</h2><div class="grid"><div class="card"><b>Volume-associated effect</b><div class="num cyan">${volume_effect:,.1f}M</div><div class="bar"><span style="width:{float(volume_effect/change)*100:.1f}%"></span></div></div><div class="card"><b>Effective-yield effect</b><div class="num gold">${yield_effect:,.1f}M</div><div class="bar yield"><span style="width:{max(2,float(yield_effect/change)*100):.1f}%"></span></div></div><div class="card"><b>Rounded residual</b><div class="num">$0.0M</div>exact identity within $0.1M</div></div><p class="equation">ΔRevenue = volume effect + yield effect + residual</p><div class="caption">Under the disclosed volume-first order, $852.9 million is associated with volume and $10.9 million with the calculated effective-yield proxy.</div></section>
<section class="slide" data-seconds="23"><div class="eyebrow">5 · Planning layer</div><h2>Test assumptions.<br><span class="cyan">Do not assign fake probabilities.</span></h2><div class="grid"><div class="card"><b>Downside</b><div class="num red">$1,002.5M</div>-20% volume; -10 bps yield</div><div class="card"><b>Reference</b><div class="num cyan">$1,347.1M</div>Q4 2024 actual inputs</div><div class="card"><b>Upside</b><div class="num gold">$1,729.3M</div>+20% volume; +10 bps yield</div></div><div class="caption">These are editable mechanical sensitivities for management questions, not Coinbase guidance or a probability-weighted forecast.</div></section>
<section class="slide" data-seconds="21"><div class="eyebrow">6 · Strongest objection</div><h2>The allocation depends on bridge order.</h2><div class="grid"><div class="card"><b>Volume-first</b><div class="num cyan">${volume_effect:,.1f}M</div>volume effect</div><div class="card"><b>Yield-first</b><div class="num blue">${alt_volume:,.1f}M</div>volume effect</div><div class="card"><b>Symmetric Shapley</b><div class="num gold">${shapley_volume:,.1f}M</div>volume; yield ${shapley_yield:,.1f}M</div></div><p class="small">All three methods preserve the ${change:,.1f}M total. The symmetric view averages both valid orders.</p><div class="caption">Showing every method makes the path dependence inspectable. It does not prove management causality or create causal evidence.</div></section>
<section class="slide" data-seconds="11"><div class="eyebrow">Verdict</div><h1>A small model with<br><span class="cyan">strong epistemics.</span></h1><p class="lede">Reproducible, auditable, decision-useful—and bounded by what public evidence can actually support.</p><div class="label">DESCRIPTIVE / NOT A FORECAST</div><div class="caption">The artifact is ready for reviewer inspection as a descriptive bridge. Forecast readiness remains blocked by comparable-history coverage.</div></section>
<div id="chrome"><div id="progress"></div></div>
<script>
const slides=[...document.querySelectorAll('.slide')],durations=slides.map(x=>+x.dataset.seconds),total=durations.reduce((a,b)=>a+b,0);let current=0,elapsed=0,playing=true,last=performance.now();
function show(i){{current=(i+slides.length)%slides.length;slides.forEach((s,j)=>s.classList.toggle('active',j===current));elapsed=durations.slice(0,current).reduce((a,b)=>a+b,0);}}
function tick(now){{if(playing){{const dt=(now-last)/1000;elapsed+=dt;let boundary=0,next=0;while(next<durations.length-1&&elapsed>=boundary+durations[next]){{boundary+=durations[next];next++;}}if(elapsed>=total){{elapsed=0;next=0;}}if(next!==current){{current=next;slides.forEach((s,j)=>s.classList.toggle('active',j===current));}}document.querySelector('#progress').style.width=`${{elapsed/total*100}}%`;}}last=now;requestAnimationFrame(tick)}}
document.querySelector('#play').onclick=e=>{{playing=!playing;e.target.textContent=playing?'Pause':'Play'}};document.querySelector('#prev').onclick=()=>show(current-1);document.querySelector('#next').onclick=()=>show(current+1);document.onkeydown=e=>{{if(e.key==='ArrowRight')show(current+1);if(e.key==='ArrowLeft')show(current-1);if(e.key===' ')document.querySelector('#play').click();}};requestAnimationFrame(tick);
</script></body></html>'''
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "demo.html").write_text(document, encoding="utf-8")
    print(f"built {OUT / 'demo.html'} ({sum([15,23,27,27,33,23,21,11])} seconds)")


if __name__ == "__main__":
    main()
