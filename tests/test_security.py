# Owner Dev: A
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.accounts.models import User
from apps.projects.models import Membership, Project, Source
from apps.projects.validators import check_content


class UploadChecks(TestCase):
    def test_fake_pdf_is_rejected(self):
        self.assertIsNotNone(check_content(SimpleUploadedFile("a.pdf", b"MZ\x90\x00 program"), ".pdf"))

    def test_real_pdf_header_passes(self):
        self.assertIsNone(check_content(SimpleUploadedFile("a.pdf", b"%PDF-1.7 content"), ".pdf"))

    def test_binary_renamed_to_txt_is_rejected(self):
        self.assertIsNotNone(check_content(SimpleUploadedFile("a.txt", b"\x00\x01\x02"), ".txt"))


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class FileAccess(TestCase):
    def setUp(self):
        mk = lambda n: User.objects.create_user(n, password="x")
        self.mgr, self.viewer, self.outsider = mk("m"), mk("v"), mk("o")
        self.p = Project.objects.create(name="P", created_by=self.mgr)
        Membership.objects.create(project=self.p, user=self.mgr, role="manager")
        Membership.objects.create(project=self.p, user=self.viewer, role="viewer")
        self.src = Source.objects.create(project=self.p, name="n.txt", sensitivity="public",
                                         file=SimpleUploadedFile("n.txt", b"hello"))
        self.url = reverse("projects:source_file", args=[self.p.id, self.src.id])

    def test_manager_can_download(self):
        self.client.force_login(self.mgr)
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_viewer_is_refused(self):
        self.client.force_login(self.viewer)
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_outsider_cannot_even_tell_it_exists(self):
        self.client.force_login(self.outsider)
        self.assertEqual(self.client.get(self.url).status_code, 404)