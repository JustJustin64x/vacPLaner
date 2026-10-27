from __future__ import annotations

from typing import Sequence
from src.vacation_planner.core.domain.value_objects.AccommodationType import AccommodationType
from src.vacation_planner.core.domain.value_objects.DateRange import DateRange
from src.vacation_planner.core.domain.value_objects.MonetaryAmount import MonetaryAmount
from src.vacation_planner.core.domain.value_objects.TransportType import TransportType


class VacationSearchCriteria:
    """
    Domain parameter object encapsulating all user constraints and preferences
    required to generate a synchronized vacation package.
    """

    def __init__(
        self,
        origin_location_name: str,
        destination_location_name: str,
        date_range: DateRange,
        maximum_budget: MonetaryAmount,
        allowed_transport_types: Sequence[TransportType] = (
            TransportType.FLIGHT,
            TransportType.TRAIN,
            TransportType.CAR,
        ),
        preferred_accommodation_type: AccommodationType | None = None,
        number_of_travelers: int = 1,
    ) -> None:
        if not origin_location_name.strip():
            raise ValueError("Origin location name cannot be empty.")
        if not destination_location_name.strip():
            raise ValueError("Destination location name cannot be empty.")
        if number_of_travelers <= 0:
            raise ValueError(f"Number of travelers must be at least 1 (got {number_of_travelers}).")
        if not allowed_transport_types:
            raise ValueError("At least one allowed transport type must be specified.")

        self._origin_location_name: str = origin_location_name.strip()
        self._destination_location_name: str = destination_location_name.strip()
        self._date_range: DateRange = date_range
        self._maximum_budget: MonetaryAmount = maximum_budget
        self._allowed_transport_types: tuple[TransportType, ...] = tuple(allowed_transport_types)
        self._preferred_accommodation_type: AccommodationType | None = (
            preferred_accommodation_type
        )
        self._number_of_travelers: int = number_of_travelers

    @property
    def origin_location_name(self) -> str:
        return self._origin_location_name

    @property
    def destination_location_name(self) -> str:
        return self._destination_location_name

    @property
    def date_range(self) -> DateRange:
        return self._date_range

    @property
    def maximum_budget(self) -> MonetaryAmount:
        return self._maximum_budget

    @property
    def allowed_transport_types(self) -> tuple[TransportType, ...]:
        return self._allowed_transport_types

    @property
    def preferred_accommodation_type(self) -> AccommodationType | None:
        return self._preferred_accommodation_type

    @property
    def number_of_travelers(self) -> int:
        return self._number_of_travelers

    def __repr__(self) -> str:
        return (
            f"VacationSearchCriteria(origin='{self._origin_location_name}', "
            f"destination='{self._destination_location_name}', "
            f"date_range={self._date_range}, budget={self._maximum_budget}, "
            f"travelers={self._number_of_travelers})"
        )
