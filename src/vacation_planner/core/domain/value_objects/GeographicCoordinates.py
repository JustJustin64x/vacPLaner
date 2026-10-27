import math
from typing import Any


class GeographicCoordinates:
    """
    Represents an exact geographical position on Earth defined by latitude and longitude.
    Provides mathematical operations like great-circle distance calculation via the Haversine formula.
    """

    __slots__ = ("_latitude", "_longitude")

    EARTH_RADIUS_KILOMETERS: float = 6371.0088

    def __init__(self, latitude: float, longitude: float) -> None:
        if not (-90.0 <= latitude <= 90.0):
            raise ValueError(
                f"Invalid latitude value: {latitude}. Latitude must be between -90.0 and +90.0 degrees."
            )
        if not (-180.0 <= longitude <= 180.0):
            raise ValueError(
                f"Invalid longitude value: {longitude}. Longitude must be between -180.0 and +180.0 degrees."
            )

        object.__setattr__(self, "_latitude", float(latitude))
        object.__setattr__(self, "_longitude", float(longitude))

    @property
    def latitude(self) -> float:
        return self._latitude

    @property
    def longitude(self) -> float:
        return self._longitude

    def calculate_distance_in_kilometers_to(self, other: "GeographicCoordinates") -> float:
        """
        Calculates the great-circle spherical distance between this point and another point
        using the Haversine formula.
        """
        latitude_1_radians = math.radians(self._latitude)
        longitude_1_radians = math.radians(self._longitude)
        latitude_2_radians = math.radians(other.latitude)
        longitude_2_radians = math.radians(other.longitude)

        difference_latitude = latitude_2_radians - latitude_1_radians
        difference_longitude = longitude_2_radians - longitude_1_radians

        haversine_formula_component = (
            math.sin(difference_latitude / 2.0) ** 2
            + math.cos(latitude_1_radians)
            * math.cos(latitude_2_radians)
            * math.sin(difference_longitude / 2.0) ** 2
        )

        angular_distance_radians = 2.0 * math.atan2(
            math.sqrt(haversine_formula_component),
            math.sqrt(1.0 - haversine_formula_component),
        )

        distance_in_kilometers = self.EARTH_RADIUS_KILOMETERS * angular_distance_radians
        return round(distance_in_kilometers, 2)

    def __setattr__(self, key: str, value: Any) -> None:
        raise AttributeError("GeographicCoordinates instances are immutable.")

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, GeographicCoordinates):
            return False
        return (
            math.isclose(self._latitude, other.latitude, abs_tol=1e-6)
            and math.isclose(self._longitude, other.longitude, abs_tol=1e-6)
        )

    def __repr__(self) -> str:
        return f"GeographicCoordinates(latitude={self._latitude}, longitude={self._longitude})"

    def __str__(self) -> str:
        return f"({self._latitude:.6f}, {self._longitude:.6f})"
