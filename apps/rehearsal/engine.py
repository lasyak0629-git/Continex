# OWNER: Dev A
from datetime import date

from apps.extraction.models import ExtractedItem
from .date_resolver import resolve_date
from .models import RehearsalRun, Finding
from .rules import ALL_RULES
from .rules.base import Context


def run_rehearsal(project, leaver, leave_date, user=None, today=None):
    today = today or date.today()
    run = RehearsalRun.objects.create(
        project=project, leaver=leaver, leave_date=leave_date, run_on=today, created_by=user
    )
    items = list(project.items.exclude(status=ExtractedItem.Status.REJECTED))

    for it in items:  # resolve dates once and store them
        if it.date_text and not it.date_resolved:
            it.date_resolved = resolve_date(it.date_text, today)
            it.save(update_fields=["date_resolved"])

    ctx = Context(leaver=leaver, leave_date=leave_date, today=today)
    for rule in ALL_RULES:
        for f in rule(items, ctx):
            Finding.objects.create(
                run=run, rule=f.rule, severity=f.severity,
                item=f.item, message=f.message, evidence=f.item.quote,
            )
    return run