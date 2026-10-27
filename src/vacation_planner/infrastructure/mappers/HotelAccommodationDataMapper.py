from __future__ import annotations

from typing import Any, Mapping
from src.vacation_planner.core.domain.models.AccommodationOption import AccommodationOption
from src.vacation_planner.core.domain.value_objects.AccommodationType import AccommodationType
from src.vacation_planner.core.domain.value_objects.DateRange import DateRange
from src.vacation_planner.core.domain.value_objects.GeographicCoordinates import (
    GeographicCoordinates,
)
from src.vacation_planner.core.domain.value_objects.MonetaryAmount import MonetaryAmount


class HotelAccommodationDataMapper:
    """
    Transforms external accommodation provider payloads (e.g. Booking.com, Airbnb, Expedia,
    or scraped lodging data structures) into Core domain AccommodationOption entities.
    Handles price per night vs total stay calculations and amenities filtering.
    """

    def map_raw_payload_to_accommodation_option(
        self, raw_data: Mapping[str, Any], date_range: DateRange
    ) -> AccommodationOption:
        """
        Maps a single hotel/lodging dictionary into an AccommodationOption domain entity.

        Expected raw structure example:
        {
            "property_id": "HOTEL-PARIS-001",
            "hotel_name": "Grand Hotel Saint-Michel",
            "type": "HOTEL",
            "city": "Paris",
            "latitude": 48.8471,
            "longitude": 2.3421,
            "nightly_rate_eur": 140.00,
            "star_rating": 4.5,
            "address": "19 Rue Cujas, 75005 Paris",
            "amenity_list": ["Free WiFi", "Breakfast included", "Air Conditioning", "Elevator"]
        }
        """
        # Step 1: Normalize accommodation category to AccommodationType Enum
        raw_type_string = str(raw_data.get("type", "HOTEL")).upper().strip()
        try:
            accommodation_type = AccommodationType(raw_type_string)
        except ValueError:
            accommodation_type = AccommodationType.HOTEL

        # Step 2: Validate and build GeographicCoordinates
        coordinates = GeographicCoordinates(
            latitude=float(raw_data["latitude"]),
            longitude=float(raw_data["longitude"]),
        )

        # Step 3: Compute total price based on date range duration
        # The external API may supply only nightly rates or a fixed total.
        # We ensure accurate financial calculations based on actual nights stayed.
        nights = date_range.calculate_total_nights()
        nightly_rate_val = raw_data.get("nightly_rate_eur") or raw_data.get("price_per_night", 100.0)
        nightly_amount = MonetaryAmount(nightly_rate_val, "EUR")

        if "total_stay_price_eur" in raw_data:
            total_amount = MonetaryAmount(raw_data["total_stay_price_eur"], "EUR")
        else:
            # Multiply nightly rate by the number of nights (minimum 1 night)
            multiplier = max(1, nights)
            total_amount = nightly_amount.multiply(multiplier)

        # Step 4: Extract and clean amenities
        raw_amenities = raw_data.get("amenity_list") or raw_data.get("amenities", [])
        clean_amenities: list[str] = [str(item).strip() for item in raw_amenities if str(item).strip()]

        # Step 5: Construct domain model
        return AccommodationOption(
            accommodation_id=str(raw_data["property_id"]),
            name=str(raw_data["hotel_name"]),
            accommodation_type=accommodation_type,
            location_name=str(raw_data["city"]),
            coordinates=coordinates,
            date_range=date_range,
            total_price=total_amount,
            price_per_night=nightly_amount,
            star_rating=float(raw_data.get("star_rating", 3.0)),
            address_line=str(raw_data.get("address", "")),
            included_amenities=clean_amenities,
        )

