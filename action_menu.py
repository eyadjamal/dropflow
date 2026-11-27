"""Pure action metadata and menu ranking; no Tk dependencies."""
CATEGORIES = ("Convert", "PDF Tools", "Extract", "Archive")

ALIASES = {
    "compress": "small smaller shrink reduce size optimize ضغط تصغير",
    "merge": "combine join جمع دمج",
    "organize": "reorder rearrange rotate sort ترتيب تدوير",
    "extract": "unpack unzip export استخراج",
    "ocr": "scan scanned recognize searchable مسح نص",
    "jpg": "jpeg picture photo صورة",
    "png": "picture photo صورة",
    "zip": "archive package folder مجلد أرشيف",
    "audio": "sound music mp3 صوت",
}

def search_actions(actions, query, translate=lambda text: text):
    """Match intent words across both languages, labels and categories."""
    tokens = query.casefold().split()
    result = []
    for action in actions:
        text = " ".join((action.label, translate(action.label), category(action), identity(action))).casefold()
        extra = " ".join(value for key, value in ALIASES.items() if key in text)
        if all(token in text or token in extra for token in tokens):
            result.append(action)
    return result

def identity(action):
    func = action.func
    name = getattr(func, "__name__", "action")
    closure = getattr(func, "__closure__", None)
    values = [str(c.cell_contents) for c in closure or ()
              if isinstance(c.cell_contents, (str, int))]
    return name + (":" + ":".join(values) if values else "")

def category(action):
    name = getattr(action.func, "__name__", "")
    if name in {"act_zip", "act_extract_zip", "act_extract_rar", "act_extract_archive"}:
        return "Archive"
    if name in {"act_extract_pages", "act_extract_audio", "act_ocr", "act_ocr_pdf", "act_docx_to_txt"}:
        return "Extract"
    if name in {"act_organize_pdf", "act_merge_pdfs", "act_compress_pdfs", "act_split_pdf", "act_split_ranges", "act_ocr_pdf_to_pdf"}:
        return "PDF Tools"
    return "Convert"

def sections(actions, favorites, counts):
    fav = [a for a in actions if identity(a) in favorites or a.label in favorites]
    rest = [a for a in actions if a not in fav]
    ranked = sorted(enumerate(rest), key=lambda pair: (-counts.get(identity(pair[1]), 0), pair[0]))
    common = [a for _, a in ranked[:3]]
    remaining = [a for a in rest if a not in common]
    title = "Frequently used" if any(counts.get(identity(a), 0) for a in rest) else "Suggested"
    return [("Favorites", fav), (title, common)] + [
        (c, [a for a in remaining if category(a) == c]) for c in CATEGORIES]
