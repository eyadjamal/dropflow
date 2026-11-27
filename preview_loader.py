"""Small background preview worker. No Tk calls or retained document handles."""
from collections import OrderedDict
from pathlib import Path
from queue import Queue, Empty
import threading
from PIL import Image

def render_preview(path):
    path = Path(path)
    # Avoid expensive/oversized inputs in the quick-action surface.
    if path.stat().st_size > 80 * 1024 * 1024:
        return None
    if path.suffix.lower() == ".pdf":
        import pymupdf
        with pymupdf.open(path) as document:
            if not len(document) or document.needs_pass:
                return None
            page = document[0]
            scale = min(44 / max(1, page.rect.width), 44 / max(1, page.rect.height))
            pix = page.get_pixmap(matrix=pymupdf.Matrix(scale, scale), colorspace=pymupdf.csRGB, alpha=False)
            return Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    with Image.open(path) as image:
        if image.width * image.height > 40_000_000:
            return None
        image.thumbnail((44, 44))
        return image.convert("RGBA").copy()

class PreviewLoader:
    def __init__(self):
        self.requests, self.results = Queue(maxsize=4), Queue()
        self.closed = threading.Event()
        self.cache = OrderedDict()
        self.thread = threading.Thread(target=self._run, name="DropFlowPreview", daemon=True)
        self.thread.start()

    def request(self, token, path):
        if self.closed.is_set():
            return
        if self.requests.full():
            try:
                self.requests.get_nowait()
            except Empty:
                pass
        self.requests.put_nowait((token, Path(path)))

    def _run(self):
        while not self.closed.is_set():
            try:
                token, path = self.requests.get(timeout=.2)
            except Empty:
                continue
            try:
                stat = path.stat()
                key = (str(path.resolve()), stat.st_mtime_ns, stat.st_size)
                if key in self.cache:
                    image = self.cache.pop(key)
                else:
                    image = render_preview(path)
                self.cache[key] = image
                while len(self.cache) > 12:
                    self.cache.popitem(last=False)
            except Exception:
                image = None
            if not self.closed.is_set():
                self.results.put((token, path, image))

    def close(self):
        self.closed.set()
