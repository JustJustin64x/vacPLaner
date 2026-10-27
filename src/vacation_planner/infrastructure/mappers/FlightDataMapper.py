from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping
from src.vacation_planner.core.domain.models.TransportOption import TransportOption
from src.vacation_planner.core.domain.value_objects.MonetaryAmount import MonetaryAmount
from src.vacation_planner.core.domain.value_objects.RouteSegment import RouteSegment
from src.vacation_planner.core.domain.value_objects.TransportType import TransportType


class FlightDataMapper:
    """
    Transforms external airline or flight aggregator API raw payloads (e.g. Amadeus, Skyscanner,
    or GDS JSON representations) into strongly-typed Core domain TransportOption entities.
    """

    def map_raw_payload_to_transport_option(
        self, raw_flight_data: Mapping[str, Any]
    ) -> TransportOption:
        """
        Maps a single raw flight dictionary to a TransportOption domain entity.

        Expected raw structure example:
        {
            "flight_id": "LH-2034-20260701",
            "airline_name": "Lufthansa",
            "departure_airport_code": "BER",
            "arrival_airport_code": "CDG",
            "origin_city_name": "Berlin",
            "destination_city_name": "Paris",
            "scheduled_departure_iso": "2026-07-01T08:30:00",
            "scheduled_arrival_iso": "2026-07-01T10:15:00",
            "fare_amount": 149.50,
            "currency_code": "EUR",
            "estimated_co2_kg": 112.5,
            "booking_deep_link": "https://flights.example.com/book/LH-2034",
            "flight_legs": [
                {
                    "origin_airport": "BER",
                    "destination_airport": "CDG",
                    "departure_time": "2026-07-01T08:30:00",
                    "arrival_time": "2026-07-01T10:15:00",
                    "operating_carrier": "Lufthansa",
                    "flight_number": "LH2034"
                }
            ]
        }
        """
        # Step 1: Parse and validate ISO-8601 timestamps
        # Flight API timestamps often contain timezone offsets or standard ISO strings.
        departure_datetime: datetime = datetime.fromisoformat(
            str(raw_flight_data["scheduled_departure_iso"])
        )
        arrival_datetime: datetime = datetime.fromisoformat(
            str(raw_flight_data["scheduled_arrival_iso"])
        )

        # Step 2: Transform individual flight legs / sub-segments
        # Many commercial flights consist of multi-leg itineraries (e.g., layovers in FRA or MUC).
        # We iterate over every leg to preserve exact flight numbers and transfer points.
        constructed_route_segments: list[RouteSegment] = []
        raw_legs = raw_flight_data.get("flight_legs", [])

        if raw_legs:
            for leg_entry in raw_legs:
                leg_departure: datetime = datetime.fromisoformat(str(leg_entry["departure_time"]))
                leg_arrival: datetime = datetime.fromisoformat(str(leg_entry["arrival_time"]))

                segment = RouteSegment(
                    departure_station_or_airport=str(leg_entry["origin_airport"]),
                    arrival_station_or_airport=str(leg_entry["destination_airport"]),
                    departure_time=leg_departure,
                    arrival_time=leg_arrival,
                    carrier_or_operator_name=str(leg_entry["operating_carrier"]),
                    segment_identifier=str(leg_entry["flight_number"]),
                )
                constructed_route_segments.append(segment)
        else:
            # Fallback for direct single-leg flights if no nested 'flight_legs' array is supplied
            single_segment = RouteSegment(
                departure_station_or_airport=str(raw_flight_data["departure_airport_code"]),
                arrival_station_or_airport=str(raw_flight_data["arrival_airport_code"]),
                departure_time=departure_datetime,
                arrival_time=arrival_datetime,
                carrier_or_operator_name=str(raw_flight_data["airline_name"]),
                segment_identifier=str(raw_flight_data["flight_id"]),
            )
            constructed_route_segments.append(single_segment)

        # Step 3: Construct precise MonetaryAmount to avoid currency floating-point errors
        monetary_price = MonetaryAmount(
            amount=raw_flight_data["fare_amount"],
            currency=str(raw_flight_data.get("currency_code", "EUR")),
        )

        # Step 4: Extract CO2 emissions and deep-link information
        co2_emission_value: float = float(raw_flight_data.get("estimated_co2_kg", 120.0))
        booking_url: str = str(raw_flight_data.get("booking_deep_link", ""))

        # Step 5: Instantiate and return clean domain entity
        return TransportOption(
            transport_option_id=str(raw_flight_data["flight_id"]),
            transport_type=TransportType.FLIGHT,
            origin_location_name=str(raw_flight_data["origin_city_name"]),
            destination_location_name=str(raw_flight_data["destination_city_name"]),
            departure_time=departure_datetime,
            arrival_time=arrival_datetime,
            segments=constructed_route_segments,
            total_price=monetary_price,
            carbon_dioxide_emission_in_kilograms=co2_emission_value,
            booking_reference_url=booking_url,
        )

