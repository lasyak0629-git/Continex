# Deploying CONTINEX

Settings module: `config.settings.prod`. The server refuses to start if `LLM_PROVIDER` or `GEMINI_API_KEY` is missing.

## Option A: Docker (recommended)
1. Copy `.env.example` to `.env` and fill it in (also set `POSTGRES_PASSWORD`).
2. `docker compose up -d --build`
3. Open the site. The `scheduler` container deletes expired projects daily.
ClamAV needs about 1.5 GB of RAM. Without it, leave `CLAMD_REQUIRED` empty (uploads are then not virus-scanned).

## Option B: Render (no Docker)
- Build command: `pip install -r requirements.txt && python manage.py collectstatic --noinput`
- Start command: `python manage.py migrate --noinput && gunicorn config.wsgi --bind 0.0.0.0:$PORT --timeout 180 --workers 1 --threads 4`
- Set every variable from `.env.example`. Do NOT use SQLite: the free disk is wiped on restart, which would delete all accounts. Use an external PostgreSQL via `DATABASE_URL`.
- Uploaded files are stored on the server disk, which is also wiped on restart unless a persistent disk is attached.
- Old projects are only deleted when `python manage.py purge_projects` runs. On Render, run it as a scheduled job or by hand.

## Required before real users
- Real SMTP (e.g. Brevo) with a verified sender address, otherwise nobody can verify their email.
- `FORCE_HTTPS=1` and the real domain in `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS` and `SITE_URL`.
- A reviewed Terms and Privacy text (templates `terms.html`, `privacy.html`) and a real `CONTACT_EMAIL`.
- Check Google's current terms for the Gemini tier you use: unpaid tiers may use submitted content to improve products.