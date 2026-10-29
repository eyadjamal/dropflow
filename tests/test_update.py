"""Update-checker tests (no network)."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import app_update


class UpdateTests(unittest.TestCase):
    def test_versions(self):
        self.assertEqual(app_update.version_key("v3.2.1"), (3, 2, 1))
        self.assertTrue(app_update.is_newer("v3.2.1", "3.2.0"))
        self.assertFalse(app_update.is_newer("3.2.0", "v3.2.0"))
        self.assertFalse(app_update.is_newer("3.1.9", "3.2.0"))

    def test_schedule(self):
        self.assertTrue(app_update.should_check(0, 100000))
        self.assertFalse(app_update.should_check(90, 100, 60))
        self.assertTrue(app_update.should_check(0, 100, 60))


if __name__ == "__main__":
    unittest.main()
