# OWNER: Dev B
import csv

def read(path) -> str:
    """Turn each row into one 'header: value | ...' line so quotes stay verifiable."""
    lines = []
    with open(path, newline="", encoding="utf-8", errors="ignore") as f:
        for row in csv.DictReader(f):
            lines.append(" | ".join(f"{k}: {v}" for k, v in row.items()))
    return "\n".join(lines)