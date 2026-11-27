"""Pointer lighting for ttk buttons, preserving native bindings and focus."""
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageDraw, ImageTk


def install_button_light(root):
    if getattr(root, "_dropflow_light", False):
        return
    root._dropflow_light = True
    style = ttk.Style(root)
    # One transient style and image serve the single hovered button.
    image = tk.PhotoImage(master=root)
    root._dropflow_light_image = image
    element = "DropFlow.light"
    style.element_create(element, "image", image, sticky="nsew")
    active = None
    original = ""
    position = None
    pending = None

    def leave(event):
        nonlocal active, pending
        if active is not event.widget:
            return
        if pending:
            root.after_cancel(pending)
            pending = None
        if active.winfo_exists():
            active.configure(style=original)
        active = None

    def paint():
        nonlocal pending
        pending = None
        if active is None or not active.winfo_exists() or active.instate(["disabled"]):
            return
        name = original or "TButton"
        color = style.lookup(name, "background", ("active",)) or "#273547"
        base = tuple(v // 257 for v in active.winfo_rgb(color))
        size = active.winfo_width(), active.winfo_height()
        layer = Image.new("RGB", size, base)
        draw = ImageDraw.Draw(layer)
        x, y = position
        radius = max(36, size[1] * 2)
        for r in range(radius, 0, -2):
            amount = .20 * (1 - r / radius) ** 2
            tint = tuple(round(v + (255 - v) * amount) for v in base)
            draw.ellipse((x-r, y-r, x+r, y+r), fill=tint)
        fresh = ImageTk.PhotoImage(layer, master=root)
        # Tk style elements retain their original image name.
        image.configure(width=size[0], height=size[1])
        root.tk.call(str(image), "copy", str(fresh))
        active.configure(style=active.cget("style"))

    def move(event):
        nonlocal active, original, position, pending
        button = event.widget
        if button.instate(["disabled"]) or root.tk.getboolean(root.tk.getvar("::dropflow_no_light")):
            return
        if active is not button:
            original = str(button.cget("style"))
            name = "Reveal." + (original or "TButton")
            style.layout(name, [(element, {"sticky":"nswe", "children":[("Button.focus", {"sticky":"nswe", "children":[("Button.padding", {"sticky":"nswe", "children":[("Button.label", {"sticky":"nswe"})]})]})]})])
            active = button
            button.configure(style=name)
        position = event.x, event.y
        if pending is None:
            pending = root.after(15, paint)

    root.bind_class("TButton", "<Motion>", move, add="+")
    root.bind_class("TButton", "<Leave>", leave, add="+")
    root.bind_class("TButton", "<Destroy>", leave, add="+")

