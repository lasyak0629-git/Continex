# OWNER: Dev A logic, B styles template

from django.shortcuts import get_object_or_404, redirect, render
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_POST

from django.contrib import messages
from apps.handover.builder import HandoverBlocked, build_handover
from apps.review.models import ReviewDecision

from django.urls import reverse

from apps.accounts.decorators import project_role_required
from apps.audit.logger import log
from apps.extraction.models import ExtractedItem
from apps.rehearsal.engine import run_rehearsal

from . import services


@project_role_required("manager")
def review_home(request, project_id):
    project = request.project
    run = services.latest_run(project)
    questions = []
    for f in services.open_blockers(project):
        d = None
        if run:
            d = (f.item.decisions.filter(action="edited", created_at__gt=run.created_at)
                 .exclude(note="").order_by("-created_at").first())
        questions.append({
            "id": f.item_id, "text": f.item.text, "finding_message": f.message,
            "answered_by": d.reviewer if d else "", "answer_text": d.note if d else "",
            "answer_url": reverse("review:answer", args=[project_id, f.item_id]),
        })
    blockers, pending = len(questions), services.pending_count(project)
    warnings = run.findings.filter(severity="warning").count() if run else 0
    if run is None:
        verdict, vclass = "No rehearsal yet", "warn"
    elif blockers:
        verdict, vclass = f"Not ready: {blockers} blocker(s)", "bad"
    else:
        verdict, vclass = "Ready with conditions", "ok"
    return render(request, "review.html", {
        "project": project, "questions": questions, "blocker_count": blockers,
        "warning_count": warnings, "verdict": verdict, "verdict_class": vclass,
        "approve_url": reverse("review:approve_all", args=[project_id]),
        "rerun_url": reverse("review:rerun", args=[project_id]),
    })


@require_POST
@project_role_required("manager")
def answer(request, project_id, item_id):
    item = get_object_or_404(ExtractedItem, pk=item_id, project=request.project)
    if request.POST.get("action") == "reject":
        services.reject_item(item, request.user, "Finding rejected by reviewer")
    else:
        owner = request.POST.get("owner", "").strip()
        if not owner:
            messages.error(request, "Enter the new owner's name.")
        else:
            services.edit_item(item, request.user, {"owner": owner},
                               request.POST.get("answer", "").strip() or f"{owner} takes over")
    return redirect("review:home", project_id=project_id)


@require_POST
@project_role_required("manager")
def approve_all(request, project_id):
    project = request.project
    for it in project.items.filter(status=ExtractedItem.Status.PENDING):
        services.approve_item(it, request.user, "Approved with handover")
    prev = services.latest_run(project)
    if prev:
        run_rehearsal(project, prev.leaver, prev.leave_date, user=request.user)
    try:
        h = build_handover(project, request.user)
    except HandoverBlocked as e:
        for r in e.reasons:
            messages.error(request, r)
        return redirect("review:home", project_id=project_id)
    messages.success(request, f"Handover v{h.version} built.")
    return redirect("projects:handover", project_id=project_id)


@require_POST
@project_role_required("manager")
def item_action(request, project_id, item_id, action):
    item = get_object_or_404(ExtractedItem, pk=item_id, project=request.project)
    note = request.POST.get("note", "")
    if action == "approve":
        services.approve_item(item, request.user, note)
    elif action == "reject":
        services.reject_item(item, request.user, note)
    return redirect("review:home", project_id=project_id)


@require_POST
@project_role_required("manager")
def item_edit(request, project_id, item_id):
    item = get_object_or_404(ExtractedItem, pk=item_id, project=request.project)
    data = {k: request.POST[k] for k in ("text", "owner", "people", "reason", "date_text")
            if k in request.POST}
    services.edit_item(item, request.user, data, request.POST.get("note", ""))
    return redirect("review:home", project_id=project_id)


@require_POST
@project_role_required("manager")
def rerun(request, project_id):
    project = request.project
    prev = services.latest_run(project)
    leaver = request.POST.get("leaver") or (prev.leaver if prev else "")
    leave_date = parse_date(request.POST.get("leave_date", "")) or (prev.leave_date if prev else None)
    if leaver and leave_date:
        run = run_rehearsal(project, leaver, leave_date, user=request.user)
        log(request.user, "rehearsal.run", project=project, target=run,
            leaver=leaver, leave_date=str(leave_date), blockers=run.blocker_count)
    return redirect("review:home", project_id=project_id)