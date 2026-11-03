# Dev A created 
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from apps.accounts.models import User
from apps.projects.models import Membership, Project, Source
from apps.projects.services import prepare_texts

SECRET = "TOPSECRET-PASSWORD-123"


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class ExtractionGlueTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user("o", password="x")
        self.viewer = User.objects.create_user("v", password="x")
        self.project = Project.objects.create(name="P", created_by=self.owner)
        Membership.objects.create(project=self.project, user=self.owner, role="owner")
        Membership.objects.create(project=self.project, user=self.viewer, role="viewer")
        for name, sens, body in [
            ("pub.md", "public", "Priya owns sponsors."),
            ("int.md", "internal", "Ravi owns hosting."),
            ("sec.md", "restricted", f"The password is {SECRET}"),
        ]:
            Source.objects.create(project=self.project, name=name, sensitivity=sens,
                                  file=SimpleUploadedFile(name, body.encode()))

    def test_restricted_file_never_reaches_the_model(self):
        texts, stats, _ = prepare_texts(self.project, self.owner)
        self.assertIn("sec.md", stats["never_sent"])
        self.assertNotIn(SECRET, " ".join(texts.values()))
        self.assertEqual(set(texts), {"pub.md", "int.md"})

    def test_viewer_only_gets_public_text(self):
        texts, stats, _ = prepare_texts(self.project, self.viewer)
        self.assertEqual(set(texts), {"pub.md"})
        self.assertIn("int.md", stats["skipped_no_access"])