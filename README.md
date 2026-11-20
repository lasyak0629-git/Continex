# CONTINEX

**Find out what breaks when someone leaves, before they leave.**

CONTINEX helps a team prepare a safe handover when a member is leaving. A manager creates a project, invites the leaving person and the newcomer, and uploads the project's records (notes, task lists, documents, even photos of handwriting and voice notes). The AI reads them and proposes facts, ordinary code checks every fact against a source quote and applies risk rules, and people review and approve. The result is a role-filtered handover that can be downloaded as PDF or Word.

> The AI only **proposes**. Code **verifies**. People **decide**.

---

## How it works

1. **Create a project** (name, purpose, who is leaving, last working day). The creator becomes its manager.
2. **Invite people by email**: the leaving person, the newcomer, other managers. Each invitation is tied to the invited email address.
3. **Upload records** with an access level per file: public, internal or restricted. Photos, scans and audio are transcribed to text, and a person confirms the text before it is used.
4. **Analyse.** Restricted files are never sent to the AI, and secrets are hidden before anything is sent. The AI extracts tasks, owners, deadlines, decisions and access points. Each item must carry an exact quote that is found in its source file, otherwise it is dropped. A second pass finds "missing information" questions and next steps, again only when a quote verifies.
5. **Departure Rehearsal.** Rule-based code compares the extracted facts with the leave date and raises blockers and warnings (for example, a task due after the person leaves and still owned by them, or an access point held by only one person).
6. **Two-stage review.** The manager sends the project to the leaving person, who answers questions and uploads anything missed. The manager then does the second review and approves. Approval is blocked while blockers remain or while the project is waiting on the leaver.
7. **Handover.** An approved, versioned handover is built. Newcomers and viewers can open and download it, and confirm receipt. What each person sees depends on their role and each file's access level.

## Features

- Accounts: sign-up with terms consent, email verification, login, logout, forgot-password, login attempt limiting
- Per-project roles: manager, leaving person, viewer (plus owner and member)
- Email invitations (single-use links, expire in 7 days) and notifications (invites, review requests, handover ready, retention warnings)
- Upload checks: file type allow-list, content check against the extension, size limits, optional ClamAV virus scan
- Secret redaction and best-effort prompt-injection flagging before analysis
- Evidence rule: every extracted fact, gap question and next step is backed by a quote verified in the source file
- Transcription of photos, scanned PDFs and audio with mandatory human confirmation
- Background analysis with a live status page
- Role-filtered handover, version history, receipts, PDF and Word downloads
- Audit log of uploads, analysis, review decisions, approvals, downloads and deletions
- Data retention: automatic deletion after a period with an email warning, manager extension and manual deletion

## User roles

| Role | Can do |
|---|---|
| **Manager / owner** | Create the project, invite people, upload, review, approve, build and download the handover, extend retention, delete the project |
| **Leaving person** | Upload documents, answer questions, do the first review, submit to the manager |
| **Member** | See internal-level information |
| **Viewer / newcomer** | View and download the handover (only what their access level allows) and confirm receipt |

Roles are per project: the same person can be a manager of one project and a viewer of another.

## Tech stack

| Layer | Technology | Why |
|---|---|---|
| Web framework | Django 5.2 (Python) | Auth, ORM, templates, admin and security defaults in one framework |
| Database | SQLite (development), PostgreSQL (production / Docker) | Zero setup locally, robust in production |
| Frontend | Django templates, Bootstrap 5, htmx, custom CSS | Clean UI without a heavy JavaScript framework |
| AI | Google Gemini API (text, images, audio) | Extraction and transcription only; never makes decisions |
| Documents | ReportLab (PDF), python-docx (Word) | Downloadable handovers |
| Security add-ons | django-axes, ClamAV (optional) | Login throttling, virus scanning |
| Serving | gunicorn, WhiteNoise | Production serving |
| Packaging | Docker, Docker Compose | One recipe for app, database, scanner and scheduler |

## Project structure

