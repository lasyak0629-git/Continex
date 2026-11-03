# OWNER: Dev B
from pathlib import Path

def read(path) -> str:
    return Path(path).read_text(encoding="utf-8", errors="ignore")