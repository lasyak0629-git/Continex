# OWNER: Dev A
from django.test import TestCase

from apps.accounts.models import User
from apps.audit.models import AuditEvent
from apps.extraction.models import ExtractedItem
from apps.projects.models import Project, Source
from apps.review import services


class AuditTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("a", password="x")
        self.project = Project.objects.create(name="P", created_by=self.user)
        src = Source.objects.create(project=self.project, name="n.md")
        self.item = ExtractedItem.objects.create(
            project=self.project, source=src, item_type="task", text="t", quote="q", owner="Priya"
        )

    def test_approve_logs_event(self):
        services.approve_item(self.item, self.user)
        self.item.refresh_from_db()
        self.assertEqual(self.item.status, "approved")
        self.assertTrue(AuditEvent.objects.filter(action="item.approved").exists())

    def test_edit_records_old_and_new(self):
        services.edit_item(self.item, self.user, {"owner": "Ravi"})
        ev = AuditEvent.objects.get(action="item.edited")
        self.assertEqual(ev.detail["changes"]["owner"], ["Priya", "Ravi"])

    def test_audit_is_append_only(self):
        services.approve_item(self.item, self.user)
        ev = AuditEvent.objects.first()
        with self.assertRaises(PermissionError):
            ev.delete()
        ev.action = "tampered"
        with self.assertRaises(PermissionError):
            ev.save()

    def test_cannot_finalize_before_a_rehearsal(self):
        ok, reasons = services.can_finalize(self.project)
        self.assertFalse(ok)