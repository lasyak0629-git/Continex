# OWNER: Dev A
from datetime import date
from django.test import SimpleTestCase
from apps.rehearsal.date_resolver import resolve_date

REF = date(2026, 11, 2)  # a Monday


class DateResolverTests(SimpleTestCase):
    def test_cases(self):
        cases = {
            "next Friday": date(2026, 11, 6),
            "15 Nov": date(2026, 11, 15),
            "before the 15th": date(2026, 11, 15),
            "tomorrow": date(2026, 11, 3),
            "in 2 weeks": date(2026, 11, 16),
            "end of month": date(2026, 11, 30),
            "2026-12-01": date(2026, 12, 1),
            "Jan 5": date(2027, 1, 5),
        }
        for text, expected in cases.items():
            self.assertEqual(resolve_date(text, REF), expected, text)

    def test_unclear_returns_none(self):
        self.assertIsNone(resolve_date("sometime soon", REF))
        self.assertIsNone(resolve_date("", REF))