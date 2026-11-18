# OWNER Dev A
import json
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from apps.accounts.models import User
from apps.extraction.models import ExtractedItem
from apps.projects.details import enrich_tasks
from apps.projects.models import Membership, Project, Source

TEXT = b"Send the contract to legal on Monday. We already emailed the venue twice."


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class DetailTests(TestCase):
    def setUp(self):
        self.u = User.objects.create_user("m", password="x")
        self.p = Project.objects.create(name="P", created_by=self.u)
        Membership.objects.create(project=self.p, user=self.u, role="manager")
        self.src = Source.objects.create(project=self.p, name="n.md", sensitivity="public",
                                         file=SimpleUploadedFile("n.md", TEXT))
        self.item = ExtractedItem.objects.create(
            project=self.p, source=self.src, item_type="task", text="Send contract to legal",
            quote="Send the contract to legal on Monday.", quote_verified=True)

    def run_with(self, payload):
        class Fake:
            def complete(self, system, user):
                return json.dumps(payload)
        return enrich_tasks(self.p, self.u, client=Fake())

    def test_verified_quotes_are_saved(self):
        self.run_with([{"id": self.item.id, "next_step": "Send it to legal",
                        "next_step_quote": "Send the contract to legal on Monday.",
                        "tried": "Emailed the venue twice",
                        "tried_quote": "We already emailed the venue twice."}])
        self.item.refresh_from_db()
        self.assertEqual(self.item.next_step, "Send it to legal")
        self.assertEqual(self.item.tried, "Emailed the venue twice")

    def test_invented_quotes_are_dropped(self):
        self.run_with([{"id": self.item.id, "next_step": "Call the CEO",
                        "next_step_quote": "Call the CEO tomorrow."}])
        self.item.refresh_from_db()
        self.assertEqual(self.item.next_step, "")