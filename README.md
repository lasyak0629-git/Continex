# CONTINEX (Team BLNV FORGE)
Intelligence that keeps work moving.

## Team rules
- Branches: `dev-a-core` (Brunda), `dev-b-ai-ui` (teammate). Never push directly to `main`.
- Merge via Pull Request, reviewed by the other person.
- Pull `main` every morning before starting.
- Never commit `.env`, API keys, or private data. Demo data is made up or public only.
- Shared contract: `apps/extraction/schemas.py`. Change it only after telling each other.

## Folder ownership
- Dev A: config, accounts, rehearsal, review, audit, all models.py, handover logic
- Dev B: ingestion, extraction logic, templates, static, demo_data, upload and handover views

Every file's first line shows its owner.

## Status
Round 1: planning only. Build starts when the official window opens.
## AI tools, libraries and services used
- Claude and ChatGPT: research, drafting and help with code. The team reviewed everything.
- Anthropic API (Claude): reads messy project text and returns structured JSON. It never acts and holds no accounts.
- Django, python-dotenv: backend and settings.
- python-docx, pypdf: file reading.
- pytest, pytest-django: testing.
- Bootstrap 5, HTMX: interface.
- All demo data is made up.