import os
from django.core.exceptions import ImproperlyConfigured
from .base import *  # noqa

DEBUG = False
SECRET_KEY = os.environ["SECRET_KEY"]
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", ".onrender.com").split(",")
CSRF_TRUSTED_ORIGINS = os.getenv("CSRF_TRUSTED_ORIGINS", "https://*.onrender.com").split(",")

MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}

FORCE_HTTPS = os.getenv("FORCE_HTTPS", "1") == "1"
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = FORCE_HTTPS
SESSION_COOKIE_SECURE = FORCE_HTTPS
CSRF_COOKIE_SECURE = FORCE_HTTPS
SECURE_HSTS_SECONDS = 86400 if FORCE_HTTPS else 0  # raise this once everything is stable
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"
SESSION_COOKIE_AGE = 60 * 60 * 24 * 7
DATA_UPLOAD_MAX_NUMBER_FILES = 25
AXES_IPWARE_PROXY_COUNT = 1  # one proxy (Render) sits in front
AXES_IPWARE_META_PRECEDENCE_ORDER = ["HTTP_X_FORWARDED_FOR", "REMOTE_ADDR"]

if EMAIL_BACKEND.endswith("console.EmailBackend"):
    import warnings
    warnings.warn("EMAIL_BACKEND is the console backend: verification and invite emails are only "
                  "printed to the log. Configure SMTP before real users sign up.")

if not os.getenv("LLM_PROVIDER"):
    raise ImproperlyConfigured("Set LLM_PROVIDER=gemini in the environment.")
if os.getenv("LLM_PROVIDER") == "fake":
    raise ImproperlyConfigured("LLM_PROVIDER=fake is for development only.")
if os.getenv("LLM_PROVIDER") == "gemini" and not os.getenv("GEMINI_API_KEY"):
    raise ImproperlyConfigured("GEMINI_API_KEY is missing.")