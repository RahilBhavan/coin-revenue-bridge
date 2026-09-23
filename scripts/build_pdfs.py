#!/usr/bin/env python3
"""Build the final standalone PDF memo and reviewer packet."""

import os
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "final-package"
OUT.mkdir(parents=True, exist_ok=True)
# Fixed creation/mod date (the 2026-09-20 evidence cutoff) so rebuilds are byte-identical.
os.environ["SOURCE_DATE_EPOCH"] = "1789862400"

NAVY = colors.HexColor("#10233F")
BLUE = colors.HexColor("#175CD3")
CYAN = colors.HexColor("#0E7490")
INK = colors.HexColor("#172B3A")
MUTED = colors.HexColor("#526575")
PALE = colors.HexColor("#EAF2FF")
ICE = colors.HexColor("#F4F8FC")
LINE = colors.HexColor("#CFD9E5")
GREEN = colors.HexColor("#087A55")
AMBER = colors.HexColor("#9A6700")


def register_fonts():
    candidates = {
        "Inter": "/System/Library/Fonts/Supplemental/Arial.ttf",
        "Inter-Bold": "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    }
    for name, path in candidates.items():
        if Path(path).exists():
            pdfmetrics.registerFont(TTFont(name, path))


register_fonts()
FONT = "Inter" if "Inter" in pdfmetrics.getRegisteredFontNames() else "Helvetica"
BOLD = "Inter-Bold" if "Inter-Bold" in pdfmetrics.getRegisteredFontNames() else "Helvetica-Bold"


def styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("title", parent=base["Title"], fontName=BOLD, fontSize=21, leading=24,
                                textColor=NAVY, alignment=TA_LEFT, spaceAfter=7),
        "eyebrow": ParagraphStyle("eyebrow", parent=base["Normal"], fontName=BOLD, fontSize=8.2,
                                  leading=10, textColor=BLUE, tracking=0.8, spaceAfter=6),
        "deck": ParagraphStyle("deck", parent=base["Normal"], fontName=FONT, fontSize=10.5, leading=15,
                               textColor=MUTED, spaceAfter=12),
        "h1": ParagraphStyle("h1", parent=base["Heading1"], fontName=BOLD, fontSize=12.5, leading=15,
                             textColor=NAVY, spaceBefore=5, spaceAfter=4),
        "h2": ParagraphStyle("h2", parent=base["Heading2"], fontName=BOLD, fontSize=9.5, leading=12,
                             textColor=BLUE, spaceBefore=6, spaceAfter=3),
        "body": ParagraphStyle("body", parent=base["BodyText"], fontName=FONT, fontSize=8.3, leading=11.5,
                               textColor=INK, spaceAfter=4),
        "small": ParagraphStyle("small", parent=base["BodyText"], fontName=FONT, fontSize=7.4, leading=10,
                                textColor=MUTED, spaceAfter=3),
        "callout": ParagraphStyle("callout", parent=base["BodyText"], fontName=BOLD, fontSize=10.3,
                                  leading=14.5, textColor=NAVY),
        "metric": ParagraphStyle("metric", parent=base["BodyText"], fontName=BOLD, fontSize=18,
                                 leading=20, textColor=NAVY, alignment=TA_CENTER),
        "metric_label": ParagraphStyle("metric_label", parent=base["BodyText"], fontName=FONT, fontSize=7.2,
                                       leading=9, textColor=MUTED, alignment=TA_CENTER),
        "table": ParagraphStyle("table", parent=base["BodyText"], fontName=FONT, fontSize=7.6,
                                leading=9.8, textColor=INK),
        "table_b": ParagraphStyle("table_b", parent=base["BodyText"], fontName=BOLD, fontSize=7.6,
                                  leading=9.8, textColor=NAVY),
    }


S = styles()


def P(text, style="body"):
    return Paragraph(text, S[style])


class ReportDoc(BaseDocTemplate):
    def __init__(self, filename, doc_label):
        super().__init__(filename, pagesize=letter, rightMargin=0.58 * inch, leftMargin=0.58 * inch,
                         topMargin=0.76 * inch, bottomMargin=0.52 * inch, title=doc_label,
                         author="Rahil Bhavan", invariant=1)
        self.doc_label = doc_label
        frame = Frame(self.leftMargin, self.bottomMargin, self.width, self.height, id="body")
        self.addPageTemplates(PageTemplate(id="main", frames=[frame], onPage=self.draw_page))

    def draw_page(self, canvas, doc):
        canvas.saveState()
        canvas.setFillColor(NAVY)
        canvas.rect(0, letter[1] - 0.18 * inch, letter[0], 0.18 * inch, stroke=0, fill=1)
        canvas.setStrokeColor(LINE)
        canvas.line(self.leftMargin, 0.38 * inch, letter[0] - self.rightMargin, 0.38 * inch)
        canvas.setFont(FONT, 6.8)
        canvas.setFillColor(MUTED)
        canvas.drawString(self.leftMargin, 0.22 * inch, "Independent analysis of Coinbase public filings | Rahil Bhavan")
        canvas.drawRightString(letter[0] - self.rightMargin, 0.22 * inch,
                               f"{self.doc_label}  |  {doc.page} / 2")
        canvas.restoreState()


