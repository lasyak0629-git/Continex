# OWNER: Dev A
from django.db import models
from apps.projects.models import Project, Source
from .schemas import ITEM_TYPES, ExtractedItemSchema


class ExtractedItem(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending review"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="items")
    source = models.ForeignKey(Source, on_delete=models.CASCADE, related_name="items")
    item_type = models.CharField(max_length=20, choices=[(t, t) for t in ITEM_TYPES])
    text = models.TextField()
    quote = models.TextField()
    quote_verified = models.BooleanField(default=False)   # set by quote_verifier
    people = models.JSONField(default=list, blank=True)
    owner = models.CharField(max_length=200, blank=True)
    date_text = models.CharField(max_length=200, blank=True)
    date_resolved = models.DateField(null=True, blank=True)  # set by date_resolver
    reason = models.TextField(blank=True)
    confidence = models.FloatField(default=0.0)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.item_type}] {self.text[:60]}"

    @classmethod
    def from_schema(cls, project, source, s: ExtractedItemSchema):
        return cls(
            project=project, source=source, item_type=s.item_type, text=s.text,
            quote=s.quote, people=s.people, owner=s.owner or "",
            date_text=s.date_text or "", reason=s.reason or "", confidence=s.confidence,
        )