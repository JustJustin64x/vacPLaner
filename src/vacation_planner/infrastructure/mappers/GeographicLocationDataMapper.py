from __future__ import annotations

from typing import Any, Mapping
from src.vacation_planner.core.domain.models.Location import Location
from src.vacation_planner.core.domain.value_objects.GeographicCoordinates import (
    GeographicCoordinates,
)


class GeographicLocationDataMapper:
    """
    Transforms external geocoding payloads (such as OpenStreetMap Nominatim, GeoNames,
    or Google Geocoding JSON structures) into Core domain Location entities.
    """

    def map_raw_payload_to_location(
        self, raw_geocoding_entry: Mapping[str, Any]
    ) -> Location:
        """
        Maps a geocoding result dictionary into a Location domain entity.

        Expected raw structure example:
        {
            "place_id": "LOC-BER-DE",
            "city_name": "Berlin",
            "country": "Germany",
            "country_code": "DE",
            "lat": 52.520008,
            "lon": 13.404954,
            "summary": "Capital and largest city of Germany."
        }
        """
        # Step 1: Extract coordinates with floating point validation
        latitude_val = float(raw_geocoding_entry.get("lat") or raw_geocoding_entry["latitude"])
        longitude_val = float(raw_geocoding_entry.get("lon") or raw_geocoding_entry["longitude"])

        coordinates = GeographicCoordinates(
            latitude=latitude_val,
            longitude=longitude_val,
        )

        # Step 2: Extract normalized identifiers and country codes
        location_id = str(raw_geocoding_entry.get("place_id", f"LOC-{raw_geocoding_entry['city_name'].upper()}"))
        city_name = str(raw_geocoding_entry.get("city_name") or raw_geocoding_entry.get("name", ""))
        country_name = str(raw_geocoding_entry.get("country", "Unknown Country"))
        country_code = str(raw_geocoding_entry.get("country_code", "XX")).upper()
        description = str(raw_geocoding_entry.get("summary") or raw_geocoding_entry.get("description", ""))

        return Location(
            location_id=location_id,
            name=city_name,
            country_name=country_name,
            country_code=country_code,
            coordinates=coordinates,
            description=description,
        )

