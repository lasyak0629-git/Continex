# OWNER Dev A
import time

from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
from apps.audit.logger import log
from .forms import SignupForm
from .verification import read_token, send_verification

User = get_user_model()


def signup(request):
    if request.user.is_authenticated:
        return redirect("home")
    form = SignupForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        log(user, "account.created", terms=user.terms_version)
        try:
            send_verification(request, user)
            messages.success(request, "Account created. We sent you an email to confirm your address.")
        except Exception:
            messages.warning(request, "Account created, but the confirmation email could not be sent. Use 'Resend'.")
        nxt = request.GET.get("next", "")
        ok = url_has_allowed_host_and_scheme(nxt, allowed_hosts={request.get_host()})
        return redirect(nxt if ok else "home")
    return render(request, "signup.html", {"form": form})


def verify_email(request, token):
    data = read_token(token)
    user = User.objects.filter(pk=data["u"]).first() if data else None
    if user is None or user.email.lower() != data["e"]:
        return render(request, "verify_result.html", {"ok": False}, status=400)
    if not user.email_verified:
        user.email_verified = True
        user.save(update_fields=["email_verified"])
        log(user, "account.email_verified")
    return render(request, "verify_result.html", {"ok": True})


@login_required
def verify_notice(request):
    return render(request, "verify_notice.html")


@require_POST
@login_required
def resend_verification(request):
    if request.user.email_verified:
        return redirect("home")
    if time.time() - request.session.get("verify_sent", 0) < 60:
        messages.warning(request, "Please wait a minute before asking for another email.")
        return redirect("verify_notice")
    request.session["verify_sent"] = time.time()
    try:
        send_verification(request, request.user)
        messages.success(request, "Confirmation email sent.")
    except Exception:
        messages.error(request, "The email could not be sent. Please try again later.")
    return redirect("verify_notice")


def terms(request):
    from django.conf import settings
    return render(request, "terms.html", {"contact": settings.CONTACT_EMAIL, "version": settings.TERMS_VERSION})


def privacy(request):
    from django.conf import settings
    return render(request, "privacy.html", {"contact": settings.CONTACT_EMAIL, "version": settings.TERMS_VERSION})