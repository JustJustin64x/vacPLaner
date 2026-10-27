import unittest
from decimal import Decimal
from src.vacation_planner.core.domain.value_objects.MonetaryAmount import MonetaryAmount


class TestMonetaryAmount(unittest.TestCase):
    def test_creation_and_normalization(self) -> None:
        money = MonetaryAmount("199.999", "eur")
        self.assertEqual(money.amount, Decimal("200.00"))
        self.assertEqual(money.currency, "EUR")

    def test_addition_same_currency(self) -> None:
        amount_1 = MonetaryAmount("100.50", "EUR")
        amount_2 = MonetaryAmount("49.50", "EUR")
        result = amount_1.add(amount_2)
        self.assertEqual(result.amount, Decimal("150.00"))
        self.assertEqual(result.currency, "EUR")

    def test_addition_different_currency_raises_error(self) -> None:
        eur = MonetaryAmount("100.00", "EUR")
        usd = MonetaryAmount("100.00", "USD")
        with self.assertRaises(ValueError):
            eur.add(usd)

    def test_multiplication(self) -> None:
        price = MonetaryAmount("25.00", "EUR")
        total = price.multiply(4)
        self.assertEqual(total.amount, Decimal("100.00"))

    def test_comparisons(self) -> None:
        low = MonetaryAmount("50.00", "EUR")
        high = MonetaryAmount("150.00", "EUR")
        self.assertTrue(low < high)
        self.assertTrue(high > low)
        self.assertTrue(low <= high)
        self.assertTrue(high >= low)
        self.assertFalse(low == high)

    def test_immutability(self) -> None:
        money = MonetaryAmount("50.00", "EUR")
        with self.assertRaises(AttributeError):
            money.amount = Decimal("60.00")  # type: ignore


if __name__ == "__main__":
    unittest.main()

