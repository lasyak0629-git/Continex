# Dev A created
from datetime import date

from django.core.management import call_command
from django.core.management.base import BaseCommand

from apps.accounts.models import User
from apps.extraction.models import ExtractedItem
from apps.handover.builder import HandoverBlocked, build_handover
from apps.handover.role_filter import handover_for_user
from apps.projects.models import Membership, Project, Source
from apps.rehearsal.engine import run_rehearsal
from apps.review import services
from apps.round3.drift_watch import drift_for_user

from apps.handover.models import Handover

DEMO_NAME = "Demo: Nova Events App"
TODAY = date(2026, 11, 3)
LEAVE = date(2026, 11, 10)
LEAVER = "Priya"
DEMO_USERS = [("demo_owner", "owner"), ("demo_manager", "manager"),
              ("demo_member", "member"), ("demo_viewer", "viewer")]


class Command(BaseCommand):
    help = "Rebuild the demo project and walk through the whole flow."

    def say(self, text="", style=None):
        self.stdout.write(getattr(self.style, style)(text) if style else text)

    def show_run(self, run):
        self.say(f"Blockers: {run.blocker_count}", "ERROR" if run.blocker_count else "SUCCESS")
        for f in run.findings.select_related("item").order_by("severity"):
            self.say(f"  {f.severity.upper():8} {f.rule:18} {f.message}")

    def handle(self, *args, **opts):
        Handover.objects.filter(project__name=DEMO_NAME).delete()
        Project.objects.filter(name=DEMO_NAME).delete()  # only the demo project
        users = {}
        for name, role in DEMO_USERS:
            u, _ = User.objects.get_or_create(username=name)
            u.set_password("demo12345")
            u.save()
            users[name] = (u, role)
        owner = users["demo_owner"][0]

        project = Project.objects.create(name=DEMO_NAME, description="Demo", created_by=owner)
        for u, role in users.values():
            Membership.objects.create(project=project, user=u, role=role)
        you = User.objects.filter(is_superuser=True).first()
        if you:  # so you can open the review page in the browser
            Membership.objects.get_or_create(project=project, user=you, defaults={"role": "owner"})

        call_command("load_fake_items", project.pk, verbosity=0)
        Source.objects.filter(project=project, name="secrets_and_restricted.md").update(sensitivity="restricted")
        Source.objects.filter(project=project, name="ops_guide.md").update(sensitivity="public")

        self.say(f"\n1. REHEARSAL: {LEAVER} leaves on {LEAVE:%d %b %Y}", "MIGRATE_HEADING")
        run = run_rehearsal(project, LEAVER, LEAVE, user=owner, today=TODAY)
        self.show_run(run)

        self.say("\n2. REVIEWER FIXES THE BLOCKERS", "MIGRATE_HEADING")
        get = lambda text: ExtractedItem.objects.get(project=project, text=text)
        services.edit_item(get("Venue contract must be signed"), owner, {"owner": "Ravi"}, "Reassigned")
        self.say("  Venue contract reassigned to Ravi")
        services.edit_item(get("Vendor portal login is held by one person"), owner,
                           {"owner": "Ravi", "people": "Priya, Ravi"}, "Second key holder added")
        self.say("  Second person added to the vendor portal login")
        services.reject_item(get("Ticket sales are up 40 percent"), owner, "Quote not found in the source")
        self.say("  Unverified 40 percent claim rejected")
        for it in project.items.filter(status="pending"):
            services.approve_item(it, owner)
        self.say("  Remaining items approved")

        self.say("\n3. RE-RUN THE REHEARSAL", "MIGRATE_HEADING")
        run = run_rehearsal(project, LEAVER, LEAVE, user=owner, today=TODAY)
        self.show_run(run)

        self.say("\n4. HANDOVER", "MIGRATE_HEADING")
        try:
            handover = build_handover(project, owner)
        except HandoverBlocked as e:
            self.say("  Blocked: " + "; ".join(e.reasons), "ERROR")
            return
        self.say(f"  Handover v{handover.version} built", "SUCCESS")

        self.say("\n5. WHO SEES WHAT", "MIGRATE_HEADING")
        for name, (u, role) in users.items():
            r = handover_for_user(u, handover)
            n = sum(len(s["entries"]) for s in r["sections"])
            self.say(f"  {name:13} ({role:7}) sees {n} entries, {r['hidden_total']} hidden")

        self.say("\n6. DRIFT: someone edits an item after handover", "MIGRATE_HEADING")
        services.edit_item(get("Sponsor deck due"), owner, {"owner": "Meera"}, "Ravi handed it over")
        for name in ("demo_owner", "demo_viewer"):
            d = drift_for_user(users[name][0], handover)
            self.say(f"  {name:13} stale={d['is_stale']}, sees {len(d['events'])} event(s), "
                     f"{d['hidden_count']} hidden")

        self.say(f"\nDone. Browser: http://127.0.0.1:8000/projects/{project.pk}/review/", "SUCCESS")