def badge(text, color=BLUE):
    t = Table([[P(text, "eyebrow")]], colWidths=[3.15 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#E8F0FF")),
        ("BOX", (0, 0), (-1, -1), 0.5, color),
        ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
    ]))
    return t


def metric_strip():
    data = [
        [P("$863.8M", "metric"), P("$852.9M", "metric"), P("$10.9M", "metric"), P("$0.0M", "metric")],
        [P("revenue change", "metric_label"), P("volume effect", "metric_label"),
         P("effective-yield effect", "metric_label"), P("rounding residual", "metric_label")],
    ]
    t = Table(data, colWidths=[1.72 * inch] * 4, rowHeights=[0.34 * inch, 0.31 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PALE),
        ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor("#BDD1F4")),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CFDDF4")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return t


def source_table():
    rows = [
        [P("SOURCE", "table_b"), P("WHAT IT SUPPORTS", "table_b"), P("PUBLIC URL", "table_b")],
        [P("Q3 2024 shareholder letter<br/><font color='#526575'>filed Oct. 30, 2024</font>", "table"),
         P("Q3 consumer revenue ($483.3M) and consumer volume ($34B)", "table"),
         P("<link href='https://www.sec.gov/Archives/edgar/data/1679788/000167978824000186/q324shareholderletter.htm' color='#175CD3'>SEC exhibit</link>", "table")],
        [P("Q4 2024 shareholder letter<br/><font color='#526575'>filed Feb. 13, 2025</font>", "table"),
         P("Q4 consumer revenue ($1,347.1M) and consumer volume ($94B)", "table"),
         P("<link href='https://www.sec.gov/Archives/edgar/data/1679788/000167978825000021/q424shareholderletter.htm' color='#175CD3'>SEC exhibit</link>", "table")],
        [P("Q1 2024 shareholder letter<br/><font color='#526575'>filed May 2, 2024</font>", "table"),
         P("Revenue reclassification and recast Q3/Q4 2023 values", "table"),
         P("<link href='https://www.sec.gov/Archives/edgar/data/1679788/000167978824000087/q124shareholderletter.htm' color='#175CD3'>SEC exhibit</link>", "table")],
        [P("2025 Form 10-K<br/><font color='#526575'>filed Feb. 2026</font>", "table"),
         P("Later Trading Volume definition change; Q4 2025 quarantine", "table"),
         P("<link href='https://www.sec.gov/Archives/edgar/data/1679788/000167978826000015/coin-20251231.htm' color='#175CD3'>SEC filing</link>", "table")],
        [P("Q2 2026 earnings deck<br/><font color='#526575'>filed July 2026</font>", "table"),
         P("Later stablecoin adjustment to Q2-Q4 2025 consumer spot volume", "table"),
         P("<link href='https://www.sec.gov/Archives/edgar/data/1679788/000167978826000087/q226earningsdeck_sec.htm' color='#175CD3'>SEC exhibit</link>", "table")],
    ]
    t = Table(rows, colWidths=[1.76 * inch, 3.55 * inch, 1.55 * inch], repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.45, LINE), ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, ICE]),
        ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return t


