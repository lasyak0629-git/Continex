# OWNER: Dev B
import json
import re
from pydantic import ValidationError
from .schemas import ExtractionResult

SUSPICIOUS = re.compile(
    r"(?i)(ignore (all )?(previous|prior) instructions|disregard .{0,30}instructions|"
    r"mark (everything|this|all) (as )?safe|you are now|system prompt)"
)


def flag_injection(texts: dict[str, str]) -> list[dict]:
    """Detect and report hidden instructions. They are logged, never obeyed."""
    hits = []
    for name, body in texts.items():
        for line in body.splitlines():
            if SUSPICIOUS.search(line):
                hits.append({"file": name, "line": line.strip()})
    return hits


def parse_llm_output(raw: str, allowed_files: set[str]) -> ExtractionResult:
    """Strict schema lock: anything that is not the exact structure is rejected."""
    raw = re.sub(r"^```(?:json)?|```$", "", raw.strip(), flags=re.M).strip()
    try:
        result = ExtractionResult.model_validate(json.loads(raw))
    except (json.JSONDecodeError, ValidationError) as e:
        raise ValueError(f"LLM output rejected: {e}")
    # drop items that cite a file we never sent
    result.items = [i for i in result.items if i.source_file in allowed_files]
    return result