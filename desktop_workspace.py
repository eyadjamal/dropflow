"""Shared desktop workspace; quick tasks still use the floating drop zone."""
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from platform_runtime import IS_WINDOWS, open_file
from recent_activity import clean_history, existing_inputs

class Workspace(ttk.Frame):
    def __init__(self, app, persist, translate=lambda s: s):
        super().__init__(app.root, padding=24)
        self.app, self.persist, self.tr = app, persist, translate
        root = app.root
        root.title("DropFlow")
        root.protocol("WM_DELETE_WINDOW", root.withdraw if IS_WINDOWS else app.quit)
        root.minsize(620, 520)
        self.pack(fill="both", expand=True)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)
        header = ttk.Frame(self)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 18))
        ttk.Label(header, text="DROPFLOW / WORKSPACE", style="Eyebrow.TLabel").pack(anchor="w")
        ttk.Label(header, text=self.tr("Your files. Ready for anything."), style="Title.TLabel").pack(anchor="w", pady=(6, 3))
        ttk.Label(header, text=self.tr("Convert, organize and find your latest outputs in one place."),
                  style="Muted.TLabel", wraplength=640).pack(anchor="w")
        drop = ttk.Frame(self, style="Card.TFrame", padding=20)
        drop.grid(row=1, column=0, sticky="ew", pady=(0, 18))
        ttk.Label(drop, text=self.tr("Drop files here"), style="CardTitle.TLabel").pack(anchor="w")
        ttk.Label(drop, text=self.tr("PDFs, images, documents, video and archives"), style="CardMuted.TLabel").pack(anchor="w", pady=(4, 14))
        buttons = ttk.Frame(drop, style="CardBody.TFrame")
        buttons.pack(fill="x")
        ttk.Button(buttons, text=self.tr("Choose files…"), command=self.choose_files, style="Primary.TButton").pack(side="left")
        ttk.Button(buttons, text=self.tr("Choose folder…"), command=self.choose_folder).pack(side="left", padx=8)
        ttk.Button(buttons, text=self.tr("Quick drop zone"), command=self.show_task, style="Ghost.TButton").pack(side="right")
        recent_header = ttk.Frame(self)
        recent_header.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        ttk.Label(recent_header, text=self.tr("Recent activity"), style="Heading.TLabel").pack(side="left")
        ttk.Button(recent_header, text=self.tr("Clear recent"), command=self.clear_history, style="Ghost.TButton").pack(side="right")
        card = ttk.Frame(self, style="Card.TFrame", padding=10)
        card.grid(row=3, column=0, sticky="nsew")
        self.tree = ttk.Treeview(card, columns=("action", "result", "when"), show="headings", height=4, selectmode="browse")
        for key, title, width in (("action", "Action", 290), ("result", "Result", 130), ("when", "When", 130)):
            self.tree.heading(key, text=self.tr(title))
            self.tree.column(key, width=width, minwidth=80, stretch=key == "action")
        scroll = ttk.Scrollbar(card, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True)
        self.empty = ttk.Label(card, text=self.tr("No recent jobs yet"), style="CardMuted.TLabel")
        self.tree.bind("<<TreeviewSelect>>", self.selection_changed)
        self.tree.bind("<Double-1>", lambda e: self.use_inputs())
        actions = ttk.Frame(self)
        actions.grid(row=4, column=0, sticky="ew", pady=(8, 0))
        self.reuse = ttk.Button(actions, text=self.tr("Use inputs again"), command=self.use_inputs)
        self.reuse.pack(side="left")
        self.open_output = ttk.Button(actions, text=self.tr("Open output folder"), command=self.open_folder, style="Ghost.TButton")
        self.open_output.pack(side="left", padx=8)
        self.notice = tk.StringVar()
        ttk.Label(self, textvariable=self.notice, style="Muted.TLabel", wraplength=650).grid(row=5, column=0, sticky="ew", pady=8)
        footer = ttk.Frame(self)
        footer.grid(row=6, column=0, sticky="ew")
        self.remember = tk.BooleanVar(value=app.cfg.get("remember_recent", True))
        ttk.Checkbutton(footer, text=self.tr("Remember recent activity locally"), variable=self.remember,
                        command=self.set_remember).pack(side="left")
        ttk.Button(footer, text=self.tr("Appearance"), command=app._open_appearance, style="Ghost.TButton").pack(side="right")
        ttk.Button(footer, text=self.tr("Settings"), command=app._open_settings, style="Ghost.TButton").pack(side="right")
        ttk.Label(self, text=self.tr("Ctrl+O: choose files · Recent activity stores paths, not file contents."),
                  style="Muted.TLabel", wraplength=650).grid(row=7, column=0, sticky="ew", pady=(8, 0))
        root.bind("<Control-o>", lambda e: self.choose_files())
        try:
            from tkinterdnd2 import DND_FILES
            def dropped(event):
                self.app.show_paths(list(root.tk.splitlist(event.data)))
                return event.action
            for widget in (root, drop):
                # ttk frames expose the registered Tcl command through Tk.
                widget.drop_target_register(DND_FILES)
                widget.dnd_bind("<<Drop>>", dropped)
        except (tk.TclError, AttributeError):
            pass
        self.refresh()

    def choose_files(self):
        if self.job_running():
            return
        paths = filedialog.askopenfilenames(parent=self.app.root)
        if paths:
            self.app.show_paths(list(paths))

    def choose_folder(self):
        if self.job_running():
            return
        path = filedialog.askdirectory(parent=self.app.root)
        if path:
            self.app.show_paths([path])

    def job_running(self):
        win = self.app.win
        if win is not None and win.alive and win.busy:
            self.notice.set(self.tr("A job is running. Finish or cancel it before adding files."))
            self.show_task()
            return True
        return False

    def show_task(self):
        win = self.app.win
        if win is not None and win.alive and not win.closing:
            win.top.deiconify()
            win.top.lift()
        else:
            self.app._toggle()

    def refresh(self):
        selected = self.tree.selection()
        selected_id = self.records[int(selected[0])]["id"] if selected and hasattr(self, "records") else None
        self.records = clean_history(self.app.cfg.get("recent_activity", []))
        if self.records:
            self.empty.place_forget()
        else:
            self.empty.place(relx=.5, rely=.55, anchor="center")
        self.tree.delete(*self.tree.get_children())
        for index, record in enumerate(self.records):
            try:
                when = datetime.fromisoformat(record["at"]).astimezone().strftime("%d %b · %H:%M")
            except ValueError:
                when = ""
            status = record["status"].replace("failed", self.tr("Failed")).replace("cancelled", self.tr("Cancelled"))
            self.tree.insert("", "end", iid=str(index), values=(self.tr(record["action"]), status, when))
            if record["id"] == selected_id:
                self.tree.selection_set(str(index))
        if self.records and not self.tree.selection():
            self.tree.selection_set("0")
        self.notice.set(self.tr("Select a recent job to reuse its inputs or open its output folder.") if self.records
                        else self.tr("Your completed jobs will appear here. Start by choosing files above."))
        self.selection_changed()

    def selected_record(self):
        selected = self.tree.selection()
        return self.records[int(selected[0])] if selected else None

    def selection_changed(self, event=None):
        record = self.selected_record()
        self.reuse.configure(state="normal" if record and record["sources"] and record["complete_inputs"] else "disabled")
        self.open_output.configure(state="normal" if record and record["outputs"] else "disabled")

    def use_inputs(self):
        if self.job_running():
            return
        record = self.selected_record()
        if not record:
            return
        paths, missing = existing_inputs(record)
        if missing or not paths:
            self.notice.set(self.tr("Some inputs are missing. Choose files again."))
            return
        self.app.show_paths([str(p) for p in paths])

    def open_folder(self):
        record = self.selected_record()
        if record:
            path = next((Path(p) for p in record["outputs"] if Path(p).exists()), None)
            if path:
                try:
                    open_file(path, reveal=True)
                    return
                except OSError:
                    pass
            self.notice.set(self.tr("Output unavailable. It may have been moved or deleted."))

    def clear_history(self):
        if messagebox.askyesno(self.tr("Clear recent"), self.tr("Remove recent activity? Your files will stay unchanged."), parent=self.app.root):
            self.app.cfg["recent_activity"] = []
            self.persist(self.app.cfg)
            self.refresh()

    def set_remember(self):
        self.app.cfg["remember_recent"] = self.remember.get()
        self.persist(self.app.cfg)

def open_workspace(app, persist, translate=lambda s: s):
    workspace = getattr(app, "workspace", None)
    if workspace is None or not workspace.winfo_exists():
        app.workspace = workspace = Workspace(app, persist, translate)
    else:
        workspace.refresh()
    root = app.root
    root.update_idletasks()
    width = min(max(760, root.winfo_reqwidth()), root.winfo_screenwidth() - 40)
    height = min(max(620, root.winfo_reqheight()), root.winfo_screenheight() - 80)
    root.geometry(f"{width}x{height}")
    root.deiconify()
    root.lift()
    return workspace
