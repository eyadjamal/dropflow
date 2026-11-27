"""Shared scrolling and focus behavior for Windows and X11/Wayland Tk."""
def bind_scroll(widget, canvas):
    def wheel(event):
        if getattr(event, "num", None) == 4:
            amount = -1
        elif getattr(event, "num", None) == 5:
            amount = 1
        else:
            delta = getattr(event, "delta", 0)
            amount = -int(delta / 120) if abs(delta) >= 120 else (-1 if delta > 0 else 1 if delta < 0 else 0)
        canvas.yview_scroll(amount, "units")
        return "break"
    if widget.winfo_class() != "TCombobox":
        for event in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            widget.bind(event, wheel)
    for child in widget.winfo_children():
        bind_scroll(child, canvas)
