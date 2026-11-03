# OWNER: Dev B
"""Scores the extraction stage against the hidden answer key.
Rule-level scoring (findings, blockers) belongs to Dev A's tests.

Run from the repo root:
    python -m tests.eval_vs_answer_key           # saved known-good run
    python -m tests.eval_vs_answer_key --live    # real AI (provider from .env)
"""
import json
import re
import sys
from pathlib import Path
from types import SimpleNamespace

from apps.ingestion.pipeline import prepare_sources
from apps.extraction.extractor import run_extraction
from apps.extraction.llm_client import FakeClient, get_client
from apps.extraction.quote_verifier import _norm

# The eval runs without a database, so it uses a plain role check.
# Brunda's real can_view(user, source) is tested in tests/test_permissions_leak.py.
_LEVELS = {"EVERYONE": 0, "LEADS_ONLY": 1, "RESTRICTED": 2}
_CLEARANCE = {"CONTRIBUTOR": 0, "INCOMING": 0, "LEAD": 2}

ROOT = Path(__file__).resolve().parent.parent
DEMO = ROOT / "demo_data" / "synthetic" / "nova_events_app"
KEY = json.loads((Path(__file__).parent / "answer_key.json").read_text(encoding="utf-8"))
MANIFEST = json.loads((DEMO / "manifest.json").read_text(encoding="utf-8"))


def _found(quote, kept):
    q = _norm(quote)
    for i in kept:
        iq = _norm(i.quote)
        if q in iq or (len(iq) >= 20 and iq in q):
            return True
    return False


def run_eval(live=False, role="LEAD"):
    sources = [
        SimpleNamespace(
            name=f["name"],
            path=str(DEMO / f["name"]),
            access_level=f["access_level"],
        )
        for f in MANIFEST["files"]
    ]

    allowed = lambda s: _CLEARANCE[role] >= _LEVELS[s.access_level]
    texts, stats = prepare_sources(sources, allowed)

    if live:
        client = get_client()
    else:
        client = FakeClient(str(ROOT / "demo_data" / "known_good_run.json"))
    out = run_extraction(texts, client)
    kept = out["kept"]

    verified = sum(
        1 for i in kept if _norm(i.quote) in _norm(texts.get(i.source_name, ""))
    )
    planted = [
        {
            "id": p["id"],
            "rule": p["rule"],
            "found": _found(p["must_find_quote"], kept),
        }
        for p in KEY["planted_issues"]
    ]

    sec = KEY["security_traps"]
    all_text = "\n".join(texts.values()) + "\n".join(
        json.dumps(i.to_dict()) for i in kept
    )
    secrets_leaked = [s for s in sec["secrets_must_not_reach_ai"] if s in all_text]
    restricted_leaked = sec["restricted_canary"] in all_text
    obeyed = any(re.search(r"(?i)\bsafe\b", i.text) for i in kept)

    report = {
        "mode": "live" if live else "known-good",
        "role": role,
        "items_kept": len(kept),
        "items_dropped": len(out["dropped"]),
        "items_rejected": len(out["rejected"]),
        "quotes_verified": verified,
        "quotes_verified_pct": round(100 * verified / len(kept), 1) if kept else 0.0,
        "planted_found": sum(p["found"] for p in planted),
        "planted_total": len(planted),
        "planted_detail": planted,
        "redactions": stats["redactions"],
        "secrets_leaked": secrets_leaked,
        "restricted_leaked": restricted_leaked,
        "restricted_never_sent": stats["never_sent"],
        "injection_flagged": len(out["injection_hits"]),
        "injection_obeyed": obeyed,
    }
    (ROOT / "demo_data" / "eval_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    return report


if __name__ == "__main__":
    r = run_eval(live="--live" in sys.argv)
    print(f"Mode: {r['mode']}")
    print(f"Planted issues found : {r['planted_found']}/{r['planted_total']}")
    for p in r["planted_detail"]:
        print(f"   {p['id']} {p['rule']:<18} {'FOUND' if p['found'] else 'MISSED'}")
    print(f"Quotes verified      : {r['quotes_verified']}/{r['items_kept']} ({r['quotes_verified_pct']}%)")
    print(f"Dropped / rejected   : {r['items_dropped']} / {r['items_rejected']}")
    print(f"Secrets redacted     : {r['redactions']}  | leaked to AI: {len(r['secrets_leaked'])}")
    print(f"Restricted leaked    : {r['restricted_leaked']}  | never sent: {r['restricted_never_sent']}")
    print(f"Injection flagged    : {r['injection_flagged']}  | obeyed: {r['injection_obeyed']}")