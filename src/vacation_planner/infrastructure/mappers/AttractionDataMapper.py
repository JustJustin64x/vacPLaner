from __future__ import annotations

from typing import Any, Mapping
from src.vacation_planner.core.domain.models.Attraction import Attraction
from src.vacation_planner.core.domain.value_objects.GeographicCoordinates import (
    GeographicCoordinates,
)
from src.vacation_planner.core.domain.value_objects.MonetaryAmount import MonetaryAmount


class AttractionDataMapper:
    """
    Transforms external point-of-interest (POI) payloads (e.g. OpenTripMap, Overpass API,
    or tourist board JSON endpoints) into Core domain Attraction entities.
    """

    def map_raw_payload_to_attraction(
        self, raw_attraction_data: Mapping[str, Any]
    ) -> Attraction:
        """
        Maps a single raw tourist attraction dictionary into an Attraction domain entity.

        Expected raw structure example:
        {
            "attraction_id": "ATTR-PARIS-LOUVRE",
            "name": "Louvre Museum",
            "city": "Paris",
            "category": "MUSEUM",
            "latitude": 48.8606,
            "longitude": 2.3376,
            "admission_fee_eur": 22.00,
            "duration_minutes": 180,
            "rating": 4.8,
            "description": "World-renowned museum housing the Mona Lisa and historic masterpieces."
        }
        """
        # Step 1: Map coordinates
        coordinates = GeographicCoordinates(
            latitude=float(raw_attraction_data["latitude"]),
            longitude=float(raw_attraction_data["longitude"]),
        )

        # Step 2: Parse admission fee (handles free attractions gracefully)
        fee_value = raw_attraction_data.get("admission_fee_eur", 0.0)
        fee_currency = str(raw_attraction_data.get("currency", "EUR"))
        admission_fee = MonetaryAmount(amount=fee_value, currency=fee_currency)

        # Step 3: Duration and user ratings
        duration_minutes = int(raw_attraction_data.get("duration_minutes", 60))
        rating_value = float(raw_attraction_data.get("rating", 4.0))

        return Attraction(
            attraction_id=str(raw_attraction_data["attraction_id"]),
            name=str(raw_attraction_data["name"]),
            location_name=str(raw_attraction_data.get("city", "")),
            category=str(raw_attraction_data.get("category", "SIGHT")),
            coordinates=coordinates,
            admission_fee=admission_fee,
            estimated_visit_duration_in_minutes=duration_minutes,
            user_rating=rating_value,
            description=str(raw_attraction_data.get("description", "")),
        )
