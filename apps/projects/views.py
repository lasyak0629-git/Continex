# OWNER: Dev B
import json
from pathlib import Path
from types import SimpleNamespace

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.accounts.permissions import can_view
from apps.extraction.extractor import run_extraction
from apps.extraction.llm_client import get_client
from apps.extraction.models import ExtractedItem
from apps.ingestion.pipeline import prepare_sources

from .forms import UploadForm
from .models import Project, Source


def _audit(user, action, detail=""):
    """Writes to Brunda's audit log. Never breaks the page if the log call differs."""
    try:
        from apps.audit.logger import log
        log(user, action, detail)
    except Exception:
        pass


@login_required
def upload(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    form = UploadForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        level = form.cleaned_data["access_level"]
        for f in form.cleaned_data["files"]:
            Source.objects.create(project=project, name=f.name, file=f, access_level=level)
            _audit(request.user, "upload", f"{f.name} [{level}]")
        return redirect("projects:upload", project_id=project.id)
    sources = Source.objects.filter(project=project)
    return render(request, "upload.html",
                  {"project": project, "form": form, "sources": sources})


@login_required
@require_POST
def run_extract(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    sources = list(Source.objects.filter(project=project))
    wrapped = [SimpleNamespace(name=s.name, path=s.file.path,
                               access_level=s.access_level, obj=s) for s in sources]

    # permission check, restricted-never-sent and secret redaction all run before the AI
    texts, stats = prepare_sources(wrapped, lambda w: can_view(request.user, w.obj))
    if not texts:
        messages.error(request, "No files you are allowed to analyse. Nothing was sent to the AI.")
        return redirect("projects:upload", project_id=project.id)

    try:
        out = run_extraction(texts, get_client())
    except Exception as e:
        messages.error(request, f"Extraction failed ({type(e).__name__}). Nothing was saved.")
        _audit(request.user, "extract_failed", type(e).__name__)
        return redirect("projects:upload", project_id=project.id)

    by_name = {s.name: s for s in sources}
    ExtractedItem.objects.filter(project=project,
                                 status=ExtractedItem.Status.PENDING).delete()
    created = 0
    for s in out["kept"]:
        src = by_name.get(s.source_name)
        if src is None:
            continue
        obj = ExtractedItem.from_schema(project, src, s)
        obj.quote_verified = True
        obj.save()
        created += 1

    _audit(request.user, "extract",
           f"saved={created} dropped={len(out['dropped'])} rejected={len(out['rejected'])} "
           f"injection={len(out['injection_hits'])} redactions={stats['redactions']}")
    messages.success(
        request,
        f"{created} items saved with verified quotes. {len(out['dropped'])} dropped "
        f"(quote not found in source), {len(out['rejected'])} rejected, "
        f"{stats['redactions']} secrets hidden, "
        f"{len(out['injection_hits'])} hidden instruction(s) ignored. "
        f"Skipped (never sent or no access): {stats['never_sent'] + stats['skipped_no_access']}.")
    return redirect("projects:upload", project_id=project.id)


@login_required
def eval_results(request):
    path = Path(settings.BASE_DIR) / "demo_data" / "eval_report.json"
    report = json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
    return render(request, "eval_results.html", {"r": report})