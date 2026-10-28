# DropFlow source bundle

Files
-----
- `DropFlow.pyw`       Tkinter/tray application and all actions.
- `media_converter.py` Universal video/audio/GIF converter.
- `office_converter.py` PowerPoint/Excel/Word/text/data converter.

The two converter modules are imported by DropFlow and are also usable on their
own.  Keep all three files in the same folder.

Quick start
-----------
1. Install Python 3.10+ (64-bit) and run:
       pip install -r requirements.txt
2. Install LibreOffice for high-fidelity Office -> PDF conversion:
       https://www.libreoffice.org/download/
3. Install Tesseract for OCR/image text extraction (optional):
       https://github.com/UB-Mannheim/tesseract/wiki
4. Run:
       python DropFlow.pyw --console
   or double-click DropFlow.pyw.

Optional external tools:
- LibreOffice: Office/PowerPoint/Excel -> PDF and legacy .ppt/.xls support.
- Tesseract: OCR and image -> TXT.
- UnRAR or 7-Zip: RAR extraction.
- FFmpeg: bundled through imageio-ffmpeg, or use FFMPEG_PATH/PATH.

Conversion matrix
-----------------
PowerPoint .pptx/.ppt:
  -> PDF
  -> PNG or JPG images, one per slide
  -> TXT (slide text and tables)

Excel .xlsx/.xls:
  -> PDF
  -> CSV (one file per sheet)
  -> HTML
  -> JSON (one array per sheet, first row as headers)
  -> TXT (tab-separated sheet content)

Text .txt:
  -> PDF (reportlab)
  -> DOCX (python-docx)
  -> PPTX (split into slides)
  -> XLSX (one row per line, detects tab/comma-separated data)

Other directions:
  images / PDF        -> PPTX (one slide per image/PDF page)
  CSV / JSON / PDF    -> XLSX (PDF tables become sheets; text falls back to rows)
  PDF / DOCX / PPTX / XLSX / CSV / JSON / images -> TXT

Office -> PDF strategy
----------------------
1. LibreOffice headless with an isolated user profile.
2. Microsoft Office COM automation if `pywin32` and Office are installed.
3. Excel/DOCX basic reportlab fallbacks if neither is available.
PowerPoint -> PDF genuinely needs LibreOffice or PowerPoint COM.

Python integration
-------------------
    from office_converter import OfficeConverter, OfficeCallbacks

    conv = OfficeConverter(soffice_path=r"C:\Program Files\LibreOffice\program\soffice.exe")
    result = conv.convert(
        "deck.pptx", "png", "deck_slides",
        callbacks=OfficeCallbacks(
            on_start=lambda src, target: print("start", src, target),
            on_progress=lambda pct, msg: print(pct, msg),
            on_success=lambda res: print("done", [str(p) for p in res.outputs]),
            on_error=lambda exc: print("failed", exc),
        ),
    )

Async:

    handle = conv.convert_async("book.xlsx", "json", "book.json")
    handle.join()

Combining multiple images/PDF pages into one PowerPoint:

    conv.to_pptx_many(["one.png", "two.pdf"], "output.pptx")

DropFlow integration
--------------------
`DropFlow.pyw` imports the modules optionally.  If a module is missing the
feature shows a clear error instead of crashing.  The relevant UI actions are
created in `build_actions()` and dispatched through `JobContext`, which supplies
progress, cancellation, and per-file fault tolerance.

Packaging notes
---------------
When rebuilding with PyInstaller, include:
  --hidden-import office_converter
  --hidden-import media_converter
  --collect-all pptx
  --collect-all openpyxl
  --collect-all docx
  --collect-all reportlab
  --collect-all pymupdf
  --collect-all fitz
  --collect-all tkinterdnd2
  --collect-all imageio_ffmpeg

LibreOffice, Tesseract, UnRAR/7-Zip and Microsoft Office are external tools and
are not bundled.  FFmpeg is bundled by the current build.
