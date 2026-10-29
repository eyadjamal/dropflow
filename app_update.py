"""GitHub release checker for DropFlow (no UI dependencies)."""
from __future__ import annotations

import json
import logging
import re
import urllib.request
from dataclasses import dataclass

LOG = logging.getLogger("DropFlow.Update")
API_URL = "https://api.github.com/repos/eyadjamal/dropflow/releases/latest"
RELEASES_URL = "https://github.com/eyadjamal/dropflow/releases/latest"


@dataclass
class UpdateInfo:
    version: str
    url: str
    name: str = ""
    notes: str = ""


def version_key(value: str) -> tuple[int, ...]:
    """Turn v3.2.1 into a comparable tuple."""
    nums = re.findall(r"\d+", str(value or ""))
    return tuple(int(n) for n in nums[:4]) or (0,)


def is_newer(latest: str, current: str) -> bool:
    return version_key(latest) > version_key(current)


def should_check(last_check: float, now: float, interval: float = 86400) -> bool:
    try:
        return float(now) - float(last_check) >= interval
    except (TypeError, ValueError):
        return True


def check_latest(current: str, timeout: float = 8.0) -> UpdateInfo | None:
    """Return the latest release if it is newer than current."""
    request = urllib.request.Request(
        API_URL,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "DropFlow-UpdateChecker",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        data = json.loads(response.read().decode("utf-8"))
    tag = str(data.get("tag_name") or data.get("name") or "").strip()
    if not tag:
        return None
    if not is_newer(tag, current):
        return None
    return UpdateInfo(
        version=tag.lstrip("vV"),
        url=str(data.get("html_url") or RELEASES_URL),
        name=str(data.get("name") or tag),
        notes=str(data.get("body") or ""),
    )
