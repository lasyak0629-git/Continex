# OWNER: Dev SHARED CONTRACT - agree before editing
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


class ExtractedItemSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")  # unknown fields = rejected

    kind: Literal["date", "owner", "pointer", "task", "decision", "claim"]
    subject: str
    person: Optional[str] = None
    raw_date_text: Optional[str] = None   # NOT parsed by the AI
    status: Optional[str] = None          # tasks: open / done
    reason_stated: Optional[bool] = None  # decisions: is a reason recorded?
    source_file: str
    source_quote: str = Field(min_length=3)


class ExtractionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    items: list[ExtractedItemSchema]