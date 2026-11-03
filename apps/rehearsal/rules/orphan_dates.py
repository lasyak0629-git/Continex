# OWNER: Dev A
from ..date_resolver import resolve_date
from .base import FindingData, owned_by_leaver


def check(items, ctx):
    out = []
    for it in items:
        if not it.date_text or not owned_by_leaver(it, ctx):
            continue
        d = it.date_resolved or resolve_date(it.date_text, ctx.today)
        if d is None:
            out.append(FindingData("orphan_dates", "warning", it,
                f'"{it.date_text}" belongs to {ctx.leaver}, but the date is unclear.'))
        elif d >= ctx.leave_date:
            out.append(FindingData("orphan_dates", "blocker", it,
                f"Due {d:%d %b %Y}, after {ctx.leaver} leaves on {ctx.leave_date:%d %b %Y}, "
                f"and nobody else owns it."))
    return out