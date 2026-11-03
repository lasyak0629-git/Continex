# OWNER: Dev B
# OWNER: Dev B
from apps.extraction.schemas import ExtractedItemSchema
from apps.extraction.quote_verifier import verify_items


def item(q):
    return ExtractedItemSchema(
        item_type="access_pointer", text="SMS gateway held by Priya",
        source_name="a.md", quote=q,
    )


def test_real_quote_kept_fake_dropped():
    src = {"a.md": "SMS gateway: ask Priya."}
    kept, dropped = verify_items([item("ask Priya"), item("ask Karthik")], src)
    assert len(kept) == 1 and len(dropped) == 1