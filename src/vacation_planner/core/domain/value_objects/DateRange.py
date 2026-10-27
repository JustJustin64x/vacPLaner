from __future__ import annotations

from datetime import date
from typing import Any


class DateRange:
    """
    Immutable value object representing a continuous period between two calendar dates.
    Validates chronological order and calculates duration metrics such as total nights.
    """

    __slots__ = ("_start_date", "_end_date")

    def __init__(self, start_date: date | str, end_date: date | str) -> None:
        parsed_start_date = (
            date.fromisoformat(start_date) if isinstance(start_date, str) else start_date
        )
        parsed_end_date = (
            date.fromisoformat(end_date) if isinstance(end_date, str) else end_date
        )

        if parsed_start_date > parsed_end_date:
            raise ValueError(
                f"Invalid date range: start_date ({parsed_start_date}) cannot be after end_date ({parsed_end_date})."
            )

        object.__setattr__(self, "_start_date", parsed_start_date)
        object.__setattr__(self, "_end_date", parsed_end_date)

    @property
    def start_date(self) -> date:
        return self._start_date

    @property
    def end_date(self) -> date:
        return self._end_date

    def calculate_total_nights(self) -> int:
        """Returns the number of overnight stays between the start and end date."""
        return (self._end_date - self._start_date).days

    def calculate_duration_in_days(self) -> int:
        """Returns the total number of calendar days inclusive of start and end dates."""
        return (self._end_date - self._start_date).days + 1

    def contains_date(self, target_date: date) -> bool:
        """Determines if a given date falls within this range inclusive."""
        return self._start_date <= target_date <= self._end_date

    def overlaps_with(self, other: "DateRange") -> bool:
        """Determines if this date range has any overlapping days with another date range."""
        return self._start_date <= other.end_date and self._end_date >= other.start_date

    def __setattr__(self, key: str, value: Any) -> None:
        raise AttributeError("DateRange instances are immutable.")

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DateRange):
            return False
        return self._start_date == other.start_date and self._end_date == other.end_date

    def __repr__(self) -> str:
        return f"DateRange(start_date={self._start_date.isoformat()}, end_date={self._end_date.isoformat()})"

    def __str__(self) -> str:
        return f"{self._start_date.isoformat()} to {self._end_date.isoformat()}"
