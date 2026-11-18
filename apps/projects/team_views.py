from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from apps.accounts.verification import is_verified
from apps.accounts.decorators import project_role_required
from apps.audit.logger import log

from .forms import InviteForm, ProjectForm
from .models import Invitation, Membership

from datetime import timedelta

from django.views.decorators.http import require_POST

from .retention import delete_project_data

ROLE_TEXT = {
    "leaver": "the person leaving: you will upload what you know and answer the first review questions",
    "viewer": "a viewer: you will be able to read and download the handover",
    "manager": "a manager: you can upload, review, approve and invite others",
}


@login_required
def project_create(request):
    if not is_verified(request.user):
        return redirect("verify_notice")
    form = ProjectForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        p = form.save(commit=False)
        p.created_by = request.user
        p.save()
        Membership.objects.create(project=p, user=request.user, role="manager")
        log(request.user, "project.created", project=p)
        messages.success(request, "Project created. Invite your team, then upload documents.")
        return redirect("projects:team", project_id=p.id)
    return render(request, "project_form.html", {"form": form})


@project_role_required("manager")
def team(request, project_id):
    project = request.project
    form = InviteForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        email = form.cleaned_data["email"].strip().lower()
        role = form.cleaned_data["role"]
        inv = Invitation.objects.create(project=project, email=email, role=role, invited_by=request.user)
        link = request.build_absolute_uri(reverse("accept_invite", args=[inv.token]))
        body = (
            f"Hello,\n\n{request.user.get_username()} added you to the handover project "
            f"\"{project.name}\" as {ROLE_TEXT[role]}.\n"
            + (f"Purpose: {project.description}\n" if project.description else "")
            + f"\nAccept here (the link works once and expires in 7 days):\n{link}\n\n"
            "If you were not expecting this, you can ignore this email."
        )
        try:
            send_mail(f"You were added to \"{project.name}\" on CONTINEX", body,
                      settings.DEFAULT_FROM_EMAIL, [email])
            messages.success(request, f"Invitation sent to {email}.")
        except Exception as e:  # mail server problem
            messages.error(request, f"Invitation saved but the email failed ({type(e).__name__}).")
        log(request.user, "invite.sent", project=project, role=role)
        return redirect("projects:team", project_id=project.id)
    members = project.memberships.select_related("user", "invited_by")
    pending = project.invitations.filter(accepted_at__isnull=True)
    return render(request, "team.html",
                  {"project": project, "form": form, "members": members, "pending": pending})


@login_required
def accept_invite(request, token):
    inv = get_object_or_404(Invitation, token=token)
    if not inv.is_valid():
        return render(request, "invite_invalid.html", status=410)
    if not is_verified(request.user):
        return redirect("verify_notice")
    if request.user.email.strip().lower() != inv.email.strip().lower():
        return render(request, "invite_wrong_account.html", {"inv": inv}, status=403)
    if request.method == "POST":
        Membership.objects.get_or_create(
            project=inv.project, user=request.user,
            defaults={"role": inv.role, "invited_by": inv.invited_by})
        inv.accepted_at = timezone.now()
        inv.save(update_fields=["accepted_at"])
        log(request.user, "invite.accepted", project=inv.project, role=inv.role)
        messages.success(request, f"You joined \"{inv.project.name}\".")
        return redirect("home")
    return render(request, "invite_accept.html", {"inv": inv, "role_text": ROLE_TEXT.get(inv.role, "")})

@require_POST
@project_role_required("manager")
def extend_retention(request, project_id):
    p = request.project
    p.delete_after = max(p.delete_after or timezone.now(), timezone.now()) + timedelta(days=30)
    p.warned_at = None
    p.save(update_fields=["delete_after", "warned_at"])
    log(request.user, "retention.extended", project=p)
    messages.success(request, "Retention extended by 30 days.")
    return redirect("projects:team", project_id=p.id)


@require_POST
@project_role_required("manager")
def delete_project(request, project_id):
    p = request.project
    if request.POST.get("confirm", "").strip() != p.name:
        messages.error(request, "The name you typed does not match. Nothing was deleted.")
        return redirect("projects:team", project_id=p.id)
    delete_project_data(p, actor=request.user, reason="manager")
    messages.success(request, "The project and all its data were deleted.")
    return redirect("home")