import sys
import unittest
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import build_revenue_bridge_card as card  # noqa: E402


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
        labels = [text for _, _, _, text, _ in card.bars(self.fig)]
        self.assertEqual(labels, ["$483.3M", "+$856.4M", "+$7.4M", "$1,347.1M"])

    def test_one_highlighted_bar_and_it_is_volume(self):
        highlighted = [label for label, _, _, _, hi in card.bars(self.fig) if hi]
        self.assertEqual(highlighted, ["Volume"])

    def test_title_alt_and_footer_agree_with_the_numbers(self):
        self.assertEqual(card.title_text(self.fig), "Volume drove $856.4M of Coinbase’s $863.8M revenue jump")
        alt = card.alt_text(self.fig)
        for text in ("$483.3M", "$856.4M", "$7.4M", "$1,347.1M", card.SHAPLEY):
            self.assertIn(text, alt)
        self.assertTrue(card.footer_text(self.fig).endswith("Data as of Feb 13, 2025."))

    def test_waterfall_steps_are_contiguous(self):
        steps = card.bars(self.fig)
        for prev, nxt in zip(steps[:2], steps[1:3]):
            self.assertAlmostEqual(prev[1] + prev[2], nxt[1], places=6)
        self.assertAlmostEqual(steps[2][1] + steps[2][2], steps[3][2], places=6)


if __name__ == "__main__":
    unittest.main()
