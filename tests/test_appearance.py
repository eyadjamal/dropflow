"""Appearance token tests."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import appearance


class AppearanceTests(unittest.TestCase):
    def test_all_themes_have_tokens(self):
        for name in appearance.THEME_ORDER:
            actual, tokens = appearance.resolve_theme(name)
            self.assertIn(actual, appearance.THEMES)
            for key in ("bg", "fg", "accent", "surface", "subtle"):
                self.assertIn(key, tokens)

    def test_contrast(self):
        self.assertGreater(appearance.contrast_ratio("#000000", "#ffffff"), 20)
        self.assertLess(appearance.contrast_ratio("#777777", "#888888"), 2)

    def test_safe_accent(self):
        color, ratio = appearance.safe_accent("#111111", "#181825")
        self.assertGreaterEqual(ratio, 4.5)
        self.assertNotEqual(color, "#111111")

    def test_normalize(self):
        self.assertEqual(appearance.normalize_hex("ABC", "#000000"), "#aabbcc")
        self.assertEqual(appearance.normalize_hex("zzzzzz", "#123456"), "#123456")


if __name__ == "__main__":
    unittest.main()

