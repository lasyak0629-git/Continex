# OWNER: Dev A
from django.core.exceptions import PermissionDenied

from apps.accounts.permissions import get_role
from apps.audit.logger import log
from apps.extraction.models import ExtractedItem
from apps.handover.role_filter import can_see
from apps.projects.models import Source
from apps.review.models import ReviewDecision


def check_drift(handover):
    """Everything that changed in the project after this handover was built (UNFILTERED)."""
    project, since = handover.project, handover.created_at
    events = []

    decisions = (ReviewDecision.objects
                 .filter(item__project=project, created_at__gt=since)
                 .select_related("item__source"))
    for d in decisions:
        events.append({
            "kind": "item_" + d.action,
            "item_id": d.item_id,
            "message": f"An item was {d.action} after handover: {d.item.text}",
            "sensitivity": d.item.source.sensitivity,
            "at": d.created_at.isoformat(),
        })

    new_items = (ExtractedItem.objects
                 .filter(project=project, created_at__gt=since)
                 .select_related("source"))
    for it in new_items:
        events.append({
            "kind": "new_item",
            "item_id": it.id,
            "message": f"New {it.item_type.replace('_', ' ')} found after handover: {it.text}",
            "sensitivity": it.source.sensitivity,
            "at": it.created_at.isoformat(),
        })

    for s in Source.objects.filter(project=project, uploaded_at__gt=since):
        events.append({
            "kind": "new_source",
            "item_id": None,
            "message": f"New source uploaded after handover: {s.name}",
            "sensitivity": s.sensitivity,
            "at": s.uploaded_at.isoformat(),
        })

    events.sort(key=lambda e: e["at"])
    return events


def drift_for_user(user, handover):
    """The ONLY way views should read drift. Same role rules as the handover itself."""
    role = get_role(user, handover.project)
    if role is None:
        raise PermissionDenied("Not a member of this project.")
    events = check_drift(handover)
    visible = [e for e in events if can_see(role, e["sensitivity"])]
    result = {
        "handover_version": handover.version,
        "built_at": handover.created_at.isoformat(),
        "is_stale": bool(events),            # staleness is shown to everyone
        "events": visible,
        "hidden_count": len(events) - len(visible),  # a count only, never the text
    }
    log(user, "drift.checked", project=handover.project, target=handover,
        stale=result["is_stale"], hidden=result["hidden_count"])
    return result