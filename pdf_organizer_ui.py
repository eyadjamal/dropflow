"""Thumbnail organizer. PDF rendering stays in a single background worker."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from uuid import uuid4
from io import BytesIO
from pathlib import Path
import queue
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import pymupdf as fitz
from pdf_organizer import PageModel, read_pages
from ui_theme import ui_scale

class PDFOrganizer(tk.Toplevel):
    PAGE_SIZE = 24

    def __init__(self, master, paths, accept, cancel, translate=lambda s: s, theme=None, initial_plan=None):
        pages = read_pages(paths)
        if initial_plan:
            lookup = {(p.source, p.number): p for p in pages}
            pages = [replace(lookup[(str(Path(p["source"]).resolve()), p["number"])],
                             rotation=p["rotation"], uid=uuid4().hex) for p in initial_plan]
        super().__init__(master)
        self.colors = theme or {"bg":"#181824", "fg":"#e5e7ef", "surface":"#242436", "accent":"#80aaff", "hover":"#444455"}
        self.configure(bg=self.colors["bg"])
        self.tr, self.accept, self.cancel = translate, accept, cancel
        self.title(translate("Organize PDF pages"))
        self.scale = ui_scale(self)
        self.px = lambda value: round(value * self.scale)
        width = min(self.px(1120), self.winfo_screenwidth()-60)
        height = min(self.px(800), self.winfo_screenheight()-80)
        self.geometry(f"{width}x{height}")
        self.minsize(min(self.px(860), width), min(self.px(580), height))
        self.model = PageModel(pages)
        self.selected = self.model.pages[0].uid if self.model.pages else None
        self.offset, self.generation = 0, 0
        self.closed, self.dragged = False, None
        self.pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="PDFThumbnail")
        self.events = queue.Queue()
        self.future = None
        self.preview_future = None
        self.images, self.cards = {}, {}
        self.protocol("WM_DELETE_WINDOW", self.close)
        header = ttk.Frame(self, padding=(self.px(22), self.px(18), self.px(22), self.px(12)))
        header.pack(fill="x")
        ttk.Button(header, text=translate("Add PDFs…"), command=self.add).pack(side="right", padx=(12, 0))
        ttk.Label(header, text=translate("DROPFLOW / PDF WORKSPACE"), style="Eyebrow.TLabel").pack(anchor="w")
        ttk.Label(header, text=translate("Organize PDF pages"), style="Title.TLabel").pack(anchor="w", pady=4)
        ttk.Label(header, text=translate("Create a new PDF. Your originals stay unchanged."), style="Muted.TLabel").pack(anchor="w")
        toolbar = ttk.Frame(self, padding=(self.px(22), 0, self.px(22), self.px(14)))
        toolbar.pack(fill="x")
        for button_index, (label, command) in enumerate((("← Move", lambda: self.move(-1)), ("Move →", lambda: self.move(1)),
                               ("Rotate left", lambda: self.rotate(-90)), ("Rotate right", lambda: self.rotate(90)),
                               ("Delete page", self.remove), ("Undo", self.undo))):
            ttk.Button(toolbar, text=translate(label), command=command,
                       style="Ghost.TButton" if label == "Undo" else "TButton").grid(
                           row=0, column=button_index, sticky="ew", padx=(0, self.px(6)))
        main = ttk.Panedwindow(self, orient="horizontal")
        main.pack(fill="both", expand=True, padx=self.px(22))
        grid = ttk.Frame(main)
        main.add(grid, weight=3)
        self.canvas = tk.Canvas(grid, bg=self.colors["bg"], highlightthickness=0)
        scroll = ttk.Scrollbar(grid, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.canvas.pack(fill="both", expand=True)
        self.content = ttk.Frame(self.canvas)
        self.canvas.create_window(0, 0, window=self.content, anchor="nw")
        self.content.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<MouseWheel>", self.wheel)
        self.canvas.bind("<Configure>", self.layout_cards)
        preview = ttk.Frame(main, padding=self.px(16), style="Card.TFrame")
        main.add(preview, weight=2)
        ttk.Label(preview, text=translate("Selected page preview"), style="CardTitle.TLabel").pack(anchor="w", pady=(0, self.px(10)))
        self.preview_label = ttk.Label(preview, anchor="center", style="Card.TLabel")
        self.preview_label.pack(fill="both", expand=True)
        self.detail = ttk.Label(preview, wraplength=self.px(290), style="CardMuted.TLabel")
        self.detail.pack(fill="x", pady=(self.px(12), 0))
        nav = ttk.Frame(self, padding=(self.px(22), self.px(14), self.px(22), self.px(8)))
        nav.pack(fill="x")
        ttk.Button(nav, text=translate("Previous"), command=lambda: self.navigate(-1), style="Ghost.TButton").pack(side="left")
        self.count = ttk.Label(nav, style="Muted.TLabel")
        self.count.pack(side="left", padx=self.px(10))
        ttk.Button(nav, text=translate("Next"), command=lambda: self.navigate(1), style="Ghost.TButton").pack(side="left")
        ttk.Button(nav, text=translate("Save PDF"), command=self.save, style="Primary.TButton").pack(side="right")
        ttk.Button(nav, text=translate("Cancel"), command=self.close, style="Ghost.TButton").pack(side="right", padx=self.px(6))
        ttk.Label(self, text=translate("Drag to reorder · Select to edit · Ctrl+Z to undo"),
                  style="Muted.TLabel").pack(fill="x", padx=self.px(22), pady=(0, self.px(14)))
        self.bind("<Delete>", lambda e: self.remove())
        self.bind("<Control-z>", lambda e: self.undo())
        self.bind("<Control-Left>", lambda e: self.move(-1))
        self.bind("<Control-Right>", lambda e: self.move(1))
        self.bind("<Escape>", lambda e: self.close())
        self.refresh()
        self.poll_id = self.after(40, self.poll)

    def wheel(self, event):
        self.canvas.yview_scroll(-int(event.delta / 120), "units")

    def current(self):
        return next((p for p in self.model.pages if p.uid == self.selected), None)

    def refresh(self):
        self.generation += 1
        generation = self.generation
        if self.future:
            self.future.cancel()
        for child in self.content.winfo_children():
            child.destroy()
        self.images, self.cards = {}, {}
        self.offset = min(self.offset, max(0, ((len(self.model.pages) - 1) // self.PAGE_SIZE) * self.PAGE_SIZE))
        visible = self.model.pages[self.offset:self.offset + self.PAGE_SIZE]
        for index, page in enumerate(visible):
            card = tk.Frame(self.content, bg=self.colors["surface"], highlightthickness=2,
                            highlightbackground=self.colors["hover"], width=self.px(156), height=self.px(228))
            card.pack_propagate(False)
            card.grid(row=index // 4, column=index % 4, padx=self.px(6), pady=self.px(6))
            top = tk.Frame(card, bg=self.colors["surface"])
            top.pack(fill="x", padx=self.px(10), pady=(self.px(7), 0))
            number = tk.Label(top, text=f"{self.offset+index+1:02}", bg=self.colors["surface"],
                              fg=self.colors["accent"], font=("Segoe UI", 9, "bold"))
            number.pack(side="left")
            rotation = tk.Label(top, text=f"{page.rotation}°" if page.rotation else "", bg=self.colors["surface"],
                                fg=self.colors.get("subtle", self.colors["fg"]), font=("Segoe UI", 8))
            rotation.pack(side="right")
            paper = tk.Frame(card, bg=self.colors["surface"], height=self.px(165))
            paper.pack(fill="x", pady=self.px(4))
            paper.pack_propagate(False)
            image = ttk.Label(paper, text=self.tr("Loading…"), anchor="center", style="Card.TLabel")
            image.pack(expand=True)
            name = Path(page.source).name
            label = ttk.Label(card, text=name[:18] + ("…" if len(name)>18 else ""),
                              anchor="w", style="CardMuted.TLabel")
            label.pack(fill="x", padx=self.px(10))
            self.cards[page.uid] = (card, image)
            for widget in (card, top, number, rotation, paper, image, label):
                widget.page_uid = page.uid
                widget.bind("<Button-1>", lambda e, uid=page.uid: self.select(uid))
                widget.bind("<B1-Motion>", self.drag)
                widget.bind("<ButtonRelease-1>", self.drop)
                widget.bind("<MouseWheel>", self.wheel)
        self.count.configure(text=f"{self.offset + 1 if visible else 0}–{self.offset + len(visible)} / {len(self.model.pages)}")
        self.layout_cards()
        self.future = self.pool.submit(self.render_batch, generation, visible)
        self.select(self.selected)

    def layout_cards(self, event=None):
        columns = max(1, self.canvas.winfo_width() // self.px(168))
        for index, (card, _) in enumerate(self.cards.values()):
            card.grid_configure(row=index // columns, column=index % columns)

    def render_batch(self, generation, pages):
        for page in pages:
            if self.closed or generation != self.generation:
                return
            self.render(generation, page, False)

    def render(self, generation, page, preview):
        try:
            with fitz.open(page.source) as document:
                p = document[page.number]
                p.set_rotation((p.rotation + page.rotation) % 360)
                width, height = (self.px(310), self.px(420)) if preview else (self.px(124), self.px(160))
                scale = min(width / p.rect.width, height / p.rect.height)
                data = p.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False).tobytes("png")
            self.events.put((generation, page.uid, preview, data, ""))
        except Exception as exc:
            self.events.put((generation, page.uid, preview, None, str(exc)))

    def poll(self):
        if self.closed:
            return
        for _ in range(40):
            try:
                generation, uid, preview, data, error = self.events.get_nowait()
            except queue.Empty:
                break
            if generation != self.generation:
                continue
            if data:
                photo = ImageTk.PhotoImage(Image.open(BytesIO(data)))
                if preview and uid == self.selected:
                    self.preview_image = photo
                    self.preview_label.configure(image=photo, text="")
                elif not preview and uid in self.cards:
                    self.images[uid] = photo
                    self.cards[uid][1].configure(image=photo, text="", width=0)
                    self.cards[uid][1].pack_configure(ipady=0)
            elif preview and uid == self.selected:
                self.detail.configure(text=error)
        self.poll_id = self.after(40, self.poll)

    def select(self, uid):
        self.selected = uid
        self.dragged = None
        for key, (card, _) in self.cards.items():
            card.configure(highlightbackground=self.colors["accent"] if key == uid else self.colors["hover"])
        page = self.current()
        self.preview_label.configure(image="", text=self.tr("Loading…") if page else "")
        if page:
            self.detail.configure(text=f"{Path(page.source).name}\n{self.tr('Source page')} {page.number + 1} · +{page.rotation}°")
            if self.preview_future:
                self.preview_future.cancel()
            self.preview_future = self.pool.submit(self.render, self.generation, page, True)
        else:
            self.detail.configure(text=self.tr("No pages selected"))

    def drag(self, event):
        self.dragged = self.selected

    def drop(self, event):
        if not self.dragged:
            return
        widget = self.winfo_containing(event.x_root, event.y_root)
        while widget and not hasattr(widget, "page_uid"):
            widget = widget.master
        if widget and widget.page_uid != self.dragged:
            target = next(i for i, p in enumerate(self.model.pages) if p.uid == widget.page_uid)
            self.model.move(self.dragged, target)
            self.refresh()
        self.dragged = None

    def move(self, delta):
        page = self.current()
        if page:
            index = self.model.pages.index(page)
            destination = max(0, min(len(self.model.pages) - 1, index + delta))
            self.model.move(page.uid, destination)
            self.offset = (destination // self.PAGE_SIZE) * self.PAGE_SIZE
            self.refresh()

    def rotate(self, degrees):
        if self.current():
            self.model.rotate(self.selected, degrees)
            self.refresh()

    def remove(self):
        if self.current():
            index = self.model.pages.index(self.current())
            self.model.remove(self.selected)
            self.selected = self.model.pages[min(index, len(self.model.pages)-1)].uid if self.model.pages else None
            self.refresh()

    def undo(self):
        self.model.undo()
        if self.selected not in {p.uid for p in self.model.pages}:
            self.selected = self.model.pages[0].uid if self.model.pages else None
        self.refresh()

    def navigate(self, direction):
        offset = self.offset + direction * self.PAGE_SIZE
        if 0 <= offset < len(self.model.pages):
            self.offset = offset
            self.canvas.yview_moveto(0)
            self.refresh()

    def add(self):
        paths = filedialog.askopenfilenames(parent=self, filetypes=[("PDF", "*.pdf")])
        if paths:
            try:
                self.model.append(read_pages(paths))
                if self.selected is None and self.model.pages:
                    self.selected = self.model.pages[0].uid
                self.refresh()
            except Exception as exc:
                messagebox.showerror(self.tr("Organize PDF pages"), str(exc), parent=self)

    def save(self):
        if not self.model.pages:
            messagebox.showinfo(self.tr("Organize PDF pages"), self.tr("Keep at least one page before saving."), parent=self)
            return
        plan = self.model.plan()
        sources = list(dict.fromkeys(p["source"] for p in plan))
        self.dispose()
        self.accept(sources, plan)

    def dispose(self):
        self.closed = True
        self.after_cancel(self.poll_id)
        self.pool.shutdown(wait=False, cancel_futures=True)
        self.destroy()

    def close(self):
        self.dispose()
        self.cancel()
