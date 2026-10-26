import json
import re
import sys
import unittest
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import build_revenue_bridge_card as card  # noqa: E402
import check_coinbase_filing as sec  # noqa: E402

OUT = ROOT / "outputs/revenue-bridge-card"


class RevenueBridgeCardTests(unittest.TestCase):
    def setUp(self):
        self.fig = card.load_figures()

    def test_printed_numbers_add_up(self):
        f = self.fig
        self.assertEqual(
            (f["start"], f["volume"], f["yield"], f["end"]),
            (Decimal("483.3"), Decimal("856.4"), Decimal("7.4"), Decimal("1347.1")),
        )
        self.assertEqual(f["start"] + f["volume"] + f["yield"], f["end"])

    def test_every_bar_label_carries_the_unit(self):
        labels = [text for _, _, _, text, _ in card.steps(self.fig)]
        self.assertEqual(labels, ["$483.3M", "+$856.4M", "+$7.4M", "$1,347.1M"])

    def test_one_highlighted_bar_and_the_title_names_its_value(self):
        highlighted = [text for _, _, _, text, hi in card.steps(self.fig) if hi]
        self.assertEqual(highlighted, ["+$856.4M"])
        self.assertIn("$856.4M", card.title_text(self.fig))

    def test_waterfall_steps_are_contiguous(self):
        steps = card.steps(self.fig)
        self.assertAlmostEqual(steps[0][1] + steps[0][2], steps[1][1], places=6)
        self.assertAlmostEqual(steps[1][1] + steps[1][2], steps[2][1], places=6)
        self.assertAlmostEqual(steps[2][1] + steps[2][2], steps[3][2], places=6)

    def test_title_footer_and_alt_agree_with_the_numbers(self):
        self.assertEqual(card.title_text(self.fig), "Volume: $856.4M of $863.8M")
        self.assertEqual(card.footer_text(self.fig), "Source: Coinbase SEC filings. Data as of Feb 13, 2025.")
        alt = card.alt_text(self.fig)
        self.assertNotIn("\n", alt)
        for text in ("$483.3M", "$856.4M", "$7.4M", "$863.8M", "$1,347.1M", card.SHAPLEY, card.footer_text(self.fig)):
            self.assertIn(text, alt)

    def test_markup_uses_only_token_fonts_and_colours(self):
        markup = card.card_html(self.fig)
        tokens = json.loads((card.RAHIL / "tokens.json").read_text())
        allowed = {v.lower() for group in ("color", "chart") for v in tokens[group].values()}
        self.assertLessEqual({c.lower() for c in re.findall(r"#[0-9a-fA-F]{6}\b", markup)}, allowed)
        self.assertEqual(set(re.findall(r"font-family:'([^']+)'", markup)), {"Rahil Display", "Rahil Plex"})

    def test_committed_manifest_matches_the_files(self):
        manifest = json.loads((OUT / "manifest.json").read_text())
        self.assertEqual(manifest["review_status"], "design review pending")
        for name, digest in manifest["artifacts"].items():
            self.assertEqual(card.sha256(OUT / name), digest, name)
        self.assertEqual((OUT / "alt-text.txt").read_text().strip(), card.alt_text(self.fig))


class FilingCheckTests(unittest.TestCase):
    def test_frozen_index_has_q2_but_no_q3_2026_filings(self):
        data = json.loads((ROOT / "data/raw/sec-submissions-cik0001679788-20261025.json").read_text())
        rows = sec.filings(data, "2026-09-30")
        self.assertEqual(rows[0][0], "10-Q")
        self.assertEqual(rows[0][3], "2026-06-30")
        self.assertEqual([r for r in rows if r[3] == "2026-09-30"], [])
        self.assertTrue(rows[0][5].startswith("https://www.sec.gov/Archives/edgar/data/1679788/"))


if __name__ == "__main__":
    unittest.main()
