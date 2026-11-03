# OWNER: Dev A
from .models import AuditEvent


def log(user, action, project=None, target=None, **detail):
    return AuditEvent.objects.create(
        actor=user if getattr(user, "is_authenticated", False) else None,
        project=project,
        action=action,
        target_type=type(target).__name__ if target is not None else "",
        target_id=getattr(target, "pk", None),
        detail=detail,
    )