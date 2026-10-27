from src.vacation_planner.core.domain.value_objects.GeographicCoordinates import GeographicCoordinates


class Location:
    """
    Domain entity representing a geographic location, city, or destination.
    Maintains geographic metadata and coordinates.
    """

    def __init__(
        self,
        location_id: str,
        name: str,
        country_name: str,
        country_code: str,
        coordinates: GeographicCoordinates,
        description: str = "",
    ) -> None:
        if not location_id.strip():
            raise ValueError("Location identifier cannot be empty.")
        if not name.strip():
            raise ValueError("Location name cannot be empty.")

        self._location_id: str = location_id.strip()
        self._name: str = name.strip()
        self._country_name: str = country_name.strip()
        self._country_code: str = country_code.strip().upper()
        self._coordinates: GeographicCoordinates = coordinates
        self._description: str = description.strip()

    @property
    def location_id(self) -> str:
        return self._location_id

    @property
    def name(self) -> str:
        return self._name

    @property
    def country_name(self) -> str:
        return self._country_name

    @property
    def country_code(self) -> str:
        return self._country_code

    @property
    def coordinates(self) -> GeographicCoordinates:
        return self._coordinates

    @property
    def description(self) -> str:
        return self._description

    def calculate_distance_in_kilometers_to(self, other: "Location") -> float:
        return self._coordinates.calculate_distance_in_kilometers_to(other.coordinates)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Location):
            return False
        return self._location_id == other.location_id

    def __repr__(self) -> str:
        return (
            f"Location(id='{self._location_id}', name='{self._name}', "
            f"country='{self._country_name}' [{self._country_code}], coordinates={self._coordinates})"
        )

