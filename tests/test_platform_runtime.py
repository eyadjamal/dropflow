import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import platform_runtime as runtime
from linux_hotkeys import HotkeyManager

class PlatformTests(unittest.TestCase):
    def test_config_paths(self):
        home = Path(tempfile.gettempdir())/"test-home"
        self.assertEqual(runtime.config_directory("linux", {}, home), home/".config/dropflow")
        self.assertEqual(runtime.config_directory("win32", {}, home), home/"DropFlow")
        self.assertEqual(runtime.config_directory("linux", {"XDG_CONFIG_HOME":str(home/"config")}, home), home/"config/dropflow")

    def test_desktop_quoting(self):
        line = runtime.desktop_exec(["/home/name with spaces/python", "/tmp/100%/app.pyw"])
        self.assertIn('"/home/name with spaces/python"', line)
        self.assertIn('100%%', line)
        with self.assertRaises(ValueError):
            runtime.desktop_exec(["bad\npath"])

    def test_linux_autostart_and_filemanager_actions(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            arguments = ["/tmp/my venv/python", "/tmp/source/app.pyw"]
            runtime.linux_autostart(True, arguments, root)
            self.assertIn('--minimized', (root/'autostart/dropflow.desktop').read_text())
            runtime.linux_filemanager_menu(True, arguments, root)
            script = root/'nautilus/scripts/Send to DropFlow'
            compile(script.read_text(), str(script), 'exec')
            self.assertIn(' %F', (root/'kio/servicemenus/dropflow.desktop').read_text())
            runtime.linux_autostart(False, arguments, root)
            runtime.linux_filemanager_menu(False, arguments, root)
            self.assertFalse(script.exists())
            self.assertFalse((root/'autostart/dropflow.desktop').exists())

    def test_wayland_gives_desktop_shortcut_guidance(self):
        manager = HotkeyManager(lambda: None)
        with mock.patch.dict(os.environ, {'WAYLAND_DISPLAY':'wayland-0'}):
            success, error = manager.register('ctrl+shift+d')
        self.assertFalse(success)
        self.assertIn('dropflow --toggle', error)

    @unittest.skipUnless(runtime.IS_LINUX, 'POSIX process groups')
    def test_cancel_terminates_child_process_group(self):
        import signal
        import time
        child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'], **runtime.process_options())
        try:
            self.assertEqual(os.getpgid(child.pid), child.pid)
            runtime.terminate_process_tree(child)
            child.wait(timeout=5)
            self.assertIsNotNone(child.returncode)
        finally:
            if child.poll() is None:
                child.kill()

    @unittest.skipUnless(runtime.IS_LINUX, 'POSIX locking')
    def test_single_instance_lock_releases_cleanly(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'instance.lock'
            first=runtime.LinuxInstanceLock(path)
            second=runtime.LinuxInstanceLock(path)
            try:
                self.assertTrue(first.acquire())
                self.assertFalse(second.acquire())
                first.release()
                self.assertTrue(second.acquire())
            finally:
                first.release()
                second.release()
