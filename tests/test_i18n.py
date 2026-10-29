"""Localization tests."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import i18n


class LocaleTests(unittest.TestCase):
    def tearDown(self):
        i18n.set_language("en")

    def test_english_fallback(self):
        i18n.set_language("en")
        self.assertEqual(i18n.tr("Settings"), "Settings")

    def test_arabic(self):
        i18n.set_language("ar")
        self.assertTrue(i18n.is_rtl())
        self.assertEqual(i18n.tr("Settings"), "الإعدادات")
        self.assertEqual(i18n.tr("Cancel"), "إلغاء")
        self.assertIn("تحويل", i18n.tr("Convert to PNG"))

    def test_unknown_language(self):
        i18n.set_language("xx")
        self.assertEqual(i18n.get_language(), "en")


if __name__ == "__main__":
    unittest.main()
