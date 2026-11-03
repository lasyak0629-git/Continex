# OWNER: Dev A
import json
from datetime import date

from django.core.exceptions import PermissionDenied
from django.test import TestCase

from apps.accounts.models import User
from apps.accounts.permissions import can_view
from apps.extraction.models import ExtractedItem
from apps.handover.builder import HandoverBlocked, build_handover
from apps.handover.role_filter import handover_for_user
from apps.projects.models import Membership, Project, Source
from apps.rehearsal.engine import run_rehearsal

PUBLIC, INTERNAL, SECRET = "PUBLIC-FACT-111", "INTERNAL-FACT-222", "RESTRICTED-FACT-333"


class LeakTests(TestCase):
    def setUp(self):
        mk = lambda n: User.objects.create_user(n, password="x")
        self.owner, self.manager, self.member, self.viewer, self.outsider = (
            mk("owner"), mk("manager"), mk("member"), mk("viewer"), mk("outsider"))
        self.project = Project.objects.create(name="P", created_by=self.owner)
        for u, r in [(self.owner, "owner"), (self.manager, "manager"),
                     (self.member, "member"), (self.viewer, "viewer")]:
            Membership.objects.create(project=self.project, user=u, role=r)

        for sens, text in [("public", PUBLIC), ("internal", INTERNAL), ("restricted", SECRET)]:
            src = Source.objects.create(project=self.project, name=f"{sens}.md", sensitivity=sens)
            ExtractedItem.objects.create(
                project=self.project, source=src, item_type="task", text=text,
                quote=f"quote {text}", owner="Ann", people=["Ann", "Bob"],
                quote_verified=True, status="approved")

        run_rehearsal(self.project, "Zed", date(2026, 11, 10), user=self.owner)
        self.handover = build_handover(self.project, self.owner)

    def dump(self, user):
        return json.dumps(handover_for_user(user, self.handover))

    def test_viewer_sees_only_public(self):
        out = self.dump(self.viewer)
        self.assertIn(PUBLIC, out)
        self.assertNotIn(INTERNAL, out)
        self.assertNotIn(SECRET, out)

    def test_member_sees_internal_not_restricted(self):
        out = self.dump(self.member)
        self.assertIn(INTERNAL, out)
        self.assertNotIn(SECRET, out)

    def test_manager_sees_everything(self):
        out = self.dump(self.manager)
        for text in (PUBLIC, INTERNAL, SECRET):
            self.assertIn(text, out)

    def test_hidden_items_are_only_counted(self):
        result = handover_for_user(self.viewer, self.handover)
        self.assertEqual(result["hidden_total"], 2)

    def test_outsider_is_blocked(self):
        with self.assertRaises(PermissionDenied):
            handover_for_user(self.outsider, self.handover)

    def test_source_level_can_view(self):
        secret = Source.objects.get(sensitivity="restricted")
        self.assertFalse(can_view(self.viewer, secret))
        self.assertTrue(can_view(self.manager, secret))
        self.assertFalse(can_view(self.outsider, secret))


class GateTests(TestCase):
    def test_pending_items_block_handover(self):
        u = User.objects.create_user("u", password="x")
        p = Project.objects.create(name="P", created_by=u)
        src = Source.objects.create(project=p, name="a.md")
        ExtractedItem.objects.create(project=p, source=src, item_type="task",
                                     text="t", quote="q", quote_verified=True)
        run_rehearsal(p, "Zed", date(2026, 11, 10), user=u)
        with self.assertRaises(HandoverBlocked):
            build_handover(p, u)