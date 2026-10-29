"""Small localization layer for DropFlow (English/Arabic)."""
from __future__ import annotations

import re

LANGUAGES = {"en": "English", "ar": "العربية"}
LANG = "en"


def set_language(code: str) -> None:
    global LANG
    LANG = code if code in LANGUAGES else "en"


def get_language() -> str:
    return LANG


def is_rtl() -> bool:
    return LANG == "ar"


AR = {
    "Drop files or folders here": "اسحب الملفات أو المجلدات هنا",
    "Ctrl + Shift + D toggles · Esc closes": "Ctrl + Shift + D للفتح · Esc للإغلاق",
    "PDF · images · Word · video · ZIP": "PDF · صور · Word · فيديو · ZIP",
    "Drop more files to add them  ·  Esc closes": "أضف ملفات أخرى بالسحب · Esc للإغلاق",
    "Cancel": "إلغاء",
    "Cancelling…": "جارٍ الإلغاء…",
    "Close": "إغلاق",
    "Back": "رجوع",
    "Run": "تشغيل",
    "Open folder": "فتح المجلد",
    "Copy text": "نسخ النص",
    "Copied ✓": "تم النسخ ✓",
    "Open log": "فتح السجل",
    "Done": "تم",
    "Done with warnings": "تم مع تحذيرات",
    "Some items failed. Open the log for details.": "فشل بعض العناصر. افتح السجل للتفاصيل.",
    "Cancelled": "أُلغي",
    "The job was stopped. Incomplete output was cleaned up.":
        "تم إيقاف العملية وتنظيف الملفات الناقصة.",
    "Something went wrong": "حدث خطأ",
    "Starting…": "جارٍ البدء…",
    "Esc also cancels": "Esc للإلغاء أيضًا",
    "Output format": "صيغة الإخراج",
    "Settings": "الإعدادات",
    "Open drop zone": "فتح منطقة الإفلات",
    "Quit": "إنهاء",
    "Check for updates": "البحث عن تحديثات",
    "Update available": "يوجد تحديث",
    "Global shortcut": "الاختصار العام",
    "Record": "تسجيل",
    "Listening…": "جارٍ الاستماع…",
    "Reset default": "إعادة الافتراضي",
    "Save": "حفظ",
    "Start DropFlow with Windows": "تشغيل DropFlow مع ويندوز",
    "Detected helper programs": "البرامج المساعدة المكتشفة",
    "OCR languages (Tesseract codes, combine with +)":
        "لغات OCR (رموز Tesseract، ادمجها بـ +)",
    "Language": "اللغة",
    "Remember window position": "تذكّر موضع النافذة",
    "Check for updates on startup": "البحث عن التحديثات عند البدء",
    "Add 'Send to DropFlow' to the Explorer context menu":
        "إضافة «إرسال إلى DropFlow» إلى قائمة النقر بزر الماوس الأيمن",
    "Click Record, then press the new combination (e.g. Ctrl + Alt + Space). Esc cancels recording.":
        "اضغط «تسجيل»، ثم اضغط الاختصار الجديد (مثل Ctrl + Alt + Space). Esc يلغي التسجيل.",
    "Active shortcut: none": "الاختصار النشط: لا يوجد",
    "Examples: ara+eng, eng, ara, fra. Installed languages appear here.":
        "أمثلة: ara+eng أو eng أو ara أو fra. تظهر اللغات المثبتة هنا.",
    "Tesseract is not available, so OCR will be disabled.":
        "Tesseract غير متاح، لذلك سيتم تعطيل OCR.",
    "That key can't be used. Try a letter, number or F-key.":
        "لا يمكن استخدام هذا المفتاح. جرّب حرفًا أو رقمًا أو مفتاح F.",
    "Add at least one modifier (Ctrl / Alt / Shift / Win).":
        "أضف مفتاحًا معدّلًا واحدًا على الأقل (Ctrl / Alt / Shift / Win).",
    "Finish recording first (Esc cancels recording).":
        "أنهِ التسجيل أولًا (Esc يلغيه).",
    "Shortcut is available. Press Save to apply.":
        "الاختصار متاح. اضغط حفظ للتطبيق.",
    "Recording — the current shortcut is paused.":
        "جارٍ التسجيل — الاختصار الحالي متوقف مؤقتًا.",
    "Press your shortcut…": "اضغط الاختصار…",
    "Merge into one PDF": "دمج في ملف PDF واحد",
    "Compress PDF": "ضغط PDF",
    "Compress PDFs": "ضغط ملفات PDF",
    "Split every N pages": "تقسيم كل N صفحات",
    "Extract page range…": "استخراج نطاق صفحات…",
    "Split at page ranges…": "تقسيم عند نطاقات الصفحات…",
    "Export pages as PNG": "تصدير الصفحات كـ PNG",
    "Export pages as JPG": "تصدير الصفحات كـ JPG",
    "Create searchable PDF (OCR)": "إنشاء PDF قابل للبحث (OCR)",
    "Extract text (.txt, OCR)": "استخراج النص (.txt، OCR)",
    "Create PowerPoint…": "إنشاء عرض PowerPoint…",
    "Create Excel workbook…": "إنشاء مصنف Excel…",
    "Combine into one PDF": "دمج في PDF واحد",
    "Create animated GIF": "إنشاء GIF متحرك",
    "Compress image": "ضغط الصورة",
    "Compress images": "ضغط الصور",
    "Compress video": "ضغط الفيديو",
    "Compress videos": "ضغط الفيديوهات",
    "Universal media converter…": "محوّل الوسائط الشامل…",
    "Extract audio (MP3)": "استخراج الصوت (MP3)",
    "Convert to PDF": "تحويل إلى PDF",
    "Extract text to .txt": "استخراج النص إلى .txt",
    "Universal document converter…": "محوّل المستندات الشامل…",
    "Extract to a new folder": "استخراج إلى مجلد جديد",
    "Extract RAR to a new folder": "استخراج RAR إلى مجلد جديد",
    "Extract archives to new folders": "استخراج الأرشيفات إلى مجلدات جديدة",
    "Combine all into one PDF": "دمج الكل في PDF واحد",
    "Compress to ZIP": "ضغط إلى ZIP",
    "Extract archive": "استخراج الأرشيف",
    "Extract archives": "استخراج الأرشيفات",
    "Quality (lower = smaller file)": "الجودة (أقل = ملف أصغر)",
    "Image quality (lower = smaller file)": "جودة الصورة (أقل = ملف أصغر)",
    "Pages per file": "الصفحات لكل ملف",
    "Pages to extract": "الصفحات المطلوبة",
    "Page ranges": "نطاقات الصفحات",
    "Resolution": "الدقة",
    "JPEG quality": "جودة JPEG",
    "OCR render resolution": "دقة عرض OCR",
    "Audio bitrate": "معدل بت الصوت",
    "Time per frame": "زمن الإطار",
    "Quality": "الجودة",
    "File": "ملف",
    "Working…": "جارٍ العمل…",
    "Recent activity": "آخر النشاط",
    "Step": "خطوة",
    "Stopping the current job…": "جارٍ إيقاف العملية…",
    "Quality (CRF, lower = better and larger)": "الجودة (CRF، أقل = أفضل وحجم أكبر)",
    "Target size (MB, optional)": "الحجم المستهدف (MB، اختياري)",
    "Use NVIDIA GPU (NVENC)": "استخدام كرت NVIDIA (NVENC)",
    "GPU encoding unavailable": "ترميز GPU غير متاح",
    "Keep original": "إبقاء الأصل",
    "Leave target empty to use CRF. A target size ignores CRF; audio is also adjusted.":
        "اترك الهدف فارغًا لاستخدام CRF. الحجم المستهدف يتجاهل CRF ويعدّل الصوت أيضًا.",
    "PDF": "PDF",
    "PNG images (one per slide/page)": "صور PNG (واحدة لكل شريحة/صفحة)",
    "JPG images (one per slide/page)": "صور JPG (واحدة لكل شريحة/صفحة)",
    "Plain text": "نص عادي",
    "Word document": "مستند Word",
    "CSV files": "ملفات CSV",
    "HTML": "HTML",
    "JSON": "JSON",
    "PowerPoint presentation": "عرض PowerPoint",
    "Excel workbook": "مصنف Excel",
    "Animated GIF": "GIF متحرك",
    "MP4 video (H.264 + AAC)": "فيديو MP4 (H.264 + AAC)",
    "MKV video": "فيديو MKV",
    "AVI video": "فيديو AVI",
    "MOV video": "فيديو MOV",
    "WEBM video (VP9 + Opus)": "فيديو WEBM (VP9 + Opus)",
    "MP3 audio": "صوت MP3",
    "AAC audio": "صوت AAC",
    "WAV audio (PCM)": "صوت WAV (PCM)",
    "M4A audio (AAC)": "صوت M4A (AAC)",
    "FLAC audio (lossless)": "صوت FLAC (بدون فقدان)",
    "Password required": "كلمة المرور مطلوبة",
    "Show password": "إظهار كلمة المرور",
    "Unlock": "فتح",
    "Enter a password.": "أدخل كلمة المرور.",
    "PDF archive": "أرشيف PDF",
    "ZIP archive": "أرشيف ZIP",
    "RAR archive": "أرشيف RAR",
    "Copy details": "نسخ التفاصيل",
    "Full details:": "التفاصيل الكاملة:",
    "Active now:": "نشط الآن:",
    "Appearance": "المظهر",
    "Choose a theme, then adjust the accent.": "اختر سمة، ثم عدّل لون التمييز.",
    "Accent": "لون التمييز",
    "Custom…": "مخصص…",
    "Reduce motion": "تقليل الحركة",
    "High Contrast is available as a theme card.": "تتوفر سمة «تباين عالٍ» كبطاقة.",
    "Accent contrast: {ratio}:1": "تباين لون التمييز: {ratio}:1",
    "auto-adjusted for readability": "تم تعديله تلقائيًا لتحسين القراءة",
    "No matching actions": "لا توجد إجراءات مطابقة",
    "Before": "قبل",
    "After": "بعد",
    "Output": "الناتج",
    "Choose accent color": "اختر لون التمييز",
    "System (Auto)": "النظام (تلقائي)",
    "Midnight": "منتصف الليل",
    "Slate": "أردوازي",
    "Ocean": "محيطي",
    "Forest": "غابة",
    "Rose": "وردي",
    "Sepia": "سيبيا",
    "Light": "فاتح",
    "High Contrast": "تباين عالٍ",
    "LibreOffice — ready (best Office → PDF)": "LibreOffice — جاهز (الأفضل لتحويل Office إلى PDF)",
    "LibreOffice — not found (using the built-in DOCX renderer)":
        "LibreOffice — غير موجود (سيُستخدم محرك DOCX الداخلي)",
    "FFmpeg — ready (video compression + audio extraction)":
        "FFmpeg — جاهز (ضغط الفيديو واستخراج الصوت)",
    "FFmpeg — not found (video tools disabled)":
        "FFmpeg — غير موجود (أدوات الفيديو معطلة)",
    "Tesseract OCR — ready": "Tesseract OCR — جاهز",
    "Tesseract OCR — not found (OCR disabled)": "Tesseract OCR — غير موجود (OCR معطل)",
    "RAR — no backend (install 7-Zip or UnRAR)":
        "RAR — لا يوجد محرك (ثبّت 7-Zip أو UnRAR)",
    "Password entry was cancelled.": "تم إلغاء إدخال كلمة المرور.",
}

_PATTERNS = [
    (re.compile(r"^Convert to (PNG|JPG|WEBP)$"), r"تحويل إلى \1"),
    (re.compile(r"^Convert all to (PNG|JPG|WEBP)$"), r"تحويل الكل إلى \1"),
    (re.compile(r"^Active now: (.+)$"), r"نشط الآن: \1"),
    (re.compile(r"^Update available: (.+)$"), r"يوجد تحديث: \1"),
    (re.compile(r"^RAR — ready \((.+)\)$"), r"RAR — جاهز (\1)"),
]


def tr(text: str) -> str:
    if LANG == "en" or not text:
        return text
    if text in AR:
        return AR[text]
    for pattern, replacement in _PATTERNS:
        if pattern.match(text):
            return pattern.sub(replacement, text)
    return text

