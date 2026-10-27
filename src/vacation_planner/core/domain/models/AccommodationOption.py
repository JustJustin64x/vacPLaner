from typing import Sequence
from src.vacation_planner.core.domain.value_objects.AccommodationType import AccommodationType
from src.vacation_planner.core.domain.value_objects.DateRange import DateRange
from src.vacation_planner.core.domain.value_objects.GeographicCoordinates import GeographicCoordinates
from src.vacation_planner.core.domain.value_objects.MonetaryAmount import MonetaryAmount


class AccommodationOption:
    """
    Domain entity representing an available overnight lodging facility at the target destination
    for the exact requested date range.
    """

    def __init__(
        self,
        accommodation_id: str,
        name: str,
        accommodation_type: AccommodationType,
        location_name: str,
        coordinates: GeographicCoordinates,
        date_range: DateRange,
        total_price: MonetaryAmount,
        price_per_night: MonetaryAmount,
        star_rating: float,
        address_line: str,
        included_amenities: Sequence[str] = (),
    ) -> None:
        if not accommodation_id.strip():
            raise ValueError("Accommodation identifier cannot be empty.")
        if not name.strip():
            raise ValueError("Accommodation name cannot be empty.")
        if not (0.0 <= star_rating <= 5.0):
            raise ValueError(f"Star rating must be between 0.0 and 5.0 (got {star_rating}).")

        self._accommodation_id: str = accommodation_id.strip()
        self._name: str = name.strip()
        self._accommodation_type: AccommodationType = accommodation_type
        self._location_name: str = location_name.strip()
        self._coordinates: GeographicCoordinates = coordinates
        self._date_range: DateRange = date_range
        self._total_price: MonetaryAmount = total_price
        self._price_per_night: MonetaryAmount = price_per_night
        self._star_rating: float = round(star_rating, 1)
        self._address_line: str = address_line.strip()
        self._included_amenities: tuple[str, ...] = tuple(
            amenity.strip() for amenity in included_amenities if amenity.strip()
        )

    @property
    def accommodation_id(self) -> str:
        return self._accommodation_id

    @property
    def name(self) -> str:
        return self._name

    @property
    def accommodation_type(self) -> AccommodationType:
        return self._accommodation_type

    @property
    def location_name(self) -> str:
        return self._location_name

    @property
    def coordinates(self) -> GeographicCoordinates:
        return self._coordinates

    @property
    def date_range(self) -> DateRange:
        return self._date_range

    @property
    def total_price(self) -> MonetaryAmount:
        return self._total_price

    @property
    def price_per_night(self) -> MonetaryAmount:
        return self._price_per_night

    @property
    def star_rating(self) -> float:
        return self._star_rating

    @property
    def address_line(self) -> str:
        return self._address_line

    @property
    def included_amenities(self) -> tuple[str, ...]:
        return self._included_amenities

    def has_amenity(self, amenity_name: str) -> bool:
        normalized_target = amenity_name.lower().strip()
        return any(
            normalized_target in amenity.lower() for amenity in self._included_amenities
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, AccommodationOption):
            return False
        return self._accommodation_id == other.accommodation_id

    def __repr__(self) -> str:
        return (
            f"AccommodationOption(id='{self._accommodation_id}', name='{self._name}', "
            f"type={self._accommodation_type}, location='{self._location_name}', "
            f"price={self._total_price}, rating={self._star_rating})"
        )
