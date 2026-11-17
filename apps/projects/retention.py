# OWNER Dev: A
from apps.audit.logger import log
from apps.audit.models import AuditEvent


def delete_project_data(project, actor=None, reason="retention"):
    """Removes files, extracted data, handovers and the project itself.
    Audit entries stay as a record of what happened, but their details are scrubbed."""
    pid = project.id
    for s in project.sources.all():
        if s.file:
            s.file.delete(save=False)
    AuditEvent.objects.filter(project=project).update(detail={"scrubbed": True})
    project.delete()
    log(actor, "project.deleted", project=None, reason=reason, project_id=pid)