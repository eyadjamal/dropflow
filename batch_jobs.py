"""Structured batch execution, independent of Tkinter."""
from dataclasses import dataclass, field
from pathlib import Path
from output_policy import output_scope
from action_menu import identity

@dataclass
class ItemResult:
    source: Path
    status: str = "Queued"
    outputs: list = field(default_factory=list)
    error: str = ""
    preview: str = ""
    clipboard: str = ""
    index: int = 1

COMBINED = {"act_merge_pdfs", "act_images_to_pdf", "act_mixed_to_pdf",
            "act_images_to_gif", "act_images_pdf_to_pptx", "act_zip", "act_ocr_to_pdf", "act_organize_pdf"}

def is_combined(action):
    return action.func.__name__ in COMBINED

def execute(action, items, options, ctx, emit, cancelled_type):
    """Adapt legacy Result objects without treating swallowed failures as success."""
    combined = is_combined(action)
    groups = [items] if combined else [[item] for item in items]
    for group in groups:
        if ctx.cancelled:
            for item in group:
                item.status = "Cancelled"
                emit(item)
            continue
        for item in group:
            item.status = "Running"
            item.error = ""
            emit(item)
        try:
            with output_scope([i.source for i in group], options.get("_output", {}),
                              identity(action), group[0].index):
                result = action.func([i.source for i in group], dict(options), ctx)
            if result.failed:
                for item in group:
                    item.outputs = list(result.outputs)
                raise RuntimeError("\n".join(getattr(result, "errors", [])) or result.message)
            for item in group:
                item.outputs = list(result.outputs)
                item.preview = result.preview or ""
                item.clipboard = result.clipboard or ""
                item.status = "Done" if item.outputs or item.preview or item.clipboard else "Unchanged"
        except cancelled_type:
            for item in group:
                item.status = "Cancelled"
        except Exception as exc:
            for item in group:
                item.status = "Failed"
                item.error = str(exc) or type(exc).__name__
        for item in group:
            emit(item)
    return items
