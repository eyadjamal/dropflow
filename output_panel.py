"""Reusable Tk output/preset review screen."""
from copy import deepcopy
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog
from action_menu import identity
from output_policy import validate_pattern, render_name
from saved_presets import save_preset, clean_output

class OutputPanel(ttk.Frame):
    def __init__(self, parent, action, options, paths, config, persist, run, back,
                 translate=lambda s: s, preset_id=None):
        super().__init__(parent, padding=0)
        from ui_theme import ui_scale
        scale = ui_scale(self)
        px = lambda value: round(value * scale)
        self.action, self.options = action, deepcopy(options)
        self.paths, self.config = list(paths), config
        self.persist, self.run, self.tr = persist, run, translate
        self.action_id = identity(action)
        self.records = [r for r in config.get("saved_presets", []) if r["action_id"] == self.action_id]
        defaults = config.get("output_defaults", {}).get(self.action_id, {})
        self.folder = tk.StringVar(value=defaults.get("folder", ""))
        self.pattern = tk.StringVar(value=defaults.get("pattern", ""))
        self.selected, self.name = tk.StringVar(), tk.StringVar()
        self.summary, self.preview, self.message = tk.StringVar(), tk.StringVar(), tk.StringVar()
        header = ttk.Frame(self, padding=(px(20), px(18), px(20), px(14)))
        header.pack(fill="x")
        ttk.Label(header, text=translate("READY TO CONVERT"), style="Eyebrow.TLabel").pack(anchor="w")
        ttk.Label(header, text=translate(action.label), style="Title.TLabel", wraplength=px(410)).pack(anchor="w", pady=(4, 4))
        ttk.Label(header, text=translate("Choose where your files go."), style="Muted.TLabel").pack(anchor="w")
        container = ttk.Frame(self)
        container.pack(fill="both", expand=True)
        bg = ttk.Style(self).lookup("TFrame", "background")
        self.canvas = tk.Canvas(container, width=px(440), height=min(px(540), max(px(260), self.winfo_screenheight()-px(245))), bg=bg, highlightthickness=0)
        scroll = ttk.Scrollbar(container, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        content = ttk.Frame(self.canvas, padding=(px(20), 0, px(12), px(8)))
        window = self.canvas.create_window(0, 0, window=content, anchor="nw")
        content.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(window, width=e.width))
        def card(title):
            frame = ttk.Frame(content, style="Card.TFrame", padding=px(14))
            frame.pack(fill="x", pady=(0, px(12)))
            ttk.Label(frame, text=translate(title), style="CardTitle.TLabel").pack(anchor="w", pady=(0, px(9)))
            return frame
        settings_card = card("Conversion settings")
        ttk.Label(settings_card, textvariable=self.summary, style="CardMuted.TLabel", wraplength=px(360)).pack(fill="x")
        row = ttk.Frame(settings_card, style="Card.TFrame")
        row.pack(fill="x", pady=(10, 0))
        self.combo = ttk.Combobox(row, textvariable=self.selected, state="readonly", width=23)
        self.combo.pack(side="left", expand=True, fill="x")
        self.combo.bind("<<ComboboxSelected>>", self.apply_selected)
        ttk.Button(row, text=translate("Delete"), command=self.delete_selected).pack(side="right", padx=(6, 0))
        self._refresh_choices()
        destination = card("Save destination")
        ttk.Label(destination, text=translate("Output folder"), style="CardMuted.TLabel").pack(anchor="w")
        row = ttk.Frame(destination, style="Card.TFrame")
        row.pack(fill="x", pady=(4, 3))
        ttk.Entry(row, textvariable=self.folder, width=23, style="Card.TEntry").pack(side="left", fill="x", expand=True)
        ttk.Button(row, text=translate("Browse…"), command=self.browse).pack(side="right", padx=(6, 0))
        ttk.Button(destination, text=translate("Use source folder"), command=lambda: self.folder.set(""), style="Ghost.TButton").pack(anchor="w")
        ttk.Label(destination, text=translate("Filename pattern (without extension)"), style="CardMuted.TLabel").pack(anchor="w", pady=(9, 4))
        ttk.Entry(destination, textvariable=self.pattern, style="Card.TEntry").pack(fill="x")
        ttk.Label(destination, text="{name}   {action}   {index}   {date}", style="CardMuted.TLabel").pack(anchor="w", pady=5)
        ttk.Label(destination, text=translate("Blank uses automatic naming. Existing files stay safe."), style="CardMuted.TLabel", wraplength=px(360)).pack(fill="x")
        preview_card = card("Output preview")
        ttk.Label(preview_card, textvariable=self.preview, style="CardMuted.TLabel", wraplength=px(360)).pack(fill="x")
        presets = card("Save a preset")
        ttk.Label(presets, text=translate("Save these settings for next time"), style="CardMuted.TLabel").pack(anchor="w", pady=(12, 4))
        row = ttk.Frame(presets, style="Card.TFrame")
        row.pack(fill="x")
        ttk.Entry(row, textvariable=self.name, width=23, style="Card.TEntry").pack(side="left", fill="x", expand=True)
        ttk.Button(row, text=translate("Save preset"), command=self.save).pack(side="right", padx=(6, 0))
        footer = ttk.Frame(self, padding=(px(20), px(10), px(20), px(16)))
        footer.pack(fill="x")
        ttk.Label(footer, textvariable=self.message, style="Muted.TLabel", wraplength=px(400)).pack(fill="x", pady=(0, 5))
        row = ttk.Frame(footer)
        row.pack(fill="x")
        ttk.Button(row, text=translate("Back"), command=back, style="Ghost.TButton").pack(side="left")
        ttk.Button(row, text=translate("Convert files"), command=self.submit, style="Primary.TButton").pack(side="right")
        self.folder.trace_add("write", self.update_preview)
        self.pattern.trace_add("write", self.update_preview)
        if preset_id:
            record = next((r for r in self.records if r["id"] == preset_id), None)
            if record:
                self.selected.set(record["name"])
                self.apply_selected()
        self.update_summary()
        self.update_preview()
        def wheel(event):
            self.canvas.yview_scroll(-int(event.delta/120), "units")
        def ensure_visible(event):
            widget = event.widget
            self.update_idletasks()
            y = widget.winfo_rooty() - content.winfo_rooty()
            top, height = self.canvas.canvasy(0), self.canvas.winfo_height()
            target = y if y < top else y + widget.winfo_height() - height if y + widget.winfo_height() > top + height else None
            if target is not None:
                self.canvas.yview_moveto(max(0, target) / max(1, content.winfo_height()))
        def bind_scroll(widget):
            widget.bind("<FocusIn>", ensure_visible, add="+")
            # Preserve native combobox selection wheel behavior.
            if widget.winfo_class() != "TCombobox":
                widget.bind("<MouseWheel>", wheel)
            for child in widget.winfo_children():
                bind_scroll(child)
        bind_scroll(content)
        from i18n import is_rtl
        if is_rtl():
            def align(widget):
                if widget.winfo_class() == "TLabel":
                    widget.configure(anchor="e", justify="right")
                    if widget.winfo_manager() == "pack":
                        widget.pack_configure(anchor="e")
                for child in widget.winfo_children():
                    align(child)
            align(self)

    def _refresh_choices(self):
        self.combo.configure(values=[r["name"] for r in self.records])

    def settings(self):
        output = clean_output({"folder": self.folder.get().strip(), "pattern": self.pattern.get()})
        folder = output["folder"]
        if folder:
            path = Path(folder)
            if not path.is_absolute():
                raise ValueError(self.tr("Choose an absolute output folder."))
            if path.exists() and not path.is_dir():
                raise ValueError(self.tr("The output folder is not a directory."))
        if output["pattern"]:
            for index, source in enumerate(self.paths, 1):
                render_name(output["pattern"], Path(source), self.action_id, index)
        return output

    def update_summary(self):
        labels = {"dpi":"Resolution", "resolution":"Resolution", "format":"Format", "target":"Format",
                  "duration":"Frame duration", "target_mb":"Target size", "gpu":"GPU encoding", "pages":"Pages"}
        parts = []
        for key, value in self.options.items():
            if key.startswith("_"):
                continue
            if key == "quality" and type(value) in (int, float):
                if self.action.func.__name__ == "act_extract_audio":
                    parts.append(f"{value} kbps")
                elif self.action.video_options:
                    parts.append(self.tr("Best quality" if value <= 19 else "Balanced" if value <= 25 else "Small file"))
                else:
                    parts.append(self.tr("Small file" if value <= 50 else "Balanced" if value <= 85 else "Best quality"))
            else:
                parts.append(f"{self.tr(labels.get(key, key))}: {value}")
        summary = " · ".join(parts)
        if "_pdf_plan" in self.options:
            summary = f"{len(self.options['_pdf_plan'])} {self.tr('pages')}"
        self.summary.set(summary or self.tr("Default settings"))

    def update_preview(self, *args):
        try:
            settings = self.settings()
            source = Path(self.paths[0])
            name = render_name(settings["pattern"], source, self.action_id, 1) if settings["pattern"] else self.tr("Automatic filename")
            folder = settings["folder"] or str(source.parent)
            self.preview.set(self.tr("Name preview") + ": " + str(Path(folder) / name)
                            + "\n" + self.tr("The conversion adds the correct extension."))
        except (ValueError, IndexError) as exc:
            self.preview.set(str(exc))

    def browse(self):
        folder = filedialog.askdirectory(parent=self.winfo_toplevel(),
                                         initialdir=self.folder.get() or str(Path(self.paths[0]).parent))
        if folder:
            self.folder.set(folder)

    def apply_selected(self, event=None):
        record = next((r for r in self.records if r["name"] == self.selected.get()), None)
        if record:
            plan = self.options.get("_pdf_plan")
            self.options = deepcopy(record["options"])
            if plan is not None:
                self.options["_pdf_plan"] = plan
            self.folder.set(record["output"]["folder"])
            self.pattern.set(record["output"]["pattern"])
            self.name.set(record["name"])
            self.update_summary()

    def save(self):
        try:
            self.config["saved_presets"] = save_preset(self.config.get("saved_presets", []),
                self.action_id, self.name.get(), self.options, self.settings())
            self.persist(self.config)
            self.records = [r for r in self.config["saved_presets"] if r["action_id"] == self.action_id]
            self._refresh_choices()
            self.selected.set(self.name.get().strip())
            self.message.set(self.tr("Preset saved"))
        except ValueError as exc:
            self.message.set(str(exc))

    def delete_selected(self):
        record = next((r for r in self.records if r["name"] == self.selected.get()), None)
        if record:
            self.config["saved_presets"] = [r for r in self.config["saved_presets"] if r["id"] != record["id"]]
            self.persist(self.config)
            self.records.remove(record)
            self._refresh_choices()
            self.selected.set("")
            self.name.set("")
            self.message.set(self.tr("Preset deleted"))

    def submit(self):
        try:
            output = self.settings()
            self.config.setdefault("output_defaults", {})[self.action_id] = output
            self.persist(self.config)
            self.run({**deepcopy(self.options), "_output": output})
        except (ValueError, OSError) as exc:
            self.message.set(str(exc))
