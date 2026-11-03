# OWNER: Dev A
from django.conf import settings
from django.db import models
from apps.extraction.models import ExtractedItem
from apps.projects.models import Project


class RehearsalRun(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="runs")
    leaver = models.CharField(max_length=200)
    leave_date = models.DateField()
    run_on = models.DateField()  # the "today" used for resolving dates
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def blocker_count(self):
        return self.findings.filter(severity="blocker").count()

    def __str__(self):
        return f"{self.project} - {self.leaver} leaves {self.leave_date}"


class Finding(models.Model):
    SEVERITIES = [("blocker", "Blocker"), ("warning", "Warning"), ("info", "Info")]

    run = models.ForeignKey(RehearsalRun, on_delete=models.CASCADE, related_name="findings")
    rule = models.CharField(max_length=50)
    severity = models.CharField(max_length=10, choices=SEVERITIES)
    item = models.ForeignKey(ExtractedItem, on_delete=models.CASCADE, related_name="findings")
    message = models.TextField()
    evidence = models.TextField(blank=True)  # the verbatim quote from the source

    def __str__(self):
        return f"[{self.severity}] {self.rule}: {self.message[:60]}"