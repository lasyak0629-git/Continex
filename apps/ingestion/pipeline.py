# OWNER: Dev B
from pathlib import Path
from .redactor import redact
from .readers import text, csv_reader, docx_reader, pdf_reader

READERS = {
    ".txt": text.read, ".md": text.read,
    ".csv": csv_reader.read,
    ".docx": docx_reader.read,
    ".pdf": pdf_reader.read,
}


def read_file(path) -> str:
    reader = READERS.get(Path(path).suffix.lower())
    if reader is None:
        raise ValueError(f"Unsupported file type: {path}")
    return reader(path)


def prepare_sources(sources, viewer_role, can_view):
    """
    sources: objects with .name, .path, .access_level
    can_view: Dev A's accounts.permissions.can_view(role, access_level)
    Returns (texts, stats). Restricted files never reach the AI.
    """
    texts = {}
    stats = {"redactions": 0, "skipped_restricted": []}
    for s in sources:
        if not can_view(viewer_role, s.access_level):
            stats["skipped_restricted"].append(s.name)
            continue
        clean, n = redact(read_file(s.path))
        stats["redactions"] += n
        texts[s.name] = clean
    return texts, stats