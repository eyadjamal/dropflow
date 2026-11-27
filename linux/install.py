"""Install the source release for the current Linux user, without sudo."""
from pathlib import Path
import os
import shlex
import shutil
import subprocess
import sys
import venv

def main():
    if not sys.platform.startswith("linux"):
        raise SystemExit("Run this installer on Linux.")
    if sys.version_info < (3, 10):
        raise SystemExit("Python 3.10 or newer is required.")
    if os.geteuid() == 0:
        raise SystemExit("Run install.sh as your desktop user, without sudo.")
    try:
        import tkinter
    except ImportError:
        raise SystemExit("Install Python Tk support first (Debian/Ubuntu: sudo apt install python3-tk python3-venv).")
    source = Path(__file__).resolve().parents[1]
    data = Path(os.environ.get("XDG_DATA_HOME", str(Path.home()/".local/share")))
    app = data / "dropflow"
    app.mkdir(parents=True, exist_ok=True)
    for pattern in ("*.py", "*.pyw", "requirements.txt", "LICENSE", "README.md", "THIRD_PARTY_NOTICES.txt"):
        for file in source.glob(pattern):
            destination = app / file.name
            if file.resolve() != destination.resolve():
                shutil.copy2(file, destination)
    environment = app / ".venv"
    venv.EnvBuilder(with_pip=True, system_site_packages=True, symlinks=True).create(environment)
    python = environment / "bin/python"
    subprocess.run([str(python), "-m", "pip", "install", "-r", str(app/"requirements.txt")], check=True)
    sys.path.insert(0, str(app))
    from platform_runtime import desktop_exec
    bin_dir = Path.home()/".local/bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    launcher = bin_dir / "dropflow"
    launcher.write_text("#!/bin/sh\nexec " + shlex.quote(str(python)) + " "
                        + shlex.quote(str(app/"DropFlow.pyw")) + ' "$@"\n', encoding="utf-8")
    launcher.chmod(0o755)
    applications = data / "applications"
    applications.mkdir(parents=True, exist_ok=True)
    icon = data / "icons/hicolor/128x128/apps/dropflow.png"
    icon.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source/"linux/dropflow.png", icon)
    entry = ("[Desktop Entry]\nType=Application\nName=DropFlow\n"
             "Comment=Local file conversion and PDF tools\nTerminal=false\n"
             "Categories=Utility;Graphics;Office;\nIcon=dropflow\nExec="
             + desktop_exec([str(launcher), "--workspace", "--send"]) + " %F\n")
    (applications/"dropflow.desktop").write_text(entry, encoding="utf-8")
    refresh = shutil.which("update-desktop-database")
    if refresh:
        subprocess.run([refresh, str(applications)], check=False)
    print("Installed. Open DropFlow from your application menu, or run:", launcher)
    print("Wayland shortcut command:", str(launcher), "--toggle")

if __name__ == "__main__":
    main()
