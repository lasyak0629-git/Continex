# OWNER: Dev B
from pathlib import Path
from .redactor import redact
from .readers import text, csv_reader, docx_reader, pdf_reader

READERS = {
    ".txt": text.read,
    ".md": text.read,
    ".csv": csv_reader.read,
    ".docx": docx_reader.read,
    ".pdf": pdf_reader.read,
}


def read_file(path) -> str:
    reader = READERS.get(Path(path).suffix.lower())
    if reader is None:
        raise ValueError(f"Unsupported file type: {path}")
    return reader(path)


def prepare_sources(sources, allowed, never_send=("RESTRICTED",)):
    """
    sources: objects with .name, .path, .access_level
    allowed: a function allowed(source) -> bool, supplied by the caller.
             In Django:  lambda s: can_view(request.user, s)
             In the eval: a plain role check
    Restricted files are never sent to the AI. Redaction runs before anything leaves.
    Returns (texts, stats).
    """
    texts = {}
    stats = {"redactions": 0, "skipped_no_access": [], "never_sent": []}
    for s in sources:
        if s.access_level in never_send:
            stats["never_sent"].append(s.name)
            continue
        if not allowed(s):
            stats["skipped_no_access"].append(s.name)
            continue
        clean, n = redact(read_file(s.path))
        stats["redactions"] += n
        texts[s.name] = clean
    return texts, stats