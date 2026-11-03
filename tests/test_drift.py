# Dev A created 
import json
from datetime import date

from django.test import TestCase

from apps.accounts.models import User
from apps.extraction.models import ExtractedItem
from apps.handover.builder import build_handover
from apps.projects.models import Membership, Project, Source
from apps.rehearsal.engine import run_rehearsal
from apps.review import services
from apps.round3.drift_watch import drift_for_user

SECRET = "RESTRICTED-DRIFT-999"


class DriftTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user("owner", password="x")
        self.viewer = User.objects.create_user("viewer", password="x")
        self.project = Project.objects.create(name="P", created_by=self.owner)
        Membership.objects.create(project=self.project, user=self.owner, role="owner")
        Membership.objects.create(project=self.project, user=self.viewer, role="viewer")
        self.restricted = Source.objects.create(project=self.project, name="r.md", sensitivity="restricted")
        self.item = ExtractedItem.objects.create(
            project=self.project, source=self.restricted, item_type="task", text=SECRET,
            quote="q", owner="Ann", people=["Ann", "Bob"], quote_verified=True, status="approved")
        run_rehearsal(self.project, "Zed", date(2026, 11, 10), user=self.owner)
        self.handover = build_handover(self.project, self.owner)

    def test_fresh_handover_is_not_stale(self):
        self.assertFalse(drift_for_user(self.owner, self.handover)["is_stale"])

    def test_edit_after_handover_is_drift(self):
        services.edit_item(self.item, self.owner, {"owner": "Bob"})
        result = drift_for_user(self.owner, self.handover)
        self.assertTrue(result["is_stale"])
        self.assertEqual(result["events"][0]["kind"], "item_edited")

    def test_new_source_is_drift(self):
        Source.objects.create(project=self.project, name="new.md", sensitivity="public")
        result = drift_for_user(self.owner, self.handover)
        self.assertTrue(any(e["kind"] == "new_source" for e in result["events"]))

    def test_viewer_never_sees_restricted_text(self):
        services.edit_item(self.item, self.owner, {"owner": "Bob"})
        result = drift_for_user(self.viewer, self.handover)
        self.assertTrue(result["is_stale"])
        self.assertNotIn(SECRET, json.dumps(result))
        self.assertEqual(result["hidden_count"], 1)