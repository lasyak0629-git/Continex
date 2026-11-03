# OWNER: Dev A
from apps.audit.logger import log
from apps.extraction.models import ExtractedItem

from .models import ReviewDecision

EDITABLE = {"text", "owner", "people", "reason", "date_text"}


def _record(item, user, action, note="", changes=None):
    ReviewDecision.objects.create(
        item=item, reviewer=user, action=action, note=note, changes=changes or {}
    )
    log(user, f"item.{action}", project=item.project, target=item, note=note, changes=changes or {})


def approve_item(item, user, note=""):
    item.status = ExtractedItem.Status.APPROVED
    item.save(update_fields=["status"])
    _record(item, user, "approved", note)


def reject_item(item, user, note=""):
    item.status = ExtractedItem.Status.REJECTED
    item.save(update_fields=["status"])
    _record(item, user, "rejected", note)


def edit_item(item, user, data, note=""):
    changes = {}
    for key, new in data.items():
        if key not in EDITABLE:
            continue
        if key == "people" and isinstance(new, str):
            new = [p.strip() for p in new.split(",") if p.strip()]
        old = getattr(item, key)
        if old != new:
            changes[key] = [old, new]
            setattr(item, key, new)
    if not changes:
        return item
    if "date_text" in changes:
        item.date_resolved = None  # engine re-resolves on the next run
    item.save()
    _record(item, user, "edited", note, changes)
    return item


def latest_run(project):
    return project.runs.order_by("-created_at").first()


def open_blockers(project):
    run = latest_run(project)
    if run is None:
        return []
    return list(
        run.findings.filter(severity="blocker")
        .exclude(item__status=ExtractedItem.Status.REJECTED)
        .select_related("item")
    )


def pending_count(project):
    return project.items.filter(status=ExtractedItem.Status.PENDING).count()


def can_finalize(project):
    """The gate for handover. Returns (ok, list_of_reasons)."""
    reasons = []
    run = latest_run(project)
    if run is None:
        return False, ["Run the rehearsal first."]
    changed_since = ReviewDecision.objects.filter(
        item__project=project, created_at__gt=run.created_at
    ).exists()
    if changed_since:
        reasons.append("Items changed since the last rehearsal. Re-run it.")
    n = len(open_blockers(project))
    if n:
        reasons.append(f"{n} blocker(s) still open.")
    p = pending_count(project)
    if p:
        reasons.append(f"{p} item(s) still pending review.")
    return (not reasons), reasons