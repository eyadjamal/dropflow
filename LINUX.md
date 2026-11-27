# DropFlow on Linux

DropFlow 3.4.0 supports Windows and Linux. Use a graphical desktop session; a display server is required. Tk uses X11, or XWayland within a Wayland session. Linux uses normal window-manager decorations instead of Windows blur effects. The control window remains available when no system tray is present.

## Install from source (recommended)

Python 3.10+ and Tk are required. On Debian/Ubuntu:

```bash
sudo apt install python3-tk python3-venv libxcursor1 xdg-utils
# Extract the source package, enter its directory, then:
sh linux/install.sh
```

Run the installer as your normal desktop user, without sudo. Internet access is required to download Python dependencies. It installs application files and a virtual environment under `${XDG_DATA_HOME:-~/.local/share}/dropflow`, creates `~/.local/bin/dropflow`, and adds an applications-menu launcher. Run `~/.local/bin/dropflow` if that directory is not on PATH. Reinstalling updates the application files while preserving settings.

For a development checkout, create a virtual environment, install requirements.txt, then run `python DropFlow.pyw --console`.

## Portable x86_64 executable

Extract the complete Linux executable archive, keep its `_internal` directory beside `DropFlow`, then run `./DropFlow`. Python is bundled. Tk still needs a graphical session and the distribution's system libraries. The release is built on Debian 12 (glibc 2.36); older distributions may require the source installation. An ARM build is not supplied. External Office/OCR/archive programs are not bundled.

## Desktop behavior

- Select files or folders in the control window, or drop files where supported by TkDND and your desktop.
- Settings offers login autostart and optional Nautilus/Dolphin actions. Other file managers can run `dropflow --send <files>`. Default file associations are not changed.
- X11 global shortcuts are optional: install requirements-x11.txt into the application's virtual environment (`~/.local/share/dropflow/.venv/bin/python -m pip install pynput`).
- Wayland restricts global keyboard hooks. Create a custom shortcut in GNOME/KDE settings with command `/home/YOUR_USER/.local/bin/dropflow --toggle` (use your actual home path).
- Tray availability depends on the desktop's AppIndicator/GTK/XEmbed support. GNOME may need an AppIndicator extension. The control window works without a tray. Closing it quits; minimizing keeps it available.
- For GTK/AppIndicator integration on Debian/Ubuntu, optional packages are `python3-gi gir1.2-gtk-3.0 gir1.2-ayatanaappindicator3-0.1`. The source installer's virtual environment can use those system bindings.
- Configuration and logs use `${XDG_CONFIG_HOME:-~/.config}/dropflow`. Windows settings remain in `%APPDATA%/DropFlow`.

## Optional conversion helpers

On Debian/Ubuntu, install only the helpers you need:

```bash
sudo apt install libreoffice tesseract-ocr tesseract-ocr-ara unrar-free
```

LibreOffice provides Office rendering; Microsoft Office COM is Windows-only. RAR support varies by archive and installed backend. FFmpeg is supplied by imageio-ffmpeg. DejaVu fonts improve PDF text output; install `fonts-dejavu-core` if absent. HEIC/HEIF image conversion remains unsupported.

## Remove a source installation

Quit DropFlow and disable its autostart and file-manager actions in Settings. Remove the `dropflow` application directory, `~/.local/bin/dropflow`, the `dropflow.desktop` application entry, and the `dropflow.png` hicolor icon created by the installer. Keep the configuration directory to preserve preferences, or remove it separately.

## Validation scope

Automated checks cover platform paths/integration, instance locking, process cancellation, conversions, real Tk workflows, PDF organization and batch retry. CI targets Windows and Ubuntu 22.04/24.04. Desktop-specific tray, Wayland shortcuts and file-manager extensions still need a check on your own desktop.
