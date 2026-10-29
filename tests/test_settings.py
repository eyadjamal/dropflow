"""Settings persistence tests without opening a GUI."""
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import importlib.machinery
import importlib.util
import i18n

loader = importlib.machinery.SourceFileLoader("dropflow_settings",
                                              str(ROOT / "DropFlow.pyw"))
spec = importlib.util.spec_from_file_location("dropflow_settings",
                                              str(ROOT / "DropFlow.pyw"),
                                              loader=loader)
df = importlib.util.module_from_spec(spec)
sys.modules["dropflow_settings"] = df
spec.loader.exec_module(df)


class FakeHotkey:
    def register(self, value):
        return True, ""

    def unregister(self):
        pass


class SettingsTests(unittest.TestCase):
    def tearDown(self):
        i18n.set_language("en")

    def test_apply_settings_persists_new_options(self):
        app = SimpleNamespace(
            cfg={"hotkey": "ctrl+shift+d", "ocr_langs": "eng",
                 "language": "en", "remember_position": True,
                 "check_updates": True, "explorer_menu": False},
            hotkey_ok=True, hotkey_error="", hotkey=FakeHotkey(),
            notify=lambda _m: None, _refresh_tray=lambda: None,
        )
        with mock.patch.object(df, "set_autostart"), \
                mock.patch.object(df, "set_explorer_menu"), \
                mock.patch.object(df, "save_config"):
            ok, err = df.App.apply_settings(
                app, "ctrl+shift+d", False, "eng",
                remember_position=False, language="ar",
                check_updates=False, explorer_menu=True)
        self.assertTrue(ok, err)
        self.assertEqual(app.cfg["language"], "ar")
        self.assertFalse(app.cfg["remember_position"])
        self.assertFalse(app.cfg["check_updates"])
        self.assertTrue(app.cfg["explorer_menu"])
        self.assertEqual(i18n.get_language(), "ar")


if __name__ == "__main__":
    unittest.main()
