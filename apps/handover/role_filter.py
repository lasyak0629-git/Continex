# OWNER: Dev A
from django.core.exceptions import PermissionDenied

from apps.accounts.permissions import ROLE_RANK, SENSITIVITY_MIN_RANK, get_role
from apps.audit.logger import log


def can_see(role, sensitivity):
    if role is None:
        return False
    # unknown sensitivity values are denied by default
    return ROLE_RANK[role] >= SENSITIVITY_MIN_RANK.get(sensitivity, 99)


def filter_content(content, role):
    hidden_total = 0
    sections = []
    for s in content["sections"]:
        keep = [e for e in s["entries"] if can_see(role, e["sensitivity"])]
        hidden = len(s["entries"]) - len(keep)
        hidden_total += hidden
        sections.append({"key": s["key"], "title": s["title"], "entries": keep, "hidden": hidden})

    warnings = [w for w in content["warnings"] if can_see(role, w["sensitivity"])]
    hidden_total += len(content["warnings"]) - len(warnings)

    return {
        "leaver": content["leaver"],
        "leave_date": content["leave_date"],
        "role": role,
        "sections": sections,
        "warnings": warnings,
        "hidden_total": hidden_total,  # only a count, never the hidden text
    }


def handover_for_user(user, handover):
    """The ONLY way views should read a handover."""
    role = get_role(user, handover.project)
    if role is None:
        raise PermissionDenied("Not a member of this project.")
    result = filter_content(handover.content, role)
    log(user, "handover.viewed", project=handover.project, target=handover,
        role=role, hidden=result["hidden_total"])
    return result