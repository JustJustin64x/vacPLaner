from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Any


class MonetaryAmount:
    """
    Immutable value object representing a financial currency amount with high precision.
    Prevents floating-point rounding errors by using Python's Decimal internally.
    """

    __slots__ = ("_amount", "_currency")

    def __init__(self, amount: Decimal | float | int | str, currency: str = "EUR") -> None:
        if isinstance(amount, Decimal):
            parsed_amount = amount
        else:
            parsed_amount = Decimal(str(amount))

        normalized_amount = parsed_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        object.__setattr__(self, "_amount", normalized_amount)
        object.__setattr__(self, "_currency", currency.upper().strip())

    @property
    def amount(self) -> Decimal:
        return self._amount

    @property
    def currency(self) -> str:
        return self._currency

    def add(self, other: "MonetaryAmount") -> "MonetaryAmount":
        self._ensure_matching_currency(other)
        return MonetaryAmount(self._amount + other.amount, self._currency)

    def subtract(self, other: "MonetaryAmount") -> "MonetaryAmount":
        self._ensure_matching_currency(other)
        return MonetaryAmount(self._amount - other.amount, self._currency)

    def multiply(self, factor: Decimal | float | int) -> "MonetaryAmount":
        factor_decimal = Decimal(str(factor))
        return MonetaryAmount(self._amount * factor_decimal, self._currency)

    def is_greater_than(self, other: "MonetaryAmount") -> bool:
        self._ensure_matching_currency(other)
        return self._amount > other.amount

    def is_less_than_or_equal_to(self, other: "MonetaryAmount") -> bool:
        self._ensure_matching_currency(other)
        return self._amount <= other.amount

    def _ensure_matching_currency(self, other: "MonetaryAmount") -> None:
        if self._currency != other.currency:
            raise ValueError(
                f"Currency mismatch error: cannot operate on '{self._currency}' and '{other.currency}'."
            )

    def to_float(self) -> float:
        return float(self._amount)

    def __setattr__(self, key: str, value: Any) -> None:
        raise AttributeError("MonetaryAmount instances are immutable.")

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, MonetaryAmount):
            return False
        return self._amount == other.amount and self._currency == other.currency

    def __lt__(self, other: "MonetaryAmount") -> bool:
        self._ensure_matching_currency(other)
        return self._amount < other.amount

    def __le__(self, other: "MonetaryAmount") -> bool:
        self._ensure_matching_currency(other)
        return self._amount <= other.amount

    def __gt__(self, other: "MonetaryAmount") -> bool:
        self._ensure_matching_currency(other)
        return self._amount > other.amount

    def __ge__(self, other: "MonetaryAmount") -> bool:
        self._ensure_matching_currency(other)
        return self._amount >= other.amount

    def __repr__(self) -> str:
        return f"MonetaryAmount(amount={self._amount}, currency='{self._currency}')"

    def __str__(self) -> str:
        return f"{self._amount:.2f} {self._currency}"
