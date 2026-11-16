# Owner Dev: A
import mimetypes

from django.core.exceptions import PermissionDenied
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404

from apps.accounts.decorators import project_role_required
from apps.accounts.permissions import can_view
from apps.audit.logger import log

from .models import Source


@project_role_required("member")  # managers, owners, members and leavers; not plain viewers
def source_file(request, project_id, source_id):
    src = get_object_or_404(Source, pk=source_id, project=request.project)
    if not src.file:
        raise Http404
    if not can_view(request.user, src):
        raise PermissionDenied
    log(request.user, "source.downloaded", project=request.project, file=src.name)
    resp = FileResponse(src.file.open("rb"), as_attachment=True, filename=src.name,
                        content_type=mimetypes.guess_type(src.name)[0] or "application/octet-stream")
    resp["X-Content-Type-Options"] = "nosniff"
    return resp