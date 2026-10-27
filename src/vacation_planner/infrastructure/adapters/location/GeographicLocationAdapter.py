from __future__ import annotations

from typing import Any
from src.vacation_planner.core.domain.models.Location import Location
from src.vacation_planner.infrastructure.mappers.GeographicLocationDataMapper import (
    GeographicLocationDataMapper,
)


class GeographicLocationAdapter:
    """
    Adapter responsible for geocoding and location resolution.
    Transforms raw geographic data into validated Location domain models using GeographicLocationDataMapper.
    """

    KNOWN_LOCATIONS_DATABASE: dict[str, dict[str, Any]] = {
        "berlin": {
            "place_id": "LOC-DE-BER",
            "city_name": "Berlin",
            "country": "Germany",
            "country_code": "DE",
            "lat": 52.520008,
            "lon": 13.404954,
            "summary": "Capital of Germany known for its vibrant arts scene and modern history.",
        },
        "paris": {
            "place_id": "LOC-FR-PAR",
            "city_name": "Paris",
            "country": "France",
            "country_code": "FR",
            "lat": 48.856614,
            "lon": 2.352222,
            "summary": "France's capital, a major European city and global center for art, fashion, gastronomy, and culture.",
        },
        "rome": {
            "place_id": "LOC-IT-ROM",
            "city_name": "Rome",
            "country": "Italy",
            "country_code": "IT",
            "lat": 41.902782,
            "lon": 12.496366,
            "summary": "The Eternal City, capital of Italy with nearly 3,000 years of globally influential art and architecture.",
        },
        "barcelona": {
            "place_id": "LOC-ES-BCN",
            "city_name": "Barcelona",
            "country": "Spain",
            "country_code": "ES",
            "lat": 41.385064,
            "lon": 2.173404,
            "summary": "Cosmopolitan capital of Spain’s Catalonia region, known for its art and architecture.",
        },
        "vienna": {
            "place_id": "LOC-AT-VIE",
            "city_name": "Vienna",
            "country": "Austria",
            "country_code": "AT",
            "lat": 48.208174,
            "lon": 16.373819,
            "summary": "Austria's capital lying on the Danube River, known for its imperial palaces and musical heritage.",
        },
        "amsterdam": {
            "place_id": "LOC-NL-AMS",
            "city_name": "Amsterdam",
            "country": "Netherlands",
            "country_code": "NL",
            "lat": 52.367573,
            "lon": 4.904139,
            "summary": "Capital of the Netherlands known for its artistic heritage, elaborate canal system and cycling culture.",
        },
        "zurich": {
            "place_id": "LOC-CH-ZRH",
            "city_name": "Zurich",
            "country": "Switzerland",
            "country_code": "CH",
            "lat": 47.376887,
            "lon": 8.541694,
            "summary": "City in north-central Switzerland, located at the northwestern tip of Lake Zurich.",
        },
        "london": {
            "place_id": "LOC-GB-LON",
            "city_name": "London",
            "country": "United Kingdom",
            "country_code": "GB",
            "lat": 51.507351,
            "lon": -0.127758,
            "summary": "Capital and largest city of England and the United Kingdom.",
        },
        "munich": {
            "place_id": "LOC-DE-MUC",
            "city_name": "Munich",
            "country": "Germany",
            "country_code": "DE",
            "lat": 48.135125,
            "lon": 11.581981,
            "summary": "Bavaria's capital, home to centuries-old buildings and numerous museums.",
        },
    }

    def __init__(self, mapper: GeographicLocationDataMapper | None = None) -> None:
        self._mapper: GeographicLocationDataMapper = mapper or GeographicLocationDataMapper()

    def resolve_location(self, location_name: str) -> Location:
        """
        Resolves a textual location name into a validated Location entity.
        Raises ValueError if the location is unrecognized.
        """
        key = location_name.strip().lower()
        if key not in self.KNOWN_LOCATIONS_DATABASE:
            raise ValueError(
                f"Location '{location_name}' could not be resolved. "
                f"Supported cities include: {', '.join(sorted([k.title() for k in self.KNOWN_LOCATIONS_DATABASE.keys()]))}."
            )

        raw_entry = self.KNOWN_LOCATIONS_DATABASE[key]
        return self._mapper.map_raw_payload_to_location(raw_entry)
