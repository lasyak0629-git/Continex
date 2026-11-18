# OWNER Dev: A
import tempfile
from datetime import timedelta
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from apps.accounts.models import User
from apps.audit.logger import log
from apps.audit.models import AuditEvent
from apps.projects.models import Membership, Project, Source


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(), EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class RetentionTests(TestCase):
    def setUp(self):
        self.mgr = User.objects.create_user("m", password="x", email="m@example.com")
        self.p = Project.objects.create(name="Alpha", created_by=self.mgr)
        Membership.objects.create(project=self.p, user=self.mgr, role="manager")
        self.src = Source.objects.create(project=self.p, name="n.txt", sensitivity="public",
                                         file=SimpleUploadedFile("n.txt", b"secret text"))
        log(self.mgr, "x.did", project=self.p, note="private detail")

    def test_expired_project_is_purged_and_audit_is_scrubbed(self):
        path = self.src.file.path
        self.p.delete_after = timezone.now() - timedelta(days=1)
        self.p.save()
        call_command("purge_projects")
        self.assertFalse(Project.objects.filter(pk=self.p.pk).exists())
        import os
        self.assertFalse(os.path.exists(path))
        ev = AuditEvent.objects.get(action="x.did")
        self.assertIsNone(ev.project)
        self.assertEqual(ev.detail, {"scrubbed": True})

    def test_warning_email_is_sent_once(self):
        self.p.delete_after = timezone.now() + timedelta(days=5)
        self.p.save()
        call_command("purge_projects")
        call_command("purge_projects")
        self.assertEqual(len(mail.outbox), 1)
        self.assertTrue(Project.objects.filter(pk=self.p.pk).exists())

    def test_manager_delete_needs_exact_name(self):
        self.client.force_login(self.mgr)
        url = reverse("projects:delete_project", args=[self.p.id])
        self.client.post(url, {"confirm": "wrong"})
        self.assertTrue(Project.objects.filter(pk=self.p.pk).exists())
        self.client.post(url, {"confirm": "Alpha"})
        self.assertFalse(Project.objects.filter(pk=self.p.pk).exists())