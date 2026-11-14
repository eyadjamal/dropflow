"""PDF page model and transactional export; independent of Tkinter."""
from dataclasses import dataclass, replace
from pathlib import Path
from uuid import uuid4
import os
import tempfile
import pymupdf as fitz

@dataclass(frozen=True)
class Page:
    source: str
    number: int
    rotation: int = 0
    uid: str = ""

def read_pages(paths):
    result = []
    for path in paths:
        path = str(Path(path).resolve())
        with fitz.open(path) as document:
            if document.needs_pass:
                raise ValueError(f"{Path(path).name}: unlock this PDF before organizing it.")
            result.extend(Page(path, n, 0, uuid4().hex) for n in range(len(document)))
    return result

class PageModel:
    def __init__(self, pages):
        self.pages = list(pages)
        self.history = []

    def _remember(self):
        self.history.append(self.pages[:])
        self.history = self.history[-50:]

    def move(self, uid, destination):
        index = next(i for i, p in enumerate(self.pages) if p.uid == uid)
        destination = max(0, min(len(self.pages) - 1, destination))
        if index != destination:
            self._remember()
            self.pages.insert(destination, self.pages.pop(index))

    def rotate(self, uid, degrees=90):
        self._remember()
        self.pages = [replace(p, rotation=(p.rotation + degrees) % 360)
                      if p.uid == uid else p for p in self.pages]

    def remove(self, uid):
        self._remember()
        self.pages = [p for p in self.pages if p.uid != uid]

    def append(self, pages):
        self._remember()
        self.pages.extend(pages)

    def undo(self):
        if self.history:
            self.pages = self.history.pop()

    def plan(self):
        return [{"source": p.source, "number": p.number, "rotation": p.rotation}
                for p in self.pages]

def export_pages(plan, output, allowed_sources, ctx):
    if not plan:
        raise ValueError("Keep at least one page before saving.")
    allowed = {str(Path(p).resolve()) for p in allowed_sources}
    output = Path(output)
    if str(output.resolve()) in allowed:
        raise ValueError("The output must not replace an input PDF.")
    descriptor, temporary = tempfile.mkstemp(prefix=".dropflow-", suffix=".pdf", dir=output.parent)
    os.close(descriptor)
    documents = {}
    try:
        with fitz.open() as result:
            for index, item in enumerate(plan, 1):
                ctx.check()
                source = str(Path(item["source"]).resolve())
                if source not in allowed:
                    raise ValueError("The page selection contains a PDF outside this job.")
                if source not in documents:
                    documents[source] = fitz.open(source)
                document = documents[source]
                number, rotation = item["number"], item["rotation"]
                if type(number) is not int or not 0 <= number < len(document):
                    raise ValueError("A source PDF changed. Open the organizer again.")
                if rotation not in (0, 90, 180, 270):
                    raise ValueError("Invalid page rotation.")
                result.insert_pdf(document, from_page=number, to_page=number)
                page = result[-1]
                page.set_rotation((page.rotation + rotation) % 360)
                ctx.progress(f"Preparing page {index}/{len(plan)}")
            result.save(temporary, garbage=4, deflate=True)
        ctx.check()
        # Reserve the destination exclusively, then replace only our placeholder.
        descriptor = os.open(output, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.close(descriptor)
        try:
            os.replace(temporary, output)
        except BaseException:
            output.unlink(missing_ok=True)
            raise
    finally:
        for document in documents.values():
            document.close()
        Path(temporary).unlink(missing_ok=True)
    return output