```
apps/
  accounts/    users, roles, permission checks, sign-up, email verification
  projects/    projects, team and invitations, uploads, background jobs, gap questions,
               transcripts, retention and deletion, protected file access
  ingestion/   reading files and redacting secrets
  extraction/  AI client, extraction, quote verifier, injection guard
  rehearsal/   Departure Rehearsal rule engine (blockers and warnings)
  review/      answer, reject, approve, review stages
  handover/    handover builder, role filter, PDF/Word documents, receipts
  audit/       append-only audit log
config/        settings (base, dev, prod), URLs
templates/     HTML templates      static/   CSS and JavaScript
tests/         automated tests and an evaluation script
demo_data/     synthetic sample case used only by the evaluation script (the app never loads it)
```

## Getting started (local)

Requirements: Python 3.12+ and a Gemini API key from Google AI Studio.

```powershell
git clone <repo-url>
cd Continex
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env          # then fill in the values
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open http://127.0.0.1:8000/ and create an account. In development the settings module is `config.settings.dev`, and emails (verification, invitations, password reset) are printed in the terminal unless you configure SMTP.

### Tests

```powershell
python manage.py test tests
python -m pytest tests/test_injection.py -q          # prompt-injection and output-schema tests (pytest style)
python manage.py makemigrations --check --dry-run   # must report: No changes detected
```

The suite covers permissions and role filtering, the restricted-file rule, rehearsal rules, the review gate, the audit log, upload validation, protected file access, retention and deletion, invitations and verification, and the quote-verified extras. The injection tests check that common injection phrases are flagged and that AI output with an unexpected shape, extra fields or an unknown item type is rejected. Tests use stand-in AI clients, so they never call the real AI.

### Docker

```powershell
docker compose up --build
```

Starts the app, PostgreSQL, ClamAV and a daily scheduler that deletes expired projects. ClamAV needs roughly 1.5 GB of RAM and downloads virus definitions on first start. Uploads show "could not be scanned" until it is ready, because the scanner fails closed when `CLAMD_REQUIRED=1`.

For hosting, see [deploy.md](deploy.md).

## Configuration

Copy `.env.example` to `.env`. Never commit `.env`.

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | Django secret key (use a long random string) |
| `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `SITE_URL` | Your domain(s) |
| `FORCE_HTTPS` | `1` in production, `0` for local HTTP |
| `DATABASE_URL` | PostgreSQL connection string (SQLite is used if unset) |
| `POSTGRES_PASSWORD` | Used by Docker Compose |
| `LLM_PROVIDER` | `gemini` for real use. `fake` is for development and tests only; production refuses to start with it |
| `GEMINI_API_KEY`, `GEMINI_MODEL`, `GEMINI_FALLBACK_MODEL` | AI settings. The fallback model is tried if the main one is overloaded |
| `EMAIL_BACKEND`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `DEFAULT_FROM_EMAIL` | SMTP (for example Brevo). Use the form `CONTINEX <sender@example.com>` with a sender you verified in your provider. Without working email, nobody can verify their account in production |
| `CONTACT_EMAIL` | Shown on the terms and privacy pages (set this to a real address) |
| `RETENTION_DAYS` | Days to keep a project after its latest handover (default 90) |
| `CLAMD_HOST`, `CLAMD_PORT`, `CLAMD_REQUIRED` | Virus scanning (`CLAMD_REQUIRED=1` blocks uploads if the scanner is down) |
| `MEDIA_ROOT` | Where uploaded files are stored |

Retention is enforced by `python manage.py purge_projects` (run daily by the Docker `scheduler`, or schedule it on your host).

## Supported inputs

Text documents: `.txt`, `.md`, `.csv`, `.docx`, `.pdf`. Photos: `.png`, `.jpg`, `.jpeg`, `.webp`. Audio: `.mp3`, `.wav`, `.ogg`, `.aac`, `.flac`. Scanned PDFs are detected and transcribed. Limits: 10 MB per document, 15 MB per photo or audio file, 20 files per upload.

## Security design

