# OWNER: Dev B
import re

PATTERNS = [
    re.compile(r"(?i)\b(password|passwd|pwd|secret|token|api[_-]?key)\b\s*[:=]\s*\S+"),
    re.compile(r"AKIA[0-9A-Z]{16}"),                       # AWS key id
    re.compile(r"\bsk-[A-Za-z0-9_\-]{20,}"),               # sk- style API keys
    re.compile(r"\bghp_[A-Za-z0-9]{36}\b"),                # GitHub token
    re.compile(r"(?i)\bbearer\s+[A-Za-z0-9\-._~+/]{20,}"), # bearer tokens
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----", re.S),
]


def redact(text: str) -> tuple[str, int]:
    """Return (clean_text, number_of_redactions). Runs BEFORE any AI call."""
    count = 0
    for pat in PATTERNS:
        text, n = pat.subn("[REDACTED]", text)
        count += n
    return text, count