def build_memo():
    story = [
        badge("DESCRIPTIVE / NOT A FORECAST"), Spacer(1, 8),
        P("Consumer transaction revenue bridge", "title"),
        P("Decision memo | Q3 to Q4 2024 | Evidence cutoff: September 20, 2026", "deck"),
        P("Decision", "h1"),
        P("Use the Q3-to-Q4 2024 bridge as a decision-support diagnostic, and <b>do not present a forecast or model-performance claim</b>. The nine-quarter public panel cannot satisfy the predeclared gate of eight training quarters plus four chronological holdouts under one comparable definition family."),
        Spacer(1, 4), metric_strip(), Spacer(1, 9),
        P("What changed", "h1"),
        P("Consumer transaction revenue increased from <b>$483.3 million</b> to <b>$1,347.1 million</b> as consumer trading volume increased from <b>$34 billion</b> to <b>$94 billion</b>. Calculated effective yield moved from <b>1.421%</b> to <b>1.433%</b>. The fixed-order bridge assigns $852.9 million to volume and $10.9 million to effective yield. A symmetric Shapley split assigns <b>$856.4 million</b> and <b>$7.4 million</b>, respectively."),
        P("Interpretation boundary", "h1"),
        P("This is an algebraic decomposition, not causal attribution. Consumer revenue includes items not directly associated with reported matched-spot volume, while reported volume excludes derivatives. Revenue divided by volume is therefore an <b>effective-yield proxy</b> - not a fee rate, price, or causal driver."),
        P("Immediate implication", "h1"),
        P("The large descriptive volume component says where diligence should concentrate: determine whether the Q4 activity surge is durable and whether customer, asset, geography, and pricing mix altered monetization. It does not prove that volume caused the revenue increase or that the relationship will persist."),
        Spacer(1, 4),
        Table([[P("RECOMMENDATION", "eyebrow"), P("Keep the artifact descriptive. Expand and reconcile the vintage-safe panel before any forecasting claim.", "callout")]],
              colWidths=[1.25 * inch, 5.55 * inch], style=TableStyle([
                  ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#E7F8F2")),
                  ("BOX", (0, 0), (-1, -1), 0.8, GREEN), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                  ("LEFTPADDING", (0, 0), (-1, -1), 9), ("RIGHTPADDING", (0, 0), (-1, -1), 9),
                  ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
              ])),
        PageBreak(),
        badge("EVIDENCE, RISKS, AND NEXT INVESTIGATION"), Spacer(1, 8),
        P("Decision support, with the limits visible", "title"),
        P("The analysis is reproducible from SEC-hosted Coinbase filings and deliberately stops short of inference.", "deck"),
        P("Definition-vintage issue", "h1"),
        P("Coinbase reclassified Base sequencer and payment-related revenue from Consumer, net to Other transaction revenue in Q1 2024 and recast prior periods. Later filings changed Trading Volume again. The Q2 2026 deck reports Q2-Q4 2025 consumer spot volumes that are $1.5B, $1.6B, and $2.3B below earlier disclosures. The crosswalk is documented, but those quarters remain outside the pre-change panel."),
        P("Strongest objection", "h1"),
        P("The bridge can look more explanatory than it is. Because effective yield is calculated as revenue divided by volume, the two-factor identity will reconcile mechanically. It does not independently validate economic drivers, isolate mix, or establish a stable forecasting relationship."),
        P("Recommended next investigation", "h1"),
        P("Use the workbook's editable sensitivities to test volume and effective-yield assumptions around the Q4 2024 reference case. Treat the downside, reference, and upside cases as planning prompts, not probabilities. A forecast still requires at least twelve definition-compatible observations and four chronological holdouts."),
        P("Decision gates", "h1"),
        Table([
            [P("GATE", "table_b"), P("PASS CONDITION", "table_b"), P("CURRENT STATUS", "table_b")],
            [P("Comparable history", "table"), P("12+ quarters in one definition family", "table"), P("<font color='#9A6700'><b>Not met: 9 quarters</b></font>", "table")],
            [P("Vintage integrity", "table"), P("No silent use of later recasts", "table"), P("Explicitly separated", "table")],
            [P("Forecast evidence", "table"), P("4 chronological holdouts; baselines scored", "table"), P("<font color='#9A6700'><b>Not attempted</b></font>", "table")],
            [P("Definition boundary", "table"), P("Later volume vintages crosswalked", "table"), P("Reconciled; still quarantined", "table")],
        ], colWidths=[1.5 * inch, 3.55 * inch, 1.8 * inch], style=TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), NAVY), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.45, LINE), ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, ICE]),
            ("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6), ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ])),
        P("Primary sources", "h1"), source_table(), Spacer(1, 6),
        P("Reviewer question", "h1"),
        P("Would you accept this bridge as a useful descriptive diagnostic while rejecting it as forecast evidence - and what additional evidence would change that judgment?", "callout"),
    ]
    ReportDoc(str(OUT / "decision-memo.pdf"), "Decision memo").build(story)


