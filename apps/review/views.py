# OWNER: Dev A logic, B styles template

from django.shortcuts import get_object_or_404, redirect, render
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_POST

from apps.accounts.decorators import project_role_required
from apps.audit.logger import log
from apps.extraction.models import ExtractedItem
from apps.rehearsal.engine import run_rehearsal

from . import services


@project_role_required("manager")
def review_home(request, project_id):
    project = request.project
    run = services.latest_run(project)
    by_item = {}
    if run:
        for f in run.findings.all():
            by_item.setdefault(f.item_id, []).append(f)
    items = list(project.items.select_related("source").order_by("status", "item_type"))
    for it in items:
        it.finding_list = by_item.get(it.id, [])
    ok, reasons = services.can_finalize(project)
    return render(request, "review.html", {
        "project": project, "run": run, "items": items,
        "blockers": services.open_blockers(project),
        "pending": services.pending_count(project),
        "can_finalize": ok, "block_reasons": reasons,
    })


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