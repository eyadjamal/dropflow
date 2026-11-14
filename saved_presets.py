"""Versioned, JSON-safe presets. PDF page selections are intentionally not saved."""
from copy import deepcopy
from uuid import uuid4
from output_policy import validate_pattern

ALLOWED = {"quality", "resolution", "target_mb", "gpu", "pages", "dpi",
           "duration", "target", "format"}

def clean_output(value):
    value = value if isinstance(value, dict) else {}
    folder, pattern = value.get("folder", ""), value.get("pattern", "")
    if not isinstance(folder, str) or not isinstance(pattern, str):
        raise ValueError("Invalid output settings.")
    validate_pattern(pattern)
    return {"folder": folder, "pattern": pattern}

def clean_options(options):
    return {k: deepcopy(v) for k, v in options.items()
            if k in ALLOWED and type(v) in (str, int, float, bool)}

def load_presets(records):
    valid = []
    for record in records[:100] if isinstance(records, list) else []:
        try:
            if not all(isinstance(record[k], str) and record[k].strip()
                       for k in ("id", "name", "action_id")):
                continue
            if not isinstance(record.get("options"), dict):
                continue
            valid.append({"id": record["id"], "name": record["name"][:60],
                          "action_id": record["action_id"], "version": 1,
                          "options": clean_options(record["options"]),
                          "output": clean_output(record.get("output"))})
        except (KeyError, TypeError, ValueError):
            continue
    return valid

def save_preset(records, action_id, name, options, output):
    name = name.strip()
    if not name or len(name) > 60:
        raise ValueError("Give the preset a name of 1–60 characters.")
    records = load_presets(records)
    existing = next((r for r in records if r["action_id"] == action_id
                     and r["name"].casefold() == name.casefold()), None)
    record = {"id": existing["id"] if existing else uuid4().hex, "version": 1,
              "name": name, "action_id": action_id, "options": clean_options(options),
              "output": clean_output(output)}
    if existing:
        records.remove(existing)
    elif len(records) >= 100:
        raise ValueError("Delete an unused preset before adding another (limit: 100).")
    return records + [record]
