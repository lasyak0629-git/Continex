# OWNER Dev A
from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User
from apps.accounts.verification import make_token, read_token
from apps.projects.models import Invitation, Membership, Project


class AccountTests(TestCase):
    def mk(self, name, email, verified=False):
        u = User.objects.create_user(name, email=email, password="x")
        u.email_verified = verified
        u.save()
        return u

    def test_token_roundtrip_and_tamper(self):
        u = self.mk("a", "a@example.com")
        token = make_token(u)
        self.assertEqual(read_token(token)["u"], u.pk)
        self.assertIsNone(read_token(token + "x"))

    def test_verify_link_marks_verified(self):
        u = self.mk("a", "a@example.com")
        self.client.get(reverse("verify_email", args=[make_token(u)]))
        u.refresh_from_db()
        self.assertTrue(u.email_verified)

    def test_unverified_cannot_create_project(self):
        self.client.force_login(self.mk("a", "a@example.com"))
        r = self.client.get(reverse("projects:create"))
        self.assertRedirects(r, reverse("verify_notice"), fetch_redirect_response=False)

    def test_invite_is_bound_to_the_invited_verified_email(self):
        mgr = self.mk("m", "m@example.com", True)
        p = Project.objects.create(name="P", created_by=mgr)
        Membership.objects.create(project=p, user=mgr, role="manager")
        inv = Invitation.objects.create(project=p, email="b@example.com", role="viewer", invited_by=mgr)
        url = reverse("accept_invite", args=[inv.token])

        other = self.mk("o", "o@example.com", True)
        self.client.force_login(other)
        self.assertEqual(self.client.post(url).status_code, 403)
        self.assertFalse(Membership.objects.filter(project=p, user=other).exists())

        right = self.mk("b", "B@Example.com", True)
        self.client.force_login(right)
        self.client.post(url)
        self.assertTrue(Membership.objects.filter(project=p, user=right).exists())

    def test_signup_needs_terms(self):
        data = {"username": "new", "email": "n@example.com",
                "password1": "Str0ng-pass-123", "password2": "Str0ng-pass-123"}
        self.client.post(reverse("signup"), data)
        self.assertFalse(User.objects.filter(username="new").exists())
        self.client.post(reverse("signup"), {**data, "accept_terms": "on"})
        u = User.objects.get(username="new")
        self.assertIsNotNone(u.terms_accepted_at)
        self.assertFalse(u.email_verified)