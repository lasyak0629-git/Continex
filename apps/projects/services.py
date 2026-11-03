# Dev A created 
from types import SimpleNamespace

from apps.accounts.permissions import can_view
from apps.audit.logger import log
from apps.extraction.extractor import run_extraction
from apps.extraction.llm_client import get_client
from apps.extraction.models import ExtractedItem
from apps.ingestion.pipeline import prepare_sources


def prepare_texts(project, user):
    """Read, permission-filter and redact sources. Restricted files are never sent."""
    sources = list(project.sources.exclude(file=""))
    by_name = {s.name: s for s in sources}
    adapters = [SimpleNamespace(name=s.name, path=s.file.path, access_level=s.sensitivity)
                for s in sources]
    texts, stats = prepare_sources(
        adapters,
        allowed=lambda a: can_view(user, by_name[a.name]),
        never_send=("restricted",),  # lowercase, matches Source.sensitivity
    )
    for name, text in texts.items():
        by_name[name].content = text  # redacted text, kept for display
        by_name[name].save(update_fields=["content"])
    return texts, stats, by_name


def extract_project(project, user, client=None):
    texts, stats, by_name = prepare_texts(project, user)
    summary = {"created": 0, "dropped": 0, "rejected": 0, "injection": 0,
               "never_sent": stats["never_sent"], "skipped": stats["skipped_no_access"],
               "redactions": stats["redactions"]}
    if not texts:
        return summary

    result = run_extraction(texts, client or get_client())
    for s in result["kept"]:
        src = by_name.get(s.source_name)
        if src is None:
            continue
        if ExtractedItem.objects.filter(project=project, source=src,
                                        text=s.text, quote=s.quote).exists():
            continue  # re-running never duplicates items
        item = ExtractedItem.from_schema(project, src, s)
        item.quote_verified = True  # kept = quote found in source
        item.save()
        summary["created"] += 1

    summary["dropped"] = len(result["dropped"])
    summary["rejected"] = len(result["rejected"])
    summary["injection"] = len(result["injection_hits"])
    log(user, "extraction.run", project=project, created=summary["created"],
        dropped=summary["dropped"], rejected=summary["rejected"],
        injection_hits=[str(h) for h in result["injection_hits"]],
        never_sent=stats["never_sent"], skipped=stats["skipped_no_access"])
    return summary