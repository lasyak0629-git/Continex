# OWNER: Dev B
import json
from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from datetime import date
from apps.rehearsal.engine import run_rehearsal
from apps.accounts.decorators import project_role_required
from apps.audit.logger import log

from .models import Project

from .forms import UploadForm
from .models import Source
from .services import extract_project


@project_role_required("manager")
def upload(request, project_id):
    project = request.project
    form = UploadForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        level = form.cleaned_data["access_level"]  # public / internal / restricted
        for f in form.cleaned_data["files"]:
            Source.objects.create(project=project, name=f.name, file=f,
                                  sensitivity=level, uploaded_by=request.user)
            log(request.user, "source.uploaded", project=project, file=f.name, sensitivity=level)
        return redirect("projects:upload", project_id=project.id)
    sources = Source.objects.filter(project=project)
    return render(request, "upload.html",
                  {"project": project, "form": form, "sources": sources})


@require_POST
@project_role_required("manager")
def run_extract(request, project_id):
    leaver = request.POST.get("leaver", "").strip()
    try:
        leave_date = date.fromisoformat(request.POST.get("leave_date", ""))
    except ValueError:
        leave_date = None
    if not leaver or not leave_date:
        messages.error(request, "Enter who is leaving and their last working day.")
        return redirect("projects:upload", project_id=project_id)
    try:
        s = extract_project(request.project, request.user)
        run_rehearsal(request.project, leaver, leave_date, user=request.user)
    except Exception as e:  # API down, bad key, unreadable file
        messages.error(request, f"Analysis failed ({type(e).__name__}): {e}")
        return redirect("projects:upload", project_id=project_id)
    messages.success(
        request,
        f"{s['created']} items saved with verified quotes. {s['dropped']} dropped "
        f"(quote not found in source), {s['rejected']} rejected, "
        f"{s['redactions']} secrets hidden, {s['injection']} hidden instruction(s) ignored.")
    return redirect("review:home", project_id=project_id)

@login_required
def eval_results(request):
    path = Path(settings.BASE_DIR) / "demo_data" / "eval_report.json"
    report = json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
    return render(request, "eval_results.html", {"r": report})

@login_required
def home(request):
    projects = Project.objects.filter(memberships__user=request.user).distinct()
    return render(request, "home.html", {"projects": projects})