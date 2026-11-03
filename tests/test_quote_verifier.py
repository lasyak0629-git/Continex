# OWNER: Dev B
from apps.extraction.schemas import ExtractedItemSchema
from apps.extraction.quote_verifier import verify_items

def item(q):
    return ExtractedItemSchema(kind="pointer", subject="SMS", source_file="a.md", source_quote=q)

def test_real_quote_kept_fake_dropped():
    src = {"a.md": "SMS gateway: ask Priya."}
    kept, dropped = verify_items([item("ask Priya"), item("ask Karthik")], src)
    assert len(kept) == 1 and len(dropped) == 1