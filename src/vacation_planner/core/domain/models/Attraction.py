from src.vacation_planner.core.domain.value_objects.GeographicCoordinates import GeographicCoordinates
from src.vacation_planner.core.domain.value_objects.MonetaryAmount import MonetaryAmount


class Attraction:
    """
    Domain entity representing a tourist attraction, cultural landmark, or recreational activity
    situated within or near a travel destination.
    """

    def __init__(
        self,
        attraction_id: str,
        name: str,
        location_name: str,
        category: str,
        coordinates: GeographicCoordinates,
        admission_fee: MonetaryAmount,
        estimated_visit_duration_in_minutes: int,
        user_rating: float,
        description: str = "",
    ) -> None:
        if not attraction_id.strip():
            raise ValueError("Attraction identifier cannot be empty.")
        if not name.strip():
            raise ValueError("Attraction name cannot be empty.")
        if not (0.0 <= user_rating <= 5.0):
            raise ValueError(f"User rating must be between 0.0 and 5.0 (got {user_rating}).")
        if estimated_visit_duration_in_minutes < 0:
            raise ValueError("Estimated visit duration cannot be negative.")

        self._attraction_id: str = attraction_id.strip()
        self._name: str = name.strip()
        self._location_name: str = location_name.strip()
        self._category: str = category.strip().upper()
        self._coordinates: GeographicCoordinates = coordinates
        self._admission_fee: MonetaryAmount = admission_fee
        self._estimated_visit_duration_in_minutes: int = estimated_visit_duration_in_minutes
        self._user_rating: float = round(user_rating, 2)
        self._description: str = description.strip()

    @property
    def attraction_id(self) -> str:
        return self._attraction_id

    @property
    def name(self) -> str:
        return self._name

    @property
    def location_name(self) -> str:
        return self._location_name

    @property
    def category(self) -> str:
        return self._category

    @property
    def coordinates(self) -> GeographicCoordinates:
        return self._coordinates

    @property
    def admission_fee(self) -> MonetaryAmount:
        return self._admission_fee

    @property
    def estimated_visit_duration_in_minutes(self) -> int:
        return self._estimated_visit_duration_in_minutes

    @property
    def user_rating(self) -> float:
        return self._user_rating

    @property
    def description(self) -> str:
        return self._description

    def is_admission_free(self) -> bool:
        return self._admission_fee.to_float() == 0.0

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Attraction):
            return False
        return self._attraction_id == other.attraction_id

    def __repr__(self) -> str:
        return (
            f"Attraction(id='{self._attraction_id}', name='{self._name}', "
            f"category='{self._category}', fee={self._admission_fee}, rating={self._user_rating})"
        )

