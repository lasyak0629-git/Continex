# OWNER: Dev A
from .base import FindingData


def check(items, ctx):
    return [
        FindingData("missing_reason", "warning", it,
                    "A decision was recorded but nobody wrote down why.")
        for it in items
        if it.item_type == "decision" and not (it.reason or "").strip()
    ]