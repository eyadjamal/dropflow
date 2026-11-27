"""Small OS boundary shared by the app and conversion engines."""
from pathlib import Path
import atexit
import importlib
import os
import signal
import subprocess
import sys
import webbrowser

IS_WINDOWS = sys.platform == "win32"
IS_LINUX = sys.platform.startswith("linux")

def load_tray_module():
    """Try XEmbed when Linux GI exists but its Gtk namespace is missing."""
    try:
        return importlib.import_module("pystray")
    except Exception:
        if not IS_LINUX or os.environ.get("PYSTRAY_BACKEND"):
            raise
        os.environ["PYSTRAY_BACKEND"] = "xorg"
        try:
            return importlib.import_module("pystray")
        finally:
            os.environ.pop("PYSTRAY_BACKEND", None)

def config_directory(platform=None, environ=None, home=None):
    platform = platform or sys.platform
    environ = os.environ if environ is None else environ
    home = Path.home() if home is None else Path(home)
    if platform == "win32":
        return Path(environ.get("APPDATA", str(home))) / "DropFlow"
    return Path(environ.get("XDG_CONFIG_HOME", str(home / ".config"))) / "dropflow"

def process_options():
    if IS_WINDOWS:
        return {"creationflags": getattr(subprocess, "CREATE_NO_WINDOW", 0)}
    return {"start_new_session": True}

def terminate_process_tree(process):
    if process.poll() is not None:
        return
    if IS_WINDOWS:
        try:
            subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                           stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL, timeout=8, **process_options())
            return
        except (OSError, subprocess.SubprocessError):
            pass
    else:
        try:
            # Only signal a process group created for this conversion.
            if os.getpgid(process.pid) == process.pid:
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                return
        except ProcessLookupError:
            return
    process.kill()

def open_file(path, reveal=False):
    path = Path(path).resolve()
    if IS_WINDOWS:
        if reveal and not path.is_dir():
            subprocess.Popen(["explorer", "/select,", str(path)], **process_options())
        else:
            os.startfile(str(path))
    else:
        target = path.parent if reveal and not path.is_dir() else path
        subprocess.Popen(["xdg-open", str(target)], stdin=subprocess.DEVNULL,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                         **process_options())

def open_browser(url):
    webbrowser.open(url)

def desktop_exec(arguments):
    """Quote Desktop Entry Exec arguments, not a shell command."""
    quoted = []
    for argument in arguments:
        argument = str(argument)
        if "\n" in argument or "\r" in argument:
            raise ValueError("Desktop launcher paths must not contain newlines.")
        argument = argument.replace("%", "%%").replace("\\", "\\\\\\\\")
        for character in ('"', '$', '`'):
            argument = argument.replace(character, "\\" + character)
        quoted.append('"' + argument + '"')
    return " ".join(quoted)

def _write(path, content, executable=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(content, encoding="utf-8")
    temporary.chmod(0o755 if executable else 0o600)
    temporary.replace(path)

def linux_autostart(enabled, arguments, config_home=None):
    config_home = Path(config_home or os.environ.get("XDG_CONFIG_HOME", str(Path.home()/".config")))
    path = config_home / "autostart" / "dropflow.desktop"
    if enabled:
        _write(path, "[Desktop Entry]\nType=Application\nName=DropFlow\n"
               + "Exec=" + desktop_exec([*arguments, "--minimized"]) + "\nTerminal=false\n")
    else:
        path.unlink(missing_ok=True)

def linux_filemanager_menu(enabled, arguments, data_home=None):
    """Optional Nautilus script and Dolphin service; no default-app takeover."""
    data_home = Path(data_home or os.environ.get("XDG_DATA_HOME", str(Path.home()/".local/share")))
    script = data_home / "nautilus/scripts/Send to DropFlow"
    service = data_home / "kio/servicemenus/dropflow.desktop"
    if not enabled:
        script.unlink(missing_ok=True)
        service.unlink(missing_ok=True)
        return
    _write(script, "#!/usr/bin/env python3\nimport os, subprocess\n"
           + "command = " + repr(list(map(str, arguments))) + "\n"
           + "paths = os.environ.get('NAUTILUS_SCRIPT_SELECTED_FILE_PATHS', '').splitlines()\n"
           + "if paths: subprocess.Popen(command + ['--send'] + paths, start_new_session=True)\n", True)
    _write(service, "[Desktop Entry]\nType=Service\nMimeType=all/all;\nActions=DropFlow;\n"
           + "X-KDE-ServiceTypes=KonqPopupMenu/Plugin\n\n[Desktop Action DropFlow]\n"
           + "Name=Send to DropFlow\nIcon=dropflow\nExec="
           + desktop_exec([*arguments, "--send"]) + " %F\n", True)

class LinuxInstanceLock:
    """Per-user advisory lock: held until process exit, never deletes a live lock."""
    def __init__(self, path):
        self.path, self.file = Path(path), None

    def acquire(self):
        import fcntl
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.file = self.path.open("a+")
        self.path.chmod(0o600)
        try:
            fcntl.flock(self.file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            self.file.close()
            self.file = None
            return False
        atexit.register(self.release)
        return True

    def release(self):
        if self.file:
            self.file.close()
            self.file = None
