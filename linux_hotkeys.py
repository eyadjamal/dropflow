"""X11 global hotkeys; Wayland uses an explicit desktop-owned shortcut."""
import os

DESKTOP_SHORTCUT_HELP = "Set a desktop keyboard shortcut to: dropflow --toggle"

class HotkeyManager:
    def __init__(self, callback):
        self.callback, self.listener = callback, None

    def start(self):
        pass

    def register(self, shortcut):
        if os.environ.get("WAYLAND_DISPLAY") or os.environ.get("XDG_SESSION_TYPE") == "wayland":
            return False, DESKTOP_SHORTCUT_HELP
        try:
            from pynput.keyboard import GlobalHotKeys
            mapping = {"ctrl":"<ctrl>", "alt":"<alt>", "shift":"<shift>", "win":"<cmd>",
                       "enter":"<enter>", "esc":"<esc>", "space":"<space>"}
            tokens = shortcut.lower().split("+")
            keys = "+".join(mapping.get(t, "<"+t+">" if len(t)>1 else t) for t in tokens)
            listener = GlobalHotKeys({keys: self.callback})
            self.unregister()
            listener.start()
            listener.wait()
            self.listener = listener
            return True, ""
        except Exception as exc:
            return False, DESKTOP_SHORTCUT_HELP + " (" + str(exc) + ")"

    def unregister(self):
        if self.listener:
            self.listener.stop()
            self.listener = None
        return True, ""

    def stop(self):
        self.unregister()
