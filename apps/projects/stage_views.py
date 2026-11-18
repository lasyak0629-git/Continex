# OWNER Dev A
from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from apps.accounts.decorators import project_role_required
from apps.audit.logger import log
from .models import GapQuestion, Project


def _notify(request, project, roles, subject, body):
    link = request.build_absolute_uri(reverse("review:home", args=[project.id]))
    emails = [m.user.email for m in project.memberships.filter(role__in=roles).select_related("user")
              if m.user.email]
    if not emails:
        return
    try:
        send_mail(subject, f"{body}\n\nOpen the review: {link}", settings.DEFAULT_FROM_EMAIL, emails)
    except Exception:
        messages.warning(request, "The status changed, but the notification email could not be sent.")


@require_POST
@project_role_required("manager")
def send_to_leaver(request, project_id):
    p = request.project
    if not p.memberships.filter(role="leaver").exists():
        messages.error(request, "Invite the leaving person first (Team page).")
        return redirect("review:home", project_id=p.id)
    p.stage = Project.Stage.LEAVER_REVIEW
    p.save(update_fields=["stage"])
    log(request.user, "stage.leaver_review", project=p)
    _notify(request, p, ["leaver"], f"Your review is requested: {p.name}",
            f"{request.user.get_username()} asks you to check what was found, answer the open "
            f"questions and upload anything that is missing.")
    messages.success(request, "Sent to the leaving person for the first review.")
    return redirect("review:home", project_id=p.id)


@require_POST
@project_role_required("manager", allow=("leaver",))
def submit_to_manager(request, project_id):
    p = request.project
    p.stage = Project.Stage.MANAGER_REVIEW
    p.save(update_fields=["stage"])
    log(request.user, "stage.manager_review", project=p)
    _notify(request, p, ["manager", "owner"], f"First review finished: {p.name}",
            f"{request.user.get_username()} has finished the first review. It is ready for your review.")
    messages.success(request, "Submitted to the manager for the second review.")
    return redirect("review:home", project_id=p.id)


@require_POST
@project_role_required("manager", allow=("leaver",))
def gap_answer(request, project_id, gap_id):
    gap = get_object_or_404(GapQuestion, pk=gap_id, project=request.project)
    if request.POST.get("action") == "dismiss":
        gap.status = GapQuestion.Status.DISMISSED
    else:
        ans = request.POST.get("answer", "").strip()[:2000]
        if not ans:
            messages.error(request, "Write an answer, or choose Not relevant.")
            return redirect("review:home", project_id=project_id)
        gap.answer, gap.status = ans, GapQuestion.Status.ANSWERED
    gap.answered_by, gap.answered_at = request.user, timezone.now()
    gap.save()
    log(request.user, "gap.answered", project=request.project, gap=gap.id, status=gap.status)
    return redirect("review:home", project_id=project_id)