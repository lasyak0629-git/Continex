# OWNER: Dev A
from django.conf import settings
from django.db import models


class Handover(models.Model):
    project = models.ForeignKey("projects.Project", on_delete=models.CASCADE, related_name="handovers")
    run = models.ForeignKey("rehearsal.RehearsalRun", on_delete=models.PROTECT, related_name="handovers")
    version = models.PositiveIntegerField(default=1)
    leaver = models.CharField(max_length=200)
    leave_date = models.DateField()
    content = models.JSONField()  # FULL, unfiltered. Only read it through role_filter.
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.project} handover v{self.version} ({self.leaver})"