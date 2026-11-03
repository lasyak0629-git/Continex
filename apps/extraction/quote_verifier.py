# OWNER: Dev B
# OWNER: Dev B
import re


def _norm(s: str) -> str:
    s = s.replace("\u2019", "'").replace("\u201c", '"').replace("\u201d", '"')
    s = s.replace("\u2013", "-").replace("\u2014", "-")
    return re.sub(r"\s+", " ", s).strip().lower()


def verify_items(items, source_texts: dict[str, str]):
    """Keep only items whose quote really exists in the source they cite.
    Dev A sets ExtractedItem.quote_verified = True for everything in `kept`."""
    kept, dropped = [], []
    for it in items:
        src = source_texts.get(it.source_name, "")
        ok = bool(it.quote) and _norm(it.quote) in _norm(src)
        (kept if ok else dropped).append(it)
    return kept, dropped