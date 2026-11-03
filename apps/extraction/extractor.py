# OWNER: Dev B
from .prompts import SYSTEM_PROMPT, build_user_prompt
from .injection_guard import parse_llm_output, flag_injection
from .quote_verifier import verify_items


def run_extraction(texts: dict[str, str], client):
    """texts must already be permission-filtered and redacted."""
    injection_hits = flag_injection(texts)
    raw = client.complete(SYSTEM_PROMPT, build_user_prompt(texts))
    result = parse_llm_output(raw, allowed_files=set(texts))
    kept, dropped = verify_items(result.items, texts)
    return {
        "kept": kept,
        "dropped": dropped,              # show the count in the UI
        "injection_hits": injection_hits,
    }