- Permission checks run on the server on every request. Non-members get a 404, so a project's existence isn't revealed.
- The handover and its downloads always pass through the role filter, and hidden items are only counted, never shown.
- Uploaded originals are served only through a permission-checked download, never from a public folder.
- Restricted files are never sent to the AI. Secrets are redacted from text before it is sent.
- Documents are treated as data. The AI has no tools and returns structured output only, so injected text cannot trigger actions, and anything it returns without a verifiable quote is discarded.
- A phrase-based guard flags common prompt-injection wording in uploaded text and records it. This is a best-effort measure, not a guarantee (see limitations).
- Invitation and password-reset links are signed or single-use and expire. Invitations only work for the invited, verified email address.
- Django's protections against SQL injection, cross-site scripting and CSRF are enabled. Uploaded content is never executed.
- Production settings enforce HTTPS, secure cookies and strict headers.

This design has not been independently audited or penetration-tested.

## Known limitations

Please read these before relying on CONTINEX.

- **"Verified" means the quote exists in the source file.** It does not prove the claim is true or correctly interpreted. A real quote can still be misread.
- **AI accuracy has not been measured.** There is no benchmark or accuracy figure. Always review the results.
- **People are matched by name text.** Name variants ("Priya" and "Priya S.") are treated as different, and the leaving person's name must match the documents.
- **The rule set is small** (work left ownerless after the leave date, access held by one person, unverified claims, decisions without reasons). It is not a complete risk analysis.
- **Approving the handover approves all pending items at once.** Item-by-item sign-off is not built, and rejecting a finding has no undo.
- **Background jobs run inside the web process.** They are lost if the server restarts and there is no real job queue yet.
- **Prompt-injection defence is best-effort.** The guard recognises common injection phrases, not every wording. A document that tries to make the AI leave something out could still succeed, because the quote check proves what is reported, not what was missed. Reviewers should compare the results with the source files.
- **Privacy depends on the AI provider.** Document text, photos, scans and audio are sent to Google's Gemini service. Free tiers may use submitted content to improve Google's products, so check the current terms. Photos and audio cannot be redacted before they are sent.
- **Free hosting may lose data.** Uploaded files and SQLite databases do not persist on many free tiers. Use PostgreSQL and persistent storage for real use.
- **Not load-tested.** Designed for small teams.
- **Input is uploaded files only.** There are no live connectors (GitHub, chat tools) and no source-code analysis.
- **Handwriting and speech transcripts can be wrong,** which is why a person must confirm them.
- **PDF output uses a Latin-only font**, so non-Latin text shows as `?`.
- **No account deletion or data export inside the app yet.** The terms and privacy pages are plain-language drafts, not legal advice.

## Roadmap

Item-by-item approval with undo, name matching and aliases, a real job queue, evidence-gated Q&A over the approved handover, git-history risk signals, a continuity monitor that flags stale handovers, two-factor login, GitHub and cloud-drive connectors, Unicode PDF fonts, and measured evaluation of extraction accuracy.

## Credits

CONTINEX was built by two developers. The table shows primary ownership; both contributed fixes across the codebase.

| | Primary contribution |
|---|---|
| **Brunda (Dev A)** | Accounts, roles and permission checks; the Departure Rehearsal rule engine; the review flow and approval gate; the handover builder and role filter; the audit log |
| **Lasya (Dev B)** | File ingestion and secret redaction; AI extraction (model client, prompts, quote verifier, prompt-injection guard); the original interface templates; the synthetic sample case |

**Multi-user upgrade (Dev A):** sign-up, email verification and password reset; projects with per-project roles and email invitations; the two-stage review; AI gap questions and next steps; transcripts for photos, scans and audio; PDF and Word handover documents with receipts; upload validation, protected file access, login throttling and retention; Docker packaging; the redesigned interface; the tests for these parts.

**Repository and deployment:** the repository belongs to Dev B, who also handles the deployment on Render.

Developed with the help of AI coding tools.

## License

No open-source license has been chosen yet, so all rights are reserved by the authors.