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

from .models import Project, Membership, Source, AnalysisJob

from .forms import UploadForm
from .models import Source
from .services import extract_project

from .models import Membership, Project

from datetime import timedelta
from django.utils import timezone

from .jobs import start_analysis
from .models import AnalysisJob

@project_role_required("manager", allow=("leaver",))
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
@project_role_required("manager", allow=("leaver",))
def run_extract(request, project_id):
    leaver = request.POST.get("leaver", "").strip()
    try:
        leave_date = date.fromisoformat(request.POST.get("leave_date", ""))
    except ValueError:
        leave_date = None
    if not leaver or not leave_date:
        messages.error(request, "Enter who is leaving and their last working day.")
        return redirect("projects:upload", project_id=project_id)
    busy = AnalysisJob.objects.filter(
        project=request.project, status__in=["queued", "running"],
        created_at__gt=timezone.now() - timedelta(minutes=15))
    if not busy.exists():
        start_analysis(request.project, request.user, leaver, leave_date)
    return redirect("projects:analysis_status", project_id=project_id)


@project_role_required("manager", allow=("leaver",))
def analysis_status(request, project_id):
    job = AnalysisJob.objects.filter(project=request.project).first()
    if job and job.status in ("queued", "running") \
            and job.created_at < timezone.now() - timedelta(minutes=15):
        job.status = "failed"
        job.message = "Timed out. The server may have restarted. Please run the analysis again."
        job.save()
    ctx = {"project": request.project, "job": job}
    if request.headers.get("HX-Request"):
        return render(request, "partials/job_status.html", ctx)
    return render(request, "analysis_status.html", ctx)

@login_required
def eval_results(request):
    path = Path(settings.BASE_DIR) / "demo_data" / "eval_report.json"
    report = json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
    return render(request, "eval_results.html", {"r": report})

@login_required
def home(request):
    memberships = (Membership.objects.filter(user=request.user)
                   .select_related("project", "invited_by").order_by("-project__created_at"))
    return render(request, "home.html", {"memberships": memberships})