"""Bounded local job history. Stores references, never document contents."""
from datetime import datetime, timezone
from pathlib import Path
import uuid

LIMIT = 15

def clean_history(records):
    if not isinstance(records, list):
        return []
    result = []
    for record in records[:LIMIT]:
        if not isinstance(record, dict) or not isinstance(record.get("action"), str):
            continue
        paths = {}
        for key in ("sources", "outputs"):
            value = record.get(key, [])
            paths[key] = list(dict.fromkeys(p for p in value if isinstance(p, str)))[:200] if isinstance(value, list) else []
        result.append({"id": str(record.get("id", ""))[:80], "action": record["action"][:200],
                       "at": str(record.get("at", ""))[:40], "status": str(record.get("status", ""))[:100],
                       "complete_inputs": record.get("complete_inputs", True) is True, **paths})
    return result

def remember(records, action, items):
    sources = list(dict.fromkeys(str(item.source) for item in items))
    outputs = list(dict.fromkeys(str(p) for item in items for p in item.outputs))
    done = sum(item.status in ("Done", "Unchanged") for item in items)
    failed = sum(item.status == "Failed" for item in items)
    cancelled = sum(item.status == "Cancelled" for item in items)
    status = f"{done}/{len(items)}"
    if failed:
        status += f" · {failed} failed"
    if cancelled:
        status += f" · {cancelled} cancelled"
    record = {"id": uuid.uuid4().hex, "action": action, "at": datetime.now(timezone.utc).isoformat(),
              "status": status, "sources": sources[:200], "outputs": outputs[:200],
              "complete_inputs": len(sources) <= 200}
    return [record, *clean_history(records)][:LIMIT]

def existing_inputs(record):
    if not record.get("complete_inputs", True):
        return [], len(record.get("sources", []))
    sources = record.get("sources", [])
    present = [Path(p) for p in sources if Path(p).exists()]
    return present, len(sources) - len(present)
