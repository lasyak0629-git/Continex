# OWNER: Dev A
from .base import FindingData


def check(items, ctx):
    out = []
    for it in items:
        if not it.quote_verified:
            sev = "blocker" if it.item_type == "claim" else "warning"
            out.append(FindingData("unsupported_claims", sev, it,
                "The supporting quote could not be verified in the source file."))
        elif it.item_type == "claim" and it.confidence < 0.5:
            out.append(FindingData("unsupported_claims", "warning", it,
                "Low-confidence claim. Please check it against the source."))
    return out