# OWNER: Dev SHARED CONTRACT - agree before editing

"""
SHARED CONTRACT between Developer A (rehearsal/review) and Developer B (extraction).
B's extractor must output a list of ExtractedItemSchema.
Do not change a field name without telling the other developer.
"""
from dataclasses import dataclass, field, asdict
from typing import List, Optional

ITEM_TYPES = (
    "task",             # something someone must do
    "deadline",         # a dated commitment
    "decision",         # a choice that was made (needs a reason)
    "responsibility",   # who owns an area, system or duty
    "access_pointer",   # WHERE something lives or WHO holds it (never the secret itself)
    "claim",            # a statement of fact the handover relies on
)


@dataclass
class ExtractedItemSchema:
    item_type: str                      # one of ITEM_TYPES
    text: str                           # one-sentence normalised statement
    source_name: str                    # file name the item came from
    quote: str                          # verbatim text from the source (must exist in it)
    people: List[str] = field(default_factory=list)   # all people involved
    owner: Optional[str] = None         # the single accountable person, if stated
    date_text: Optional[str] = None     # raw date wording, e.g. "next Friday", "15 Nov"
    reason: Optional[str] = None        # why, for decisions; None if not stated
    confidence: float = 0.0             # 0.0 to 1.0, from the extractor

    def validate(self):
        if self.item_type not in ITEM_TYPES:
            raise ValueError(f"bad item_type: {self.item_type}")
        if not self.text.strip() or not self.quote.strip():
            raise ValueError("text and quote are required")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, d):
        item = cls(**d)
        item.validate()
        return item
