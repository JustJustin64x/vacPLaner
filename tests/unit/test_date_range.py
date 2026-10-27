import unittest
from datetime import date
from src.vacation_planner.core.domain.value_objects.DateRange import DateRange


class TestDateRange(unittest.TestCase):
    def test_valid_date_range_nights_calculation(self) -> None:
        dr = DateRange("2026-07-01", "2026-07-08")
        self.assertEqual(dr.start_date, date(2026, 7, 1))
        self.assertEqual(dr.end_date, date(2026, 7, 8))
        self.assertEqual(dr.calculate_total_nights(), 7)
        self.assertEqual(dr.calculate_duration_in_days(), 8)

    def test_invalid_date_range_raises_error(self) -> None:
        with self.assertRaises(ValueError):
            DateRange("2026-07-10", "2026-07-01")

    def test_contains_date(self) -> None:
        dr = DateRange("2026-07-01", "2026-07-10")
        self.assertTrue(dr.contains_date(date(2026, 7, 5)))
        self.assertTrue(dr.contains_date(date(2026, 7, 1)))
        self.assertTrue(dr.contains_date(date(2026, 7, 10)))
        self.assertFalse(dr.contains_date(date(2026, 7, 11)))

    def test_overlaps_with(self) -> None:
        dr1 = DateRange("2026-07-01", "2026-07-10")
        dr2 = DateRange("2026-07-08", "2026-07-15")
        dr3 = DateRange("2026-07-12", "2026-07-20")
        self.assertTrue(dr1.overlaps_with(dr2))
        self.assertFalse(dr1.overlaps_with(dr3))


if __name__ == "__main__":
    unittest.main()

