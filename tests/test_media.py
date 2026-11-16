from django.test import TestCase

from apps.accounts.models import User
from apps.projects.models import Membership, Project, Source
from apps.projects.services import prepare_texts


class MediaTests(TestCase):
    def setUp(self):
        self.mgr = User.objects.create_user("m", password="x")
        self.p = Project.objects.create(name="P", created_by=self.mgr)
        Membership.objects.create(project=self.p, user=self.mgr, role="manager")

    def mk(self, name, sens, status, text):
        return Source.objects.create(project=self.p, name=name, file=f"sources/{name}", kind="audio",
                                     sensitivity=sens, transcript=text, transcript_status=status)

    def test_only_confirmed_non_restricted_transcripts_are_analysed(self):
        self.mk("ok.mp3", "public", "confirmed", "Priya owns the portal")
        self.mk("draft.mp3", "public", "ready", "UNCONFIRMED-TEXT")
        self.mk("secret.mp3", "restricted", "confirmed", "RESTRICTED-TEXT")
        texts, stats, _ = prepare_texts(self.p, self.mgr)
        self.assertIn("ok.mp3", texts)
        self.assertNotIn("draft.mp3", texts)
        self.assertNotIn("secret.mp3", texts)
        self.assertIn("draft.mp3", stats["unconfirmed"])
        self.assertIn("secret.mp3", stats["never_sent"])