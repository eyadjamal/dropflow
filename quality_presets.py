"""Encoder-specific starting points; output size is not guaranteed."""
LABELS = ("Small file", "Balanced", "Best quality")
VIDEO = ((28, "720p"), (23, "Keep original"), (18, "Keep original"))

def values(key, lo, hi, default):
    if key == "quality":
        return (max(lo, min(hi, round(default * .65))), default, min(hi, max(default, 95)))
    if key == "dpi":
        return (lo, default, hi)
    return None
