import threading

from django.db import close_old_connections
from django.utils import timezone

from .models import AnalysisJob


def start_analysis(project, user, leaver, leave_date):
    job = AnalysisJob.objects.create(project=project, started_by=user)
    threading.Thread(
        target=_run, args=(job.id, project.id, user.id, leaver, leave_date), daemon=True
    ).start()
    return job


def _run(job_id, project_id, user_id, leaver, leave_date):
    close_old_connections()
    from django.contrib.auth import get_user_model

    from apps.rehearsal.engine import run_rehearsal

    from .models import Project
    from .services import extract_project

    job = AnalysisJob.objects.get(pk=job_id)
    try:
        job.status = AnalysisJob.Status.RUNNING
        job.save(update_fields=["status"])
        project = Project.objects.get(pk=project_id)
        user = get_user_model().objects.get(pk=user_id)
        s = extract_project(project, user)
        run_rehearsal(project, leaver, leave_date, user=user)
        job.status = AnalysisJob.Status.DONE
        job.message = (
            f"{s['created']} items saved with verified quotes. {s['dropped']} dropped "
            f"(quote not found in source), {s['rejected']} rejected, "
            f"{s['redactions']} secrets hidden, {s['injection']} hidden instruction(s) ignored."
        )
    except Exception as e:  # API down, unreadable file, etc.
        job.status = AnalysisJob.Status.FAILED
        job.message = f"{type(e).__name__}: {e}"
    finally:
        job.finished_at = timezone.now()
        job.save()
        close_old_connections()