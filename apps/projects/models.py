# OWNER: Dev A
from django.conf import settings
from django.db import models
import secrets
from datetime import timedelta

from django.utils import timezone

class Project(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    class ProjectType(models.TextChoices):
        SOFTWARE = "software", "Software"
        FINANCE = "finance", "Finance"
        RESEARCH = "research", "Research"
        OPERATIONS = "operations", "Operations"
        OTHER = "other", "Other"
    project_type = models.CharField(max_length=20, choices=ProjectType.choices, default=ProjectType.OTHER)
    leaver_name = models.CharField(max_length=120, blank=True)
    leave_date = models.DateField(null=True, blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_projects"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Membership(models.Model):
    class Role(models.TextChoices):
        OWNER = "owner", "Owner"
        MANAGER = "manager", "Manager"
        MEMBER = "member", "Member"
        LEAVER = "leaver", "Leaving person"
        VIEWER = "viewer", "Viewer"

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="memberships")
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.MEMBER)

    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="sent_invites"
    )

    class Meta:
        unique_together = ("project", "user")

    def __str__(self):
        return f"{self.user} - {self.project} ({self.role})"


class Source(models.Model):
    class Sensitivity(models.TextChoices):
        PUBLIC = "public", "Public"
        INTERNAL = "internal", "Internal"
        RESTRICTED = "restricted", "Restricted"

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="sources")
    name = models.CharField(max_length=255)
    file = models.FileField(upload_to="sources/", blank=True)
    content = models.TextField(blank=True)  # text after reading and redaction
    sensitivity = models.CharField(max_length=20, choices=Sensitivity.choices, default=Sensitivity.INTERNAL)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="uploaded_sources"
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

def make_token():
    return secrets.token_urlsafe(32)


class Invitation(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="invitations")
    email = models.EmailField()
    role = models.CharField(max_length=20, choices=Membership.Role.choices)
    invited_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    token = models.CharField(max_length=64, unique=True, default=make_token)
    created_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)

    def is_valid(self):
        return self.accepted_at is None and self.created_at > timezone.now() - timedelta(days=7)

    def __str__(self):
        return f"{self.email} -> {self.project} ({self.role})"

class AnalysisJob(models.Model):
    class Status(models.TextChoices):
        QUEUED = "queued", "Queued"
        RUNNING = "running", "Running"
        DONE = "done", "Done"
        FAILED = "failed", "Failed"

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="jobs")
    started_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.QUEUED)
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]