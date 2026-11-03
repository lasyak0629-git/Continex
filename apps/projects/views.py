# OWNER: Dev B
# OWNER: Dev B
import json
from pathlib import Path
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from django.contrib import messages
from django.views.decorators.http import require_POST

from apps.accounts.decorators import project_role_required
from .services import extract_project

from .forms import UploadForm
from .models import Project, Source

from apps.accounts.decorators import project_role_required

@login_required
def upload(request, project_id):

    @project_role_required("manager")
    def upload(request, project_id):
        project = request.project
        form = UploadForm(request.POST or None, request.FILES or None)
        if request.method == "POST" and form.is_valid():
            level = form.cleaned_data["access_level"]  # must be public / internal / restricted
            for f in form.cleaned_data["files"]:
                Source.objects.create(project=project, name=f.name, file=f,
                                  sensitivity=level, uploaded_by=request.user)
            return redirect("projects:upload", project_id=project.id)
        sources = Source.objects.filter(project=project)
        return render(request, "upload.html", {"project": project, "form": form, "sources": sources})
    
    project = get_object_or_404(Project, pk=project_id)
    form = UploadForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        level = form.cleaned_data["access_level"]
        for f in form.cleaned_data["files"]:
            Source.objects.create(project=project, name=f.name, file=f, access_level=level)
        return redirect("projects:upload", project_id=project.id)
    sources = Source.objects.filter(project=project)
    return render(request, "upload.html", {"project": project, "form": form, "sources": sources})


@login_required
def eval_results(request):
    path = Path(settings.BASE_DIR) / "demo_data" / "eval_report.json"
    report = json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
    return render(request, "eval_results.html", {"r": report})

@require_POST
@project_role_required("manager")
def run_extract(request, project_id):
    try:
        s = extract_project(request.project, request.user)
    except Exception as e:  # API down, bad key, unreadable file
        messages.error(request, f"Extraction failed: {e}")
    else:
        messages.success(
            request,
            f"{s['created']} items extracted. {s['dropped']} dropped (quote not found), "
            f"{s['rejected']} rejected, {len(s['never_sent'])} restricted file(s) never sent.")
    return redirect("review:home", project_id=project_id)