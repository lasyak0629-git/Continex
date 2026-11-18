# OWNER Dev A
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from apps.accounts.decorators import project_role_required
from apps.audit.logger import log
from .media import start_transcription
from .models import Source


@project_role_required("manager", allow=("leaver",))
def transcript(request, project_id, source_id):
    src = get_object_or_404(Source, pk=source_id, project=request.project)
    if src.kind == "text" or src.sensitivity == "restricted":
        return redirect("projects:upload", project_id=project_id)
    if request.method == "POST":
        if request.POST.get("action") == "retry":
            src.transcript_status, src.transcript_error = "pending", ""
            src.save(update_fields=["transcript_status", "transcript_error"])
            start_transcription(src.id)
            return redirect("projects:upload", project_id=project_id)
        text = request.POST.get("transcript", "").strip()[:100000]
        if len(text) < 5:
            messages.error(request, "The transcript is empty.")
        else:
            src.transcript, src.transcript_status = text, "confirmed"
            src.save(update_fields=["transcript", "transcript_status"])
            log(request.user, "transcript.confirmed", project=request.project, file=src.name)
            messages.success(request, f"Transcript of {src.name} confirmed. Run the analysis to include it.")
            return redirect("projects:upload", project_id=project_id)
    return render(request, "transcript.html", {"project": request.project, "src": src})