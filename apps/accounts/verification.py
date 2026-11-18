# OWNER Dev A
from django.core import signing
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse

SALT = "verify-email"
MAX_AGE = 3 * 24 * 3600  # links last 3 days


def make_token(user):
    # bound to the address, so a link stops working if the email on the account changes
    return signing.dumps({"u": user.pk, "e": user.email.lower()}, salt=SALT)


def read_token(token):
    try:
        return signing.loads(token, salt=SALT, max_age=MAX_AGE)
    except signing.BadSignature:  # also covers expired links
        return None


def is_verified(user):
    return bool(user.is_authenticated and (user.email_verified or user.is_superuser))


def send_verification(request, user):
    link = request.build_absolute_uri(reverse("verify_email", args=[make_token(user)]))
    send_mail(
        "Confirm your email for CONTINEX",
        f"Hello {user.get_username()},\n\nConfirm your email address to start using CONTINEX:\n"
        f"{link}\n\nThe link works for 3 days. If you did not create this account, ignore this email.",
        settings.DEFAULT_FROM_EMAIL, [user.email])