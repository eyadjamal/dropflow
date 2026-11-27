# Developing DropFlow 3.4.0

Use Windows x64 or Linux and Python 3.10+ (3.12 recommended). Keep the Python modules together.

```powershell
python -m pip install -r requirements.txt
python -m pip install pyinstaller pywin32
python -m unittest discover -s tests -v
python DropFlow.pyw --selftest --console
```

Install Inno Setup 6, then run `./build.ps1 -Python python` in PowerShell. The committed spec collects the conversion libraries and explicitly excludes pillow_heif and _pillow_heif. Confirm those codecs are absent from the built distribution.

The public installer is `shell/installer/DropFlow-Setup-Classic.iss`; it packages `dist350/DropFlow`, installs per user and registers the classic Explorer menu. The modern-menu package is development-only and not bundled in the public setup. Current builds are unsigned. Preserve LICENSE, package metadata and notices when distributing.

## Modules

- DropFlow.pyw: composition, Windows/tray integration, existing screens and conversion handlers.
- action_menu.py / quality_presets.py: menu and quality behavior.
- batch_jobs.py: per-file/combined execution and cancellation.
- saved_presets.py / output_policy.py: named settings and scoped output paths.
- output_panel.py / ui_theme.py: output review and shared ttk styling.
- pdf_organizer.py / pdf_organizer_ui.py: page model/export and background-rendered thumbnails.
- office_converter.py / media_converter.py: conversion engines.
- appearance.py / i18n.py / app_update.py: themes, translations and update checks.
- tests/: unit/integration checks.

ARCHITECTURE.md describes remaining extraction work; DESIGN.md describes the UI contract.

Optional Office/OCR/archive helpers remain external. Automated tests cover presets, output naming, collisions, PDF ordering/rotation/undo, cancellation, removed image formats, IPC and existing settings/converter behavior. Native Tk smoke checks cover real conversion/retry, dark/light, Arabic, keyboard navigation and scaling. Office fidelity depends on the available engine.

## Linux development and packaging

Install Python Tk, venv, Xvfb and fonts through your distribution. In a virtual environment, install requirements.txt and optionally requirements-x11.txt, then run the same unit suite. Headless GUI checks:

```bash
xvfb-run -a python DropFlow.pyw --selftest --console
xvfb-run -a python tests/gui_smoke.py
python -m pip install pyinstaller
python -m PyInstaller --noconfirm --distpath dist-linux --workpath build-linux DropFlow.spec
```

Build on Linux: PyInstaller does not cross-compile Windows binaries to Linux. Build on the oldest supported glibc distribution. Preserve LICENSE and THIRD_PARTY_NOTICES.txt beside the executable. See LINUX.md for integration and limitations.
