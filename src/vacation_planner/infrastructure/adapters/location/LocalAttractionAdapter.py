from __future__ import annotations

from typing import Any
from src.vacation_planner.core.domain.models.Attraction import Attraction
from src.vacation_planner.core.domain.models.Location import Location
from src.vacation_planner.infrastructure.mappers.AttractionDataMapper import AttractionDataMapper


class LocalAttractionAdapter:
    """
    Adapter querying points of interest, tourist landmarks, and cultural venues for destinations.
    Uses AttractionDataMapper to convert raw data structures into domain Attraction entities.
    """

    DESTINATION_ATTRACTIONS_CATALOG: dict[str, list[dict[str, Any]]] = {
        "Paris": [
            {
                "attraction_id": "ATTR-PAR-01",
                "name": "Eiffel Tower (Tour Eiffel)",
                "city": "Paris",
                "category": "HISTORICAL_MONUMENT",
                "latitude": 48.8584,
                "longitude": 2.2945,
                "admission_fee_eur": 29.40,
                "duration_minutes": 150,
                "rating": 4.7,
                "description": "Iconic wrought-iron lattice tower on the Champ de Mars, symbol of Paris.",
            },
            {
                "attraction_id": "ATTR-PAR-02",
                "name": "Louvre Museum (Musée du Louvre)",
                "city": "Paris",
                "category": "MUSEUM",
                "latitude": 48.8606,
                "longitude": 2.3376,
                "admission_fee_eur": 22.00,
                "duration_minutes": 240,
                "rating": 4.8,
                "description": "World's most-visited museum and historic monument home to the Mona Lisa.",
            },
            {
                "attraction_id": "ATTR-PAR-03",
                "name": "Cathedrale Notre-Dame de Paris",
                "city": "Paris",
                "category": "ARCHITECTURE",
                "latitude": 48.8530,
                "longitude": 2.3499,
                "admission_fee_eur": 0.00,
                "duration_minutes": 90,
                "rating": 4.9,
                "description": "Masterpiece of French Gothic architecture on the Île de la Cité.",
            },
        ],
        "Berlin": [
            {
                "attraction_id": "ATTR-BER-01",
                "name": "Brandenburg Gate (Brandenburger Tor)",
                "city": "Berlin",
                "category": "HISTORICAL_MONUMENT",
                "latitude": 52.5163,
                "longitude": 13.3777,
                "admission_fee_eur": 0.00,
                "duration_minutes": 45,
                "rating": 4.7,
                "description": "18th-century neoclassical monument and national symbol of German unity.",
            },
            {
                "attraction_id": "ATTR-BER-02",
                "name": "Museum Island (Museumsinsel)",
                "city": "Berlin",
                "category": "MUSEUM",
                "latitude": 52.5209,
                "longitude": 13.3986,
                "admission_fee_eur": 19.00,
                "duration_minutes": 180,
                "rating": 4.8,
                "description": "UNESCO World Heritage site complex of five world-class museums in central Berlin.",
            },
            {
                "attraction_id": "ATTR-BER-03",
                "name": "Reichstag Building & Glass Dome",
                "city": "Berlin",
                "category": "ARCHITECTURE",
                "latitude": 52.5186,
                "longitude": 13.3761,
                "admission_fee_eur": 0.00,
                "duration_minutes": 90,
                "rating": 4.6,
                "description": "Historic parliament building featuring a modern glass dome with 360-degree city views.",
            },
        ],
        "Rome": [
            {
                "attraction_id": "ATTR-ROM-01",
                "name": "The Colosseum (Colosseo)",
                "city": "Rome",
                "category": "HISTORICAL_MONUMENT",
                "latitude": 41.8902,
                "longitude": 12.4922,
                "admission_fee_eur": 18.00,
                "duration_minutes": 150,
                "rating": 4.8,
                "description": "Largest ancient amphitheatre ever built, hosting gladiatorial contests in Imperial Rome.",
            },
            {
                "attraction_id": "ATTR-ROM-02",
                "name": "Vatican Museums & Sistine Chapel",
                "city": "Rome",
                "category": "MUSEUM",
                "latitude": 41.9065,
                "longitude": 12.4536,
                "admission_fee_eur": 25.00,
                "duration_minutes": 210,
                "rating": 4.9,
                "description": "Immense collection of classical sculptures and Renaissance masterpieces by Michelangelo.",
            },
        ],
        "Barcelona": [
            {
                "attraction_id": "ATTR-BCN-01",
                "name": "Basílica de la Sagrada Família",
                "city": "Barcelona",
                "category": "ARCHITECTURE",
                "latitude": 41.4036,
                "longitude": 2.1744,
                "admission_fee_eur": 26.00,
                "duration_minutes": 120,
                "rating": 4.9,
                "description": "Antoni Gaudí's unfinished monumental basilica and UNESCO World Heritage landmark.",
            },
            {
                "attraction_id": "ATTR-BCN-02",
                "name": "Park Güell",
                "city": "Barcelona",
                "category": "NATURAL_PARK",
                "latitude": 41.4145,
                "longitude": 2.1527,
                "admission_fee_eur": 10.00,
                "duration_minutes": 90,
                "rating": 4.6,
                "description": "Whimsical public park system of gardens and architectural elements designed by Antoni Gaudí.",
            },
        ],
        "Vienna": [
            {
                "attraction_id": "ATTR-VIE-01",
                "name": "Schönbrunn Palace & Gardens",
                "city": "Vienna",
                "category": "HISTORICAL_MONUMENT",
                "latitude": 48.1858,
                "longitude": 16.3128,
                "admission_fee_eur": 24.00,
                "duration_minutes": 180,
                "rating": 4.8,
                "description": "Former imperial summer residence of the Habsburg monarchs with vast baroque gardens.",
            },
            {
                "attraction_id": "ATTR-VIE-02",
                "name": "St. Stephen's Cathedral (Stephansdom)",
                "city": "Vienna",
                "category": "ARCHITECTURE",
                "latitude": 48.2085,
                "longitude": 16.3731,
                "admission_fee_eur": 6.50,
                "duration_minutes": 60,
                "rating": 4.7,
                "description": "Gothic and Romanesque mother church of the Roman Catholic Archdiocese of Vienna.",
            },
        ],
    }

    def __init__(self, mapper: AttractionDataMapper | None = None) -> None:
        self._mapper: AttractionDataMapper = mapper or AttractionDataMapper()

    def fetch_attractions(
        self, destination_location: Location, maximum_results: int = 10
    ) -> list[Attraction]:
        """
        Retrieves points of interest for the destination.
        """
        raw_items = self.DESTINATION_ATTRACTIONS_CATALOG.get(destination_location.name, [])

        if not raw_items:
            # Fallback sight generator for unlisted cities
            raw_items = [
                {
                    "attraction_id": f"ATTR-{destination_location.name.upper()}-01",
                    "name": f"Historic Old Town Center of {destination_location.name}",
                    "city": destination_location.name,
                    "category": "HISTORICAL_MONUMENT",
                    "latitude": destination_location.coordinates.latitude,
                    "longitude": destination_location.coordinates.longitude,
                    "admission_fee_eur": 0.00,
                    "duration_minutes": 90,
                    "rating": 4.5,
                    "description": f"Charming historic center of {destination_location.name}.",
                }
            ]

        results: list[Attraction] = []
        for raw_item in raw_items[:maximum_results]:
            attraction = self._mapper.map_raw_payload_to_attraction(raw_item)
            results.append(attraction)

        return results
