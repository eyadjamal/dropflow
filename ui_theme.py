"""Shared visual system: typography, semantic buttons and accessible palette."""
from tkinter import ttk, font as tkfont
from appearance import contrast_ratio

def primary_text(accent):
    return max(("#000000", "#ffffff"), key=lambda color: contrast_ratio(color, accent))

def ui_scale(widget):
    return max(.8, widget.winfo_fpixels("1i") / 96.0)

def configure_widgets(root, colors):
    style = ttk.Style(root)
    bg, fg, surface, accent, hover = (colors[k] for k in ("bg", "fg", "surface", "accent", "hover"))
    muted = colors.get("subtle", fg)
    ink = primary_text(accent)
    scale = ui_scale(root)
    families = set(tkfont.families(root))
    font = next((name for name in ("Segoe UI", "Noto Sans", "DejaVu Sans") if name in families), "TkDefaultFont")
    style.configure(".", font=(font, 10))
    style.configure("TFrame", background=bg)
    style.configure("TLabel", background=bg, foreground=fg)
    style.configure("Muted.TLabel", background=bg, foreground=muted, font=(font, 9))
    style.configure("Eyebrow.TLabel", background=bg, foreground=accent, font=(font, 9, "bold"))
    style.configure("Title.TLabel", background=bg, foreground=fg, font=(font, 19, "bold"))
    style.configure("Heading.TLabel", background=bg, foreground=fg, font=(font, 12, "bold"))
    style.configure("Card.TFrame", background=surface, bordercolor=hover, borderwidth=1, relief="solid")
    style.configure("CardBody.TFrame", background=surface, borderwidth=0, relief="flat")
    style.configure("Card.TLabel", background=surface, foreground=fg)
    style.configure("CardTitle.TLabel", background=surface, foreground=fg, font=(font, 10, "bold"))
    style.configure("CardMuted.TLabel", background=surface, foreground=muted, font=(font, 9))
    style.configure("Card.TEntry", fieldbackground=bg, foreground=fg, insertcolor=fg, padding=8)
    style.configure("TButton", background=surface, foreground=fg, bordercolor=hover,
                    lightcolor=surface, darkcolor=surface, borderwidth=1, relief="flat", padding=(12, 8))
    style.map("TButton", background=[("disabled", surface), ("active", hover)],
              foreground=[("disabled", muted), ("active", fg)], bordercolor=[("focus", accent)])
    style.configure("Primary.TButton", background=accent, foreground=ink,
                    bordercolor=accent, lightcolor=accent, darkcolor=accent, font=(font, 10, "bold"))
    style.map("Primary.TButton", background=[("disabled", hover), ("pressed", accent), ("active", accent)],
              foreground=[("disabled", muted), ("active", ink)], bordercolor=[("focus", fg)])
    style.configure("Ghost.TButton", background=bg, foreground=muted, borderwidth=0, padding=(10, 7))
    style.map("Ghost.TButton", background=[("active", surface)], foreground=[("active", accent)])
    style.configure("Favorite.TButton", foreground=accent, background=bg, borderwidth=0)
    style.configure("Action.TButton", anchor="w", padding=(13, 10), borderwidth=0)
    style.configure("Section.TButton", anchor="w", background=bg, foreground=muted, borderwidth=0, padding=(6, 9))
    style.map("Section.TButton", background=[("active", surface)], foreground=[("active", fg)])
    for name in ("TCheckbutton", "TRadiobutton"):
        style.configure(name, background=bg, foreground=fg, indicatorbackground=surface, padding=5)
        style.map(name, background=[("active", bg)], foreground=[("active", accent)])
    style.map("TEntry", bordercolor=[("focus", accent)])
    style.map("Card.TEntry", bordercolor=[("focus", accent)])
    style.configure("TPanedwindow", background=bg)
    style.configure("Treeview", background=surface, fieldbackground=surface, foreground=fg,
                    bordercolor=hover, lightcolor=surface, darkcolor=surface, relief="flat",
                    rowheight=round(32 * scale), borderwidth=0)
    style.map("Treeview", background=[("selected", hover)], foreground=[("selected", accent)])
    style.configure("Treeview.Heading", background=bg, foreground=muted, padding=(8, 8), font=(font, 9, "bold"),
                    borderwidth=0, relief="flat", bordercolor=hover, lightcolor=bg, darkcolor=bg)
    style.configure("Vertical.TScrollbar", background=surface, troughcolor=bg, arrowcolor=muted,
                    bordercolor=bg, lightcolor=surface, darkcolor=surface, borderwidth=0, arrowsize=10)