def build_reviewer():
    story = [
        badge("DESCRIPTIVE / NOT A FORECAST"), Spacer(1, 8),
        P("Reviewer packet", "title"),
        P("Consumer transaction revenue bridge | Q3 to Q4 2024 | Evidence cutoff: September 20, 2026", "deck"),
        P("Review objective", "h1"),
        P("Assess whether the evidence, definitions, arithmetic, and claims support a useful descriptive comparison without implying causality or forecasting performance."),
        metric_strip(), Spacer(1, 8),
        P("Inputs and calculation", "h1"),
        Table([
            [P("METRIC", "table_b"), P("Q3 2024", "table_b"), P("Q4 2024", "table_b"), P("CHANGE", "table_b")],
            [P("Consumer transaction revenue", "table"), P("$483.3M", "table"), P("$1,347.1M", "table"), P("+$863.8M", "table")],
            [P("Consumer trading volume", "table"), P("$34B", "table"), P("$94B", "table"), P("+$60B", "table")],
            [P("Calculated effective yield", "table"), P("1.421%", "table"), P("1.433%", "table"), P("+0.012 pp", "table")],
        ], colWidths=[2.8 * inch, 1.32 * inch, 1.32 * inch, 1.32 * inch], style=TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), NAVY), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.45, LINE), ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, ICE]),
            ("ALIGN", (1, 1), (-1, -1), "RIGHT"), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 7), ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ])),
        P("Fixed-order methodology", "h1"),
        P("Let revenue <i>R</i> = volume <i>V</i> x effective yield <i>Y</i>. The bridge holds Q3 yield constant while volume moves first, then applies the yield change at Q4 volume:"),
        Table([
            [P("Volume effect", "table_b"), P("(94 - 34) x 1.4214706% = $852.9M", "table")],
            [P("Effective-yield effect", "table_b"), P("94 x (1.4330851% - 1.4214706%) = $10.9M", "table")],
            [P("Symmetric allocation", "table_b"), P("Average both factor orders: volume $856.4M; calculated yield $7.4M", "table")],
            [P("Reconciliation", "table_b"), P("$852.9M + $10.9M = $863.8M; rounded residual $0.0M", "table")],
        ], colWidths=[2.0 * inch, 4.76 * inch], style=TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), PALE), ("GRID", (0, 0), (-1, -1), 0.45, LINE),
            ("LEFTPADDING", (0, 0), (-1, -1), 7), ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ])),
        P("Required claim boundary", "h1"),
        P("The sequence is a convention, not a causal finding. Reversing the order reallocates the interaction term. Effective yield is calculated from the same revenue and volume inputs, so exact reconciliation is mechanical. Do not call the proxy a fee rate or present the result as predictive."),
        P("Reviewer question", "h1"),
        P("Does this bridge improve the decision conversation without overstating what the two reported metrics can explain?", "callout"),
        PageBreak(),
        badge("REVIEW CHECKLIST AND SOURCE TRAIL"), Spacer(1, 8),
        P("What to challenge", "title"),
        P("The packet is designed for rejection testing, not affirmation.", "deck"),
        P("1. Comparability", "h1"),
        P("Confirm both featured quarters use the post-Q1-2024 consumer-revenue family and the pre-Q4-2025 matched-spot consumer-volume family. Verify that the revenue scope can include components not tied directly to reported spot volume."),
        P("2. Vintage discipline", "h1"),
        P("The nine-quarter descriptive panel uses Q1 2024 recasts for Q3/Q4 2023 and first-reported observations thereafter. A separate crosswalk now preserves later Q2-Q4 2025 volume vintages. The later values differ by $1.5B, $1.6B, and $2.3B, so they remain quarantined rather than silently spliced into the panel."),
        P("3. Forecast gate", "h1"),
        P("The planned tournament required eight comparable training observations plus four chronological holdouts. Nine total quarters cannot satisfy twelve required observations. No model was fit, no forecast was scored, and no superiority claim was tested."),
        P("Strongest objection", "h1"),
        Table([[P("A perfect bridge is not proof of explanatory power.", "callout")],
               [P("Because yield is derived from revenue / volume, the identity must reconcile. Mix, customer behavior, asset composition, spreads, and non-volume revenue can all sit inside the residual economic meaning of the calculated yield even when the arithmetic residual is zero.", "body")]],
              colWidths=[6.78 * inch], style=TableStyle([
                  ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FFF4D6")),
                  ("BOX", (0, 0), (-1, -1), 0.8, AMBER),
                  ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                  ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
              ])),
        P("Recommended next investigation", "h1"),
        P("Use the editable downside, reference, and upside sensitivities to frame management questions now. Extend the original-vintage panel to twelve or more compatible quarters before scoring a seasonal naive baseline and a volume x trailing-yield baseline across four chronological holdouts."),
        P("Primary sources", "h1"), source_table(),
        P("Reviewer disposition", "h1"),
        Table([[P("Accept / revise / reject", "table_b"),
                P("Single most valuable next analysis: __________________________________________", "table")]],
              colWidths=[1.55 * inch, 5.23 * inch], style=TableStyle([
                  ("BACKGROUND", (0, 0), (-1, -1), ICE), ("BOX", (0, 0), (-1, -1), 0.6, LINE),
                  ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                  ("LEFTPADDING", (0, 0), (-1, -1), 7), ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                  ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
              ])),
    ]
    ReportDoc(str(OUT / "reviewer-packet.pdf"), "Reviewer packet").build(story)


if __name__ == "__main__":
    build_memo()
    build_reviewer()
    print(f"Built PDFs in {OUT}")
