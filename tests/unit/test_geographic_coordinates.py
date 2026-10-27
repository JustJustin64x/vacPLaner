import unittest
from src.vacation_planner.core.domain.value_objects.GeographicCoordinates import (
    GeographicCoordinates,
)


class TestGeographicCoordinates(unittest.TestCase):
    def test_valid_coordinates_creation(self) -> None:
        coordinates = GeographicCoordinates(latitude=52.5200, longitude=13.4050)
        self.assertAlmostEqual(coordinates.latitude, 52.5200)
        self.assertAlmostEqual(coordinates.longitude, 13.4050)

    def test_invalid_latitude_raises_error(self) -> None:
        with self.assertRaises(ValueError):
            GeographicCoordinates(latitude=91.0, longitude=10.0)
        with self.assertRaises(ValueError):
            GeographicCoordinates(latitude=-90.5, longitude=10.0)

    def test_invalid_longitude_raises_error(self) -> None:
        with self.assertRaises(ValueError):
            GeographicCoordinates(latitude=45.0, longitude=180.5)
        with self.assertRaises(ValueError):
            GeographicCoordinates(latitude=45.0, longitude=-181.0)

    def test_haversine_distance_calculation_berlin_to_paris(self) -> None:
        # Berlin coordinates: 52.5200 N, 13.4050 E
        berlin = GeographicCoordinates(latitude=52.5200, longitude=13.4050)
        # Paris coordinates: 48.8566 N, 2.3522 E
        paris = GeographicCoordinates(latitude=48.8566, longitude=2.3522)

        distance_km = berlin.calculate_distance_in_kilometers_to(paris)
        # True great-circle distance between Berlin and Paris is approximately 878 km
        self.assertGreater(distance_km, 870.0)
        self.assertLess(distance_km, 890.0)

    def test_immutability(self) -> None:
        coords = GeographicCoordinates(latitude=10.0, longitude=20.0)
        with self.assertRaises(AttributeError):
            coords.latitude = 15.0  # type: ignore


if __name__ == "__main__":
    unittest.main()
