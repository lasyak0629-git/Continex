# Dev A created this file on 2024-06-15
from dataclasses import dataclass
from datetime import date


@dataclass
class Context:
    leaver: str
    leave_date: date
    today: date


@dataclass
class FindingData:
    rule: str
    severity: str
    item: object
    message: str


def same_person(a, b):
    return bool(a) and bool(b) and a.strip().lower() == b.strip().lower()


def owned_by_leaver(item, ctx):
    if item.owner:
        return same_person(item.owner, ctx.leaver)
    return any(same_person(p, ctx.leaver) for p in (item.people or []))