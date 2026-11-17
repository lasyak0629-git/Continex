# OWNER Dev: A
from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.projects.models import Project
from apps.projects.retention import delete_project_data


class Command(BaseCommand):
    help = "Warn managers before a project's data is deleted, then delete expired projects."

    def handle(self, *args, **options):
        now = timezone.now()
        soon = now + timedelta(days=settings.RETENTION_WARN_DAYS)
        for p in Project.objects.filter(delete_after__gt=now, delete_after__lte=soon, warned_at__isnull=True):
            emails = [m.user.email for m in p.memberships.filter(role__in=["manager", "owner"])
                      .select_related("user") if m.user.email]
            try:
                if emails:
                    send_mail(
                        f"Project data will be deleted soon: {p.name}",
                        f"The project \"{p.name}\" and all its files will be deleted on "
                        f"{p.delete_after:%d %b %Y}. Download the handover you need now, or extend "
                        f"retention on the Team page:\n{settings.SITE_URL}/projects/{p.id}/team/",
                        settings.DEFAULT_FROM_EMAIL, emails)
            except Exception as e:
                self.stderr.write(f"Warning email failed for project {p.id}: {e}")
                continue  # tried again on the next run
            p.warned_at = now
            p.save(update_fields=["warned_at"])
        expired = list(Project.objects.filter(delete_after__lte=now))
        for p in expired:
            delete_project_data(p)
        self.stdout.write(f"Deleted {len(expired)} expired project(s).")