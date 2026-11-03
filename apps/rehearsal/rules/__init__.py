# OWNER: Dev A
from .orphan_dates import check as orphan_dates
from .single_person import check as single_person
from .unsupported_claims import check as unsupported_claims
from .missing_reason import check as missing_reason

ALL_RULES = [orphan_dates, single_person, unsupported_claims, missing_reason]