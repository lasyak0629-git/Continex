from django.http import Http404, HttpResponse
from django.utils.text import slugify

from apps.accounts.decorators import project_role_required
from apps.audit.logger import log

from .document import build_document, render_docx, render_pdf

TYPES = {
    "pdf": ("application/pdf", render_pdf),
    "docx": ("application/vnd.openxmlformats-officedocument.wordprocessingml.document", render_docx),
}


@project_role_required("viewer")
def handover_download(request, project_id, fmt):
    if fmt not in TYPES:
        raise Http404
    qs = request.project.handovers.all()
    v = request.GET.get("v", "")
    handover = qs.filter(version=int(v)).first() if v.isdigit() else qs.first()
    if handover is None:
        raise Http404
    ctype, render = TYPES[fmt]
    content = render(build_document(request.user, handover))
    log(request.user, "handover.downloaded", project=request.project, target=handover,
        format=fmt, version=handover.version)
    name = f"{slugify(request.project.name) or 'handover'}-v{handover.version}.{fmt}"
    resp = HttpResponse(content, content_type=ctype)
    resp["Content-Disposition"] = f'attachment; filename="{name}"'
    return resp