# OWNER: Dev B writen by Dev A 

from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from apps.accounts.decorators import project_role_required

from .builder import HandoverBlocked, build_handover
from .role_filter import handover_for_user


@project_role_required("viewer")
def handover_page(request, project_id):
    project = request.project
    handover = project.handovers.first()  # newest
    ctx = {"project": project, "handover": handover, "received": False, "receipt_url": ""}
    if handover:
        data = handover_for_user(request.user, handover)  # role-filtered, never raw content
        entries = [e for s in data["sections"] for e in s["entries"]]
        tasks = next((s["entries"] for s in data["sections"] if s["key"] == "task"), [])
        ctx.update({
            "incoming": request.user.get_username(),
            "viewer_role": data["role"],
            "version": {"number": handover.version,
                        "approved_by": handover.created_by,
                        "approved_at": handover.created_at},
            "versions": [{"number": h.version, "approved_at": h.created_at}
                         for h in project.handovers.all()],
            "timeline": sorted(
                ({"date": e["date"], "label": e["text"]} for e in entries if e["date"]),
                key=lambda t: t["date"]),
            "cards": [{"title": t["text"], "status": "open", "owner": t["owner"],
                    "next_step": "", "tried": "",
                    "source_quote": t["quote"], "source_name": t["source"]}
                    for t in tasks],
            "data": data,
            "leaver": data["leaver"],
        })
    return render(request, "handover.html", ctx)


@require_POST
@project_role_required("manager")
def handover_build(request, project_id):
    try:
        h = build_handover(request.project, request.user)
    except HandoverBlocked as e:
        for reason in e.reasons:
            messages.error(request, reason)
    else:
        messages.success(request, f"Handover v{h.version} built.")
    return redirect("projects:handover", project_id=project_id)

