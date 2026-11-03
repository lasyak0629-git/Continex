# OWNER: Dev A
import calendar
import re
from datetime import date, timedelta

MONTHS = {}
for i in range(1, 13):
    MONTHS[calendar.month_name[i].lower()] = i
    MONTHS[calendar.month_abbr[i].lower()] = i
MONTHS["sept"] = 9

WEEKDAYS = {name.lower(): i for i, name in enumerate(calendar.day_name)}


def _safe_date(year, month, day):
    try:
        return date(year, month, day)
    except ValueError:
        return None


def _next_day_month(day, month, ref):
    d = _safe_date(ref.year, month, day)
    if d and d < ref:
        d = _safe_date(ref.year + 1, month, day)
    return d


def resolve_date(text, ref):
    """Turn wording like 'next Friday' or '15 Nov' into a date. Returns None if unclear."""
    if not text:
        return None
    t = text.strip().lower()

    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", t)
    if m:
        return _safe_date(int(m[1]), int(m[2]), int(m[3]))

    if "today" in t:
        return ref
    if "tomorrow" in t:
        return ref + timedelta(days=1)

    m = re.search(r"\bin (\d+) (day|week)s?\b", t)
    if m:
        n = int(m[1]) * (7 if m[2] == "week" else 1)
        return ref + timedelta(days=n)

    for m in re.finditer(r"\b(\d{1,2})(?:st|nd|rd|th)?\s+(?:of\s+)?([a-z]+)", t):
        if m[2] in MONTHS:
            return _next_day_month(int(m[1]), MONTHS[m[2]], ref)

    for m in re.finditer(r"\b([a-z]+)\s+(\d{1,2})(?:st|nd|rd|th)?\b", t):
        if m[1] in MONTHS:
            return _next_day_month(int(m[2]), MONTHS[m[1]], ref)

    for name, idx in WEEKDAYS.items():
        if re.search(rf"\b{name}\b", t):
            ahead = (idx - ref.weekday()) % 7
            return ref + timedelta(days=ahead or 7)

    if "end of month" in t or "month end" in t:
        return date(ref.year, ref.month, calendar.monthrange(ref.year, ref.month)[1])

    m = re.search(r"\b(\d{1,2})(?:st|nd|rd|th)\b", t)  # "the 15th"
    if m:
        day = int(m[1])
        d = _safe_date(ref.year, ref.month, day)
        if d and d >= ref:
            return d
        nxt_month = ref.month % 12 + 1
        nxt_year = ref.year + (1 if ref.month == 12 else 0)
        return _safe_date(nxt_year, nxt_month, day)

    return None