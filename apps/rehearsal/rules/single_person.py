# OWNER: Dev A
from .base import FindingData

RISKY = {"responsibility", "access_pointer", "task"}


def check(items, ctx):
    out = []
    leaver = ctx.leaver.strip().lower()
    for it in items:
        if it.item_type not in RISKY:
            continue
        names = {n.strip().lower() for n in (it.people or []) if n}
        if it.owner:
            names.add(it.owner.strip().lower())
        if names == {leaver}:
            sev = "blocker" if it.item_type == "access_pointer" else "warning"
            out.append(FindingData("single_person", sev, it,
                f"Only {ctx.leaver} is linked to this {it.item_type.replace('_', ' ')}. "
                f"Nobody else is named."))
    return out