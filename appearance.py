"""Local appearance tokens for DropFlow (no Tk dependency)."""
from __future__ import annotations

import os

try:
    import winreg
except ImportError:  # pragma: no cover
    winreg = None

THEME_ORDER = ["system", "midnight", "slate", "ocean", "forest",
               "rose", "sepia", "light", "high_contrast"]

THEME_LABELS = {
    "system": "System (Auto)",
    "midnight": "Midnight",
    "slate": "Slate",
    "ocean": "Ocean",
    "forest": "Forest",
    "rose": "Rose",
    "sepia": "Sepia",
    "light": "Light",
    "high_contrast": "High Contrast",
}

THEMES = {
    "midnight": dict(
        bg="#181825", fg="#cdd6f4", accent="#cba6f7", accent_hi="#e2cffb",
        surface="#1f1f31", hover="#313244", subtle="#7f849c",
        green="#a6e3a1", red="#f38ba8"),
    "slate": dict(
        bg="#111827", fg="#e5e7eb", accent="#38bdf8", accent_hi="#7dd3fc",
        surface="#1b2433", hover="#263244", subtle="#94a3b8",
        green="#4ade80", red="#fb7185"),
    "ocean": dict(
        bg="#081e26", fg="#d7f3f8", accent="#22d3ee", accent_hi="#67e8f9",
        surface="#102d38", hover="#173e4b", subtle="#7aa9b5",
        green="#2dd4bf", red="#ff7b8a"),
    "forest": dict(
        bg="#0d1c14", fg="#d9f5e4", accent="#34d399", accent_hi="#6ee7b7",
        surface="#14281c", hover="#1d3827", subtle="#86a894",
        green="#4ade80", red="#fb7185"),
    "rose": dict(
        bg="#1c1017", fg="#fbe4ee", accent="#fb7185", accent_hi="#fda4af",
        surface="#2a1822", hover="#3a2230", subtle="#b08a9b",
        green="#4ade80", red="#fb7185"),
    "sepia": dict(
        bg="#efe4cf", fg="#3a2c24", accent="#8a5a2b", accent_hi="#a9713a",
        surface="#f8efdf", hover="#e2d3bb", subtle="#6f5a49",
        green="#2f7d4f", red="#a63a32"),
    "light": dict(
        bg="#f4f6fb", fg="#1e2530", accent="#2563eb", accent_hi="#3b82f6",
        surface="#ffffff", hover="#e7edf6", subtle="#5d6b7d",
        green="#15803d", red="#b91c1c"),
    "high_contrast": dict(
        bg="#000000", fg="#ffffff", accent="#ffff00", accent_hi="#ffff99",
        surface="#111111", hover="#333333", subtle="#d0d0d0",
        green="#00ff66", red="#ff5555"),
}


def _reg_dword(root, path, name, default=0):
    if winreg is None:
        return default
    try:
        with winreg.OpenKey(root, path) as key:
            value, _ = winreg.QueryValueEx(key, name)
        return int(value)
    except Exception:
        return default


def system_prefers_light() -> bool:
    try:
        if winreg is None:
            return False
        value = _reg_dword(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
            "AppsUseLightTheme", 0)
        return value == 1
    except Exception:
        return False


def system_accent() -> str | None:
    """Read the Windows accent colour (stored as 0xAABBGGRR)."""
    if winreg is None:
        return None
    try:
        raw = _reg_dword(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\DWM", "AccentColor", -1)
        if raw < 0:
            return None
        raw &= 0xFFFFFFFF
        r, g, b = raw & 0xFF, (raw >> 8) & 0xFF, (raw >> 16) & 0xFF
        return f"#{r:02x}{g:02x}{b:02x}"
    except Exception:
        return None


def resolve_theme(name: str, accent: str | None = None) -> tuple[str, dict]:
    chosen = name if name in THEMES or name == "system" else "midnight"
    if chosen == "system":
        chosen = "light" if system_prefers_light() else "midnight"
    tokens = dict(THEMES[chosen])
    if accent:
        tokens["accent"] = normalize_hex(accent, tokens["accent"])
        tokens["accent_hi"] = lighten(tokens["accent"], 0.22)
    return chosen, tokens


def normalize_hex(value: str | None, fallback: str) -> str:
    if not value:
        return fallback
    text = str(value).strip()
    if not text.startswith("#"):
        text = "#" + text
    if len(text) == 4:
        text = "#" + "".join(ch * 2 for ch in text[1:])
    if len(text) != 7:
        return fallback
    try:
        int(text[1:], 16)
        return text.lower()
    except ValueError:
        return fallback


def _rgb(hex_color: str) -> tuple[int, int, int]:
    color = normalize_hex(hex_color, "#000000")
    return int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)


def _hex(r: int, g: int, b: int) -> str:
    return "#{:02x}{:02x}{:02x}".format(max(0, min(255, r)),
                                       max(0, min(255, g)),
                                       max(0, min(255, b)))


def lighten(hex_color: str, amount: float) -> str:
    r, g, b = _rgb(hex_color)
    return _hex(int(r + (255 - r) * amount), int(g + (255 - g) * amount),
                int(b + (255 - b) * amount))


def darken(hex_color: str, amount: float) -> str:
    r, g, b = _rgb(hex_color)
    return _hex(int(r * (1 - amount)), int(g * (1 - amount)), int(b * (1 - amount)))


def _luminance(hex_color: str) -> float:
    values = []
    for value in _rgb(hex_color):
        c = value / 255.0
        values.append(c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4)
    return 0.2126 * values[0] + 0.7152 * values[1] + 0.0722 * values[2]


def contrast_ratio(a: str, b: str) -> float:
    la, lb = _luminance(a), _luminance(b)
    high, low = max(la, lb), min(la, lb)
    return (high + 0.05) / (low + 0.05)


def readable_text(bg: str) -> str:
    return "#111111" if contrast_ratio("#ffffff", bg) < contrast_ratio("#111111", bg) else "#ffffff"


def safe_accent(color: str, bg: str, minimum: float = 4.5) -> tuple[str, float]:
    """Return an accent adjusted toward the nearest readable shade."""
    color = normalize_hex(color, "#4c8dff")
    if contrast_ratio(color, bg) >= minimum:
        return color, contrast_ratio(color, bg)
    # Try lightening for dark backgrounds, darkening for light backgrounds.
    target = "#ffffff" if _luminance(bg) < 0.4 else "#000000"
    best, best_ratio = color, contrast_ratio(color, bg)
    for step in range(1, 21):
        candidate = _mix(color, target, step / 20.0)
        ratio = contrast_ratio(candidate, bg)
        if ratio > best_ratio:
            best, best_ratio = candidate, ratio
        if ratio >= minimum:
            return candidate, ratio
    return best, best_ratio


def _mix(a: str, b: str, amount: float) -> str:
    ar, ag, ab = _rgb(a)
    br, bg_, bb = _rgb(b)
    return _hex(int(ar + (br - ar) * amount),
                int(ag + (bg_ - ag) * amount),
                int(ab + (bb - ab) * amount))
