# OWNER: Dev A
from datetime import date
from types import SimpleNamespace as NS
from django.test import SimpleTestCase
from apps.rehearsal.rules import orphan_dates, single_person, unsupported_claims, missing_reason
from apps.rehearsal.rules.base import Context

CTX = Context(leaver="Priya", leave_date=date(2026, 11, 10), today=date(2026, 11, 2))


def item(**kw):
    base = dict(item_type="task", people=[], owner="", date_text="", date_resolved=None,
                reason="", quote="q", quote_verified=True, confidence=0.9)
    base.update(kw)
    return NS(**base)


class RuleTests(SimpleTestCase):
    def test_orphan_date_after_leaving_is_blocker(self):
        out = orphan_dates([item(owner="Priya", date_text="15 Nov")], CTX)
        self.assertEqual(out[0].severity, "blocker")

    def test_date_before_leaving_is_fine(self):
        self.assertEqual(orphan_dates([item(owner="Priya", date_text="5 Nov")], CTX), [])

    def test_other_owner_is_fine(self):
        self.assertEqual(orphan_dates([item(owner="Ravi", date_text="15 Nov")], CTX), [])

    def test_single_person_access_pointer_is_blocker(self):
        out = single_person([item(item_type="access_pointer", people=["Priya"])], CTX)
        self.assertEqual(out[0].severity, "blocker")

    def test_two_people_is_fine(self):
        self.assertEqual(single_person([item(people=["Priya", "Ravi"])], CTX), [])

    def test_unverified_claim_is_blocker(self):
        out = unsupported_claims([item(item_type="claim", quote_verified=False)], CTX)
        self.assertEqual(out[0].severity, "blocker")

    def test_decision_without_reason(self):
        self.assertEqual(len(missing_reason([item(item_type="decision")], CTX)), 1)
        self.assertEqual(missing_reason([item(item_type="decision", reason="cheaper")], CTX), [])