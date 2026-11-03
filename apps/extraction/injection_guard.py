# OWNER: Dev B
# OWNER: Dev B
import json
import re
from dataclasses import fields
from .schemas import ExtractedItemSchema

ALLOWED_KEYS = {f.name for f in fields(ExtractedItemSchema)}

SUSPICIOUS = re.compile(
    r"(?i)(ignore (all )?(previous|prior) instructions|disregard .{0,30}instructions|"
    r"mark (everything|this|all) (as )?safe|you are now|system prompt)"
)


def flag_injection(texts: dict[str, str]) -> list[dict]:
    """Detect hidden instructions. They are logged, never obeyed."""
    hits = []
    for name, body in texts.items():
        for line in body.splitlines():
            if SUSPICIOUS.search(line):
                hits.append({"file": name, "line": line.strip()})
    return hits


def parse_llm_output(raw: str, allowed_files: set[str]):
    """
    Strict schema lock. Returns (items, rejected).
    Raises ValueError if the output is not exactly {"items": [...]}.
    Individual bad items are rejected and counted, not trusted.
    """
    raw = re.sub(r"^```(?:json)?|```$", "", raw.strip(), flags=re.M).strip()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"LLM output rejected (not JSON): {e}")
    if not isinstance(data, dict) or set(data) != {"items"} or not isinstance(data["items"], list):
        raise ValueError("LLM output rejected: must be exactly {'items': [...]}")

    items, rejected = [], []
    for d in data["items"]:
        try:
            if not isinstance(d, dict) or set(d) - ALLOWED_KEYS:
                raise ValueError("unknown or missing fields")
            if not isinstance(d.get("people", []), list):
                raise ValueError("people must be a list")
            d = {**d, "confidence": float(d.get("confidence", 0.0))}
            item = ExtractedItemSchema.from_dict(d)   # her validate() runs here
            if item.source_name not in allowed_files:
                raise ValueError("cites a file that was never sent")
            items.append(item)
        except (ValueError, TypeError) as e:
            rejected.append({"item": d, "why": str(e)})
    return items, rejected