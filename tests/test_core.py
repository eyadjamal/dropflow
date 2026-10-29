"""Unit tests for DropFlow utility helpers (no GUI, no external converters)."""
import importlib.machinery
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

loader = importlib.machinery.SourceFileLoader("dropflow_app", str(ROOT / "DropFlow.pyw"))
spec = importlib.util.spec_from_file_location("dropflow_app",
                                              str(ROOT / "DropFlow.pyw"), loader=loader)
df = importlib.util.module_from_spec(spec)
sys.modules["dropflow_app"] = df
spec.loader.exec_module(df)


class CoreTests(unittest.TestCase):
    def test_version(self):
        self.assertEqual(df.APP_VERSION, "3.2.0")

    def test_fmt_size(self):
        self.assertIn("KB", df.fmt_size(2048))
        self.assertIn("MB", df.fmt_size(2 * 1024 * 1024))

    def test_natural_key(self):
        values = [Path("page10.pdf"), Path("page2.pdf"), Path("page1.pdf")]
        self.assertEqual([p.name for p in sorted(values, key=df.natural_key)],
                         ["page1.pdf", "page2.pdf", "page10.pdf"])

    def test_archive_safety(self):
        self.assertTrue(df._archive_name_unsafe("../escape.txt"))
        self.assertTrue(df._archive_name_unsafe("/absolute.txt"))
        self.assertTrue(df._archive_name_unsafe(r"C:\absolute.txt"))
        self.assertFalse(df._archive_name_unsafe("folder/file.txt"))

    def test_hotkey_pretty(self):
        self.assertEqual(df.pretty_hotkey("ctrl+shift+d"), "Ctrl + Shift + D")

    def test_config_defaults_and_window_position(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / "config.json"
            with mock.patch.object(df, "CONFIG_PATH", config):
                cfg = df.load_config()
                self.assertEqual(cfg["language"], "en")
                self.assertTrue(cfg["remember_position"])
                self.assertIsNone(cfg["window_x"])
                app = SimpleNamespace(cfg=cfg)
                df.App.save_window_position(app, 123, 456)
                self.assertEqual(cfg["window_x"], 123)
                self.assertEqual(cfg["window_y"], 456)
                saved = json.loads(config.read_text(encoding="utf-8"))
                self.assertEqual(saved["window_y"], 456)


if __name__ == "__main__":
    unittest.main()
