"""Job-local output routing. Never changes input files or nested export names."""
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import date
from pathlib import Path
import re
import string

_active = ContextVar("dropflow_output_policy", default=None)
TOKENS = {"name", "action", "index", "date"}
RESERVED = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)),
            *(f"LPT{i}" for i in range(1, 10))}

def validate_pattern(pattern):
    if not isinstance(pattern, str) or len(pattern) > 160:
        raise ValueError("Filename pattern must contain at most 160 characters.")
    for _, key, spec, conversion in string.Formatter().parse(pattern):
        if key is not None and (key not in TOKENS or spec or conversion):
            raise ValueError("Use only {name}, {action}, {index}, and {date}.")
    if pattern:
        render_name(pattern, Path("Example.pdf"), "convert", 1)
    return pattern

def render_name(pattern, source, action, index):
    name = pattern.format(name=source.stem, action=re.sub(r"[^a-zA-Z0-9_-]", "_", action),
                          index=index, date=date.today().isoformat())
    if (not name.strip() or name != name.rstrip(" .") or len(name) > 220
            or re.search(r'[<>:"/\\|?*\x00-\x1f]', name)
            or name.split(".")[0].upper() in RESERVED):
        raise ValueError("The filename is not valid on Windows. Do not include folders or an extension.")
    return name

def unique_path(path, is_dir=False):
    path = Path(path)
    stem, suffix = (path.name, "") if is_dir else (path.stem, path.suffix)
    candidate, index = path, 1
    while candidate.exists():
        candidate = path.with_name(f"{stem} ({index}){suffix}")
        index += 1
    return candidate

@contextmanager
def output_scope(sources, settings, action, index=1):
    sources = [Path(p).resolve() for p in sources]
    pattern = validate_pattern(settings.get("pattern", ""))
    folder = settings.get("folder", "")
    if folder and not Path(folder).is_absolute():
        raise ValueError("Choose an absolute output folder.")
    token = _active.set((sources, folder, pattern, action, index))
    try:
        yield
    finally:
        _active.reset(token)

def route_output(proposed, is_dir=False):
    proposed = Path(proposed)
    policy = _active.get()
    if policy:
        sources, folder, pattern, action, index = policy
        # Child files within split/export folders keep their relative names.
        if sources and proposed.parent.resolve() in {p.parent for p in sources}:
            source = sources[0]
            parent = Path(folder) if folder else proposed.parent
            parent.mkdir(parents=True, exist_ok=True)
            name = render_name(pattern, source, action, index) if pattern else (
                proposed.name if is_dir else proposed.stem)
            proposed = parent / (name if is_dir else name + proposed.suffix)
    return unique_path(proposed, is_dir)
