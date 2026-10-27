from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping
from src.vacation_planner.core.domain.models.TransportOption import TransportOption
from src.vacation_planner.core.domain.value_objects.MonetaryAmount import MonetaryAmount
from src.vacation_planner.core.domain.value_objects.RouteSegment import RouteSegment
from src.vacation_planner.core.domain.value_objects.TransportType import TransportType


class TrainDataMapper:
    """
    Transforms external railway API / scraper responses (e.g. Deutsche Bahn HAFAS, SNCF,
    or European Rail timetable responses) into strongly-typed Core TransportOption domain models.
    """

    def map_raw_payload_to_transport_option(
        self, raw_train_data: Mapping[str, Any]
    ) -> TransportOption:
        """
        Maps a single raw rail connection dictionary into a TransportOption domain entity.

        Expected raw structure example:
        {
            "connection_id": "ICE-593-20260701",
            "train_operator": "Deutsche Bahn",
            "departure_station_name": "Berlin Hbf",
            "arrival_station_name": "München Hbf",
            "departure_timestamp": "2026-07-01T07:05:00",
            "arrival_timestamp": "2026-07-01T11:15:00",
            "ticket_price_eur": 79.90,
            "train_legs": [
                {
                    "from_station": "Berlin Hbf",
                    "to_station": "Nürnberg Hbf",
                    "departure": "2026-07-01T07:05:00",
                    "arrival": "2026-07-01T09:50:00",
                    "train_category": "ICE",
                    "line_number": "ICE 593"
                },
                {
                    "from_station": "Nürnberg Hbf",
                    "to_station": "München Hbf",
                    "departure": "2026-07-01T10:05:00",
                    "arrival": "2026-07-01T11:15:00",
                    "train_category": "ICE",
                    "line_number": "ICE 701"
                }
            ],
            "eco_carbon_kg": 18.4,
            "booking_link": "https://bahn.example.com/booking/ICE-593"
        }
        """
        # Step 1: Parse overall timetable timestamps
        departure_datetime: datetime = datetime.fromisoformat(
            str(raw_train_data["departure_timestamp"])
        )
        arrival_datetime: datetime = datetime.fromisoformat(
            str(raw_train_data["arrival_timestamp"])
        )

        # Step 2: Transform train sections / transfer connections
        # European railway trips frequently involve transfers at central hubs.
        # Each train leg is converted to an immutable RouteSegment.
        route_segments: list[RouteSegment] = []
        raw_legs = raw_train_data.get("train_legs", [])

        if raw_legs:
            for leg in raw_legs:
                leg_departure = datetime.fromisoformat(str(leg["departure"]))
                leg_arrival = datetime.fromisoformat(str(leg["arrival"]))
                operator_label = str(leg.get("train_category", raw_train_data.get("train_operator", "Rail")))
                line_id = str(leg.get("line_number", f"TRAIN-{operator_label}"))

                route_segments.append(
                    RouteSegment(
                        departure_station_or_airport=str(leg["from_station"]),
                        arrival_station_or_airport=str(leg["to_station"]),
                        departure_time=leg_departure,
                        arrival_time=leg_arrival,
                        carrier_or_operator_name=operator_label,
                        segment_identifier=line_id,
                    )
                )
        else:
            # Direct non-stop rail connection fallback
            route_segments.append(
                RouteSegment(
                    departure_station_or_airport=str(raw_train_data["departure_station_name"]),
                    arrival_station_or_airport=str(raw_train_data["arrival_station_name"]),
                    departure_time=departure_datetime,
                    arrival_time=arrival_datetime,
                    carrier_or_operator_name=str(raw_train_data.get("train_operator", "Rail")),
                    segment_identifier=str(raw_train_data["connection_id"]),
                )
            )

        # Step 3: Parse monetary ticket price
        price_amount = raw_train_data.get("ticket_price_eur", raw_train_data.get("price", 0.0))
        monetary_price = MonetaryAmount(
            amount=price_amount,
            currency=str(raw_train_data.get("currency", "EUR")),
        )

        # Step 4: Extract rail eco carbon profile
        # Trains inherently have significantly lower CO2 footprints than flights
        carbon_kg: float = float(raw_train_data.get("eco_carbon_kg", 20.0))
        booking_url: str = str(raw_train_data.get("booking_link", ""))

        origin_name = str(raw_train_data.get("origin_city_name", raw_train_data["departure_station_name"]))
        destination_name = str(raw_train_data.get("destination_city_name", raw_train_data["arrival_station_name"]))

        return TransportOption(
            transport_option_id=str(raw_train_data["connection_id"]),
            transport_type=TransportType.TRAIN,
            origin_location_name=origin_name,
            destination_location_name=destination_name,
            departure_time=departure_datetime,
            arrival_time=arrival_datetime,
            segments=route_segments,
            total_price=monetary_price,
            carbon_dioxide_emission_in_kilograms=carbon_kg,
            booking_reference_url=booking_url,
        )
