from __future__ import annotations

from typing import Any
from src.vacation_planner.core.domain.models.AccommodationOption import AccommodationOption
from src.vacation_planner.core.domain.models.Location import Location
from src.vacation_planner.core.domain.value_objects.AccommodationType import AccommodationType
from src.vacation_planner.core.domain.value_objects.DateRange import DateRange
from src.vacation_planner.core.interfaces.AccommodationGatewayInterface import (
    AccommodationGatewayInterface,
)
from src.vacation_planner.infrastructure.mappers.HotelAccommodationDataMapper import (
    HotelAccommodationDataMapper,
)


class HotelAccommodationAdapter(AccommodationGatewayInterface):
    """
    Adapter implementing AccommodationGatewayInterface. Queries and parses accommodation
    inventory (hotels, boutique apartments, hostels, resorts) for destinations.
    """

    DESTINATION_HOTEL_CATALOG: dict[str, list[dict[str, Any]]] = {
        "Paris": [
            {
                "property_id": "HTL-PARIS-01",
                "hotel_name": "Hôtel Le Marais Charme",
                "type": "HOTEL",
                "city": "Paris",
                "latitude": 48.8584,
                "longitude": 2.3582,
                "nightly_rate_eur": 165.00,
                "star_rating": 4.5,
                "address": "14 Rue des Rosiers, 75004 Paris",
                "amenity_list": ["High-Speed WiFi", "Continental Breakfast", "Air Conditioning", "Concierge"],
            },
            {
                "property_id": "HTL-PARIS-02",
                "hotel_name": "Eiffel Tower View Studio Apartment",
                "type": "APARTMENT",
                "city": "Paris",
                "latitude": 48.8588,
                "longitude": 2.2943,
                "nightly_rate_eur": 210.00,
                "star_rating": 4.8,
                "address": "22 Avenue de la Bourdonnais, 75007 Paris",
                "amenity_list": ["Kitchenette", "Balcony View", "Washing Machine", "High-Speed WiFi"],
            },
            {
                "property_id": "HTL-PARIS-03",
                "hotel_name": "St. Christopher's Canal Hostel",
                "type": "HOSTEL",
                "city": "Paris",
                "latitude": 48.8912,
                "longitude": 2.3765,
                "nightly_rate_eur": 48.00,
                "star_rating": 3.8,
                "address": "159 Rue de Crimée, 75019 Paris",
                "amenity_list": ["Lockers", "Bar & Lounge", "Shared Kitchen", "Free WiFi"],
            },
        ],
        "Berlin": [
            {
                "property_id": "HTL-BER-01",
                "hotel_name": "Mitte Boutique Grand Hotel",
                "type": "HOTEL",
                "city": "Berlin",
                "latitude": 52.5186,
                "longitude": 13.3888,
                "nightly_rate_eur": 135.00,
                "star_rating": 4.4,
                "address": "Friedrichstraße 150, 10117 Berlin",
                "amenity_list": ["Sauna", "Fitness Center", "Breakfast Buffet", "Free High-Speed WiFi"],
            },
            {
                "property_id": "HTL-BER-02",
                "hotel_name": "Prenzlauer Berg Urban Loft",
                "type": "APARTMENT",
                "city": "Berlin",
                "latitude": 52.5373,
                "longitude": 13.4140,
                "nightly_rate_eur": 120.00,
                "star_rating": 4.7,
                "address": "Kastanienallee 24, 10435 Berlin",
                "amenity_list": ["Designer Kitchen", "Balcony", "Espresso Machine", "Fast WiFi"],
            },
            {
                "property_id": "HTL-BER-03",
                "hotel_name": "Generator Alexanderplatz Hostel",
                "type": "HOSTEL",
                "city": "Berlin",
                "latitude": 52.5235,
                "longitude": 13.4115,
                "nightly_rate_eur": 42.00,
                "star_rating": 3.9,
                "address": "Otto-Braun-Straße 65, 10178 Berlin",
                "amenity_list": ["Bar", "Bicycle Rental", "Luggage Storage", "24h Reception"],
            },
        ],
        "Rome": [
            {
                "property_id": "HTL-ROME-01",
                "hotel_name": "Hotel Navona Antica",
                "type": "HOTEL",
                "city": "Rome",
                "latitude": 41.8992,
                "longitude": 12.4731,
                "nightly_rate_eur": 155.00,
                "star_rating": 4.6,
                "address": "Via dei Canestrari 78, 00186 Roma",
                "amenity_list": ["Rooftop Terrace", "Italian Breakfast", "Air Conditioning", "WiFi"],
            },
            {
                "property_id": "HTL-ROME-02",
                "hotel_name": "Colosseum Historic Residence",
                "type": "APARTMENT",
                "city": "Rome",
                "latitude": 41.8902,
                "longitude": 12.4922,
                "nightly_rate_eur": 175.00,
                "star_rating": 4.7,
                "address": "Via Labicana 42, 00184 Roma",
                "amenity_list": ["Full Kitchen", "Terrace with View", "Air Conditioning", "WiFi"],
            },
        ],
        "Barcelona": [
            {
                "property_id": "HTL-BCN-01",
                "hotel_name": "Hotel Arts Coastal Resort",
                "type": "RESORT",
                "city": "Barcelona",
                "latitude": 41.3888,
                "longitude": 2.1969,
                "nightly_rate_eur": 240.00,
                "star_rating": 4.9,
                "address": "Carrer de Marina 19, 08005 Barcelona",
                "amenity_list": ["Infinity Pool", "Direct Beach Access", "Spa & Wellness", "Michelin Dining"],
            },
            {
                "property_id": "HTL-BCN-02",
                "hotel_name": "Eixample Modernist Hotel",
                "type": "HOTEL",
                "city": "Barcelona",
                "latitude": 41.3923,
                "longitude": 2.1648,
                "nightly_rate_eur": 145.00,
                "star_rating": 4.3,
                "address": "Carrer de Mallorca 250, 08008 Barcelona",
                "amenity_list": ["Rooftop Bar", "Swimming Pool", "Breakfast", "Free WiFi"],
            },
        ],
        "Vienna": [
            {
                "property_id": "HTL-VIE-01",
                "hotel_name": "Hotel Sacher Wien",
                "type": "HOTEL",
                "city": "Vienna",
                "latitude": 48.2045,
                "longitude": 16.3695,
                "nightly_rate_eur": 260.00,
                "star_rating": 5.0,
                "address": "Philharmoniker Str. 4, 1010 Wien",
                "amenity_list": ["Original Sacher-Torte", "Luxury Spa", "Concierge", "Fine Dining"],
            },
            {
                "property_id": "HTL-VIE-02",
                "hotel_name": "Leopoldstadt Art Apartment",
                "type": "APARTMENT",
                "city": "Vienna",
                "latitude": 48.2167,
                "longitude": 16.3833,
                "nightly_rate_eur": 115.00,
                "star_rating": 4.5,
                "address": "Taborstraße 35, 1020 Wien",
                "amenity_list": ["Balcony", "Kitchen", "Nespresso Machine", "High-Speed WiFi"],
            },
        ],
    }

    def __init__(self, mapper: HotelAccommodationDataMapper | None = None) -> None:
        self._mapper: HotelAccommodationDataMapper = mapper or HotelAccommodationDataMapper()

    def search_accommodation_options(
        self,
        destination_location: Location,
        date_range: DateRange,
        number_of_guests: int,
        preferred_accommodation_type: AccommodationType | None = None,
    ) -> list[AccommodationOption]:
        """
        Retrieves matching accommodation options for the specified destination and dates.
        """
        raw_catalog = self.DESTINATION_HOTEL_CATALOG.get(destination_location.name)

        if not raw_catalog:
            # Fallback generator for locations not in static dictionary
            raw_catalog = [
                {
                    "property_id": f"HTL-{destination_location.name.upper()}-01",
                    "hotel_name": f"Grand Central Hotel {destination_location.name}",
                    "type": "HOTEL",
                    "city": destination_location.name,
                    "latitude": destination_location.coordinates.latitude + 0.005,
                    "longitude": destination_location.coordinates.longitude + 0.005,
                    "nightly_rate_eur": 130.00,
                    "star_rating": 4.2,
                    "address": f"Main Avenue 1, {destination_location.name}",
                    "amenity_list": ["Free WiFi", "Breakfast", "Air Conditioning"],
                },
                {
                    "property_id": f"APT-{destination_location.name.upper()}-01",
                    "hotel_name": f"{destination_location.name} Panorama City Apartment",
                    "type": "APARTMENT",
                    "city": destination_location.name,
                    "latitude": destination_location.coordinates.latitude - 0.004,
                    "longitude": destination_location.coordinates.longitude - 0.003,
                    "nightly_rate_eur": 110.00,
                    "star_rating": 4.5,
                    "address": f"Old Town Square 12, {destination_location.name}",
                    "amenity_list": ["Full Kitchen", "City View", "Free WiFi"],
                },
            ]

        results: list[AccommodationOption] = []
        for raw_entry in raw_catalog:
            option = self._mapper.map_raw_payload_to_accommodation_option(
                raw_data=raw_entry,
                date_range=date_range,
            )

            # Filter by preferred accommodation type if specified
            if (
                preferred_accommodation_type is not None
                and option.accommodation_type != preferred_accommodation_type
            ):
                continue

            results.append(option)

        return results

