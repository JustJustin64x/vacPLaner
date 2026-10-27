from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Mapping
from src.vacation_planner.core.domain.models.TransportOption import TransportOption
from src.vacation_planner.core.domain.value_objects.MonetaryAmount import MonetaryAmount
from src.vacation_planner.core.domain.value_objects.RouteSegment import RouteSegment
from src.vacation_planner.core.domain.value_objects.TransportType import TransportType


class CarRouteDataMapper:
    """
    Transforms road routing engine outputs (e.g. OSRM, GraphHopper, OpenRouteService,
    or Google Maps Directions API JSON payloads) into Core domain TransportOption entities.
    Computes realistic driving segments, fuel cost estimates, and highway tolls.
    """

    def map_raw_payload_to_transport_option(
        self, raw_route_data: Mapping[str, Any]
    ) -> TransportOption:
        """
        Maps a routing engine response into a TransportOption domain entity.

        Expected raw structure example:
        {
            "route_id": "CAR-BER-PARIS-20260701",
            "departure_location": "Berlin",
            "destination_location": "Paris",
            "start_time_iso": "2026-07-01T06:00:00",
            "distance_in_kilometers": 1050.4,
            "duration_in_minutes": 630,
            "estimated_fuel_cost_eur": 145.20,
            "estimated_toll_cost_eur": 38.50,
            "car_model_or_category": "Standard Gasoline / Electric Mix",
            "highway_segments": [
                {
                    "from_waypoint": "Berlin",
                    "to_waypoint": "Köln",
                    "highway_name": "A2 / A1",
                    "distance_km": 575.0,
                    "estimated_minutes": 330
                },
                {
                    "from_waypoint": "Köln",
                    "to_waypoint": "Paris",
                    "highway_name": "A4",
                    "distance_km": 475.4,
                    "estimated_minutes": 300
                }
            ]
        }
        """
        # Step 1: Compute continuous departure and arrival dates
        departure_datetime: datetime = datetime.fromisoformat(
            str(raw_route_data["start_time_iso"])
        )
        total_duration_minutes: int = int(raw_route_data["duration_in_minutes"])
        arrival_datetime: datetime = departure_datetime + timedelta(minutes=total_duration_minutes)

        # Step 2: Build RouteSegments from highway waypoints
        # Highway segments trace the exact route across national borders or motorways.
        route_segments: list[RouteSegment] = []
        raw_highway_segments = raw_route_data.get("highway_segments", [])

        if raw_highway_segments:
            current_segment_departure = departure_datetime
            for segment_data in raw_highway_segments:
                segment_duration = int(segment_data["estimated_minutes"])
                current_segment_arrival = current_segment_departure + timedelta(
                    minutes=segment_duration
                )

                route_segments.append(
                    RouteSegment(
                        departure_station_or_airport=str(segment_data["from_waypoint"]),
                        arrival_station_or_airport=str(segment_data["to_waypoint"]),
                        departure_time=current_segment_departure,
                        arrival_time=current_segment_arrival,
                        carrier_or_operator_name=str(
                            raw_route_data.get("car_model_or_category", "Personal Automobile")
                        ),
                        segment_identifier=str(segment_data["highway_name"]),
                    )
                )
                current_segment_departure = current_segment_arrival
        else:
            # Single aggregated car route segment fallback
            route_segments.append(
                RouteSegment(
                    departure_station_or_airport=str(raw_route_data["departure_location"]),
                    arrival_station_or_airport=str(raw_route_data["destination_location"]),
                    departure_time=departure_datetime,
                    arrival_time=arrival_datetime,
                    carrier_or_operator_name=str(
                        raw_route_data.get("car_model_or_category", "Personal Automobile")
                    ),
                    segment_identifier="DIRECT-ROAD-ROUTE",
                )
            )

        # Step 3: Compute total driving expenses (fuel + motorway tolls)
        fuel_cost = float(raw_route_data.get("estimated_fuel_cost_eur", 0.0))
        toll_cost = float(raw_route_data.get("estimated_toll_cost_eur", 0.0))
        total_car_cost = fuel_cost + toll_cost

        monetary_price = MonetaryAmount(
            amount=total_car_cost,
            currency="EUR",
        )

        # Step 4: Calculate realistic CO2 emissions for passenger vehicles
        # Average modern European automobile emits approximately 120g CO2 per km.
        distance_km: float = float(raw_route_data.get("distance_in_kilometers", 0.0))
        calculated_co2_kg: float = round(distance_km * 0.120, 2)

        return TransportOption(
            transport_option_id=str(raw_route_data["route_id"]),
            transport_type=TransportType.CAR,
            origin_location_name=str(raw_route_data["departure_location"]),
            destination_location_name=str(raw_route_data["destination_location"]),
            departure_time=departure_datetime,
            arrival_time=arrival_datetime,
            segments=route_segments,
            total_price=monetary_price,
            carbon_dioxide_emission_in_kilograms=calculated_co2_kg,
            booking_reference_url="https://maps.example.com/route",
        )

