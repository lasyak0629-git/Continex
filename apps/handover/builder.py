# OWNER: Dev A
from types import SimpleNamespace

from apps.audit.logger import log
from apps.extraction.models import ExtractedItem
from apps.rehearsal.rules.base import owned_by_leaver
from apps.review.services import can_finalize, latest_run

from .models import Handover

SECTIONS = [
    ("responsibility", "Responsibilities"),
    ("task", "Open tasks"),
    ("deadline", "Deadlines"),
    ("decision", "Decisions and reasons"),
    ("access_pointer", "Where to find access"),
    ("claim", "Facts to double-check"),
]
LEAVER_OWNED_TYPES = {"task", "deadline", "responsibility"}


class HandoverBlocked(Exception):
    def __init__(self, reasons):
        super().__init__("; ".join(reasons))
        self.reasons = reasons


def _entry(item, leaver):
    ctx = SimpleNamespace(leaver=leaver)
    return {
        "item_id": item.id,
        "text": item.text,
        "quote": item.quote,
        "source": item.source.name,
        "sensitivity": item.source.sensitivity,
        "owner": item.owner,
        "people": item.people or [],
        "date_text": item.date_text,
        "date": item.date_resolved.isoformat() if item.date_resolved else None,
        "reason": item.reason,
        "needs_new_owner": item.item_type in LEAVER_OWNED_TYPES and owned_by_leaver(item, ctx),
    }


def build_handover(project, user):
    ok, reasons = can_finalize(project)
    if not ok:
        raise HandoverBlocked(reasons)

    run = latest_run(project)
    approved = list(
        project.items.filter(status=ExtractedItem.Status.APPROVED)
        .select_related("source").order_by("id")
    )
    sections = [
        {"key": key, "title": title,
         "entries": [_entry(it, run.leaver) for it in approved if it.item_type == key]}
        for key, title in SECTIONS
    ]
    warnings = [
        {"item_id": f.item_id, "rule": f.rule, "message": f.message,
         "sensitivity": f.item.source.sensitivity}
        for f in run.findings.filter(severity="warning")
        .exclude(item__status=ExtractedItem.Status.REJECTED)
        .select_related("item__source")
    ]
    content = {
        "leaver": run.leaver,
        "leave_date": run.leave_date.isoformat(),
        "sections": sections,
        "warnings": warnings,
    }
    handover = Handover.objects.create(
        project=project, run=run, version=project.handovers.count() + 1,
        leaver=run.leaver, leave_date=run.leave_date, content=content, created_by=user,
    )
    log(user, "handover.built", project=project, target=handover,
        version=handover.version, items=len(approved))
    return handover