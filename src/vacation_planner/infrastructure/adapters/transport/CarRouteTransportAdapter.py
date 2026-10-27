from __future__ import annotations

from datetime import date, datetime, time
from typing import Any
from src.vacation_planner.core.domain.models.Location import Location
from src.vacation_planner.core.domain.models.TransportOption import TransportOption
from src.vacation_planner.infrastructure.mappers.CarRouteDataMapper import CarRouteDataMapper


class CarRouteTransportAdapter:
    """
    Adapter responsible for calculating automobile driving routes between origin and destination.
    Uses road geometry, realistic motorway detour factors (approx 1.25x spherical distance),
    average motorway speeds (105 km/h), fuel consumption and road tolls. Uses CarRouteDataMapper.
    """

    def __init__(self, mapper: CarRouteDataMapper | None = None) -> None:
        self._mapper: CarRouteDataMapper = mapper or CarRouteDataMapper()

    def find_car_route(
        self,
        origin_location: Location,
        destination_location: Location,
        travel_date: date,
        number_of_passengers: int,
    ) -> list[TransportOption]:
        """
        Calculates personal car route options for the given journey date.
        """
        spherical_distance_km = origin_location.calculate_distance_in_kilometers_to(
            destination_location
        )
        # Real-world road detour factor is approximately 1.22 - 1.28 of great-circle distance
        actual_driving_distance_km = round(spherical_distance_km * 1.25, 1)

        # Average driving speed including brief rest stops: 95 km/h
        duration_minutes = max(30, int((actual_driving_distance_km / 95.0) * 60))

        # Fuel cost: 6.8 liters / 100km at 1.82 EUR / liter
        fuel_consumption_liters = (actual_driving_distance_km / 100.0) * 6.8
        fuel_cost_eur = round(fuel_consumption_liters * 1.82, 2)

        # Toll estimation: approx 0.04 EUR per km for international motorway transit
        toll_cost_eur = (
            round(actual_driving_distance_km * 0.04, 2)
            if origin_location.country_code != destination_location.country_code
            else 0.0
        )

        dep_time = datetime.combine(travel_date, time(7, 0))
        route_id = f"CAR-{origin_location.name[:3].upper()}-{destination_location.name[:3].upper()}-{travel_date.strftime('%Y%m%d')}"

        raw_payload: dict[str, Any] = {
            "route_id": route_id,
            "departure_location": origin_location.name,
            "destination_location": destination_location.name,
            "start_time_iso": dep_time.isoformat(),
            "distance_in_kilometers": actual_driving_distance_km,
            "duration_in_minutes": duration_minutes,
            "estimated_fuel_cost_eur": fuel_cost_eur,
            "estimated_toll_cost_eur": toll_cost_eur,
            "car_model_or_category": "Standard Passenger Vehicle",
            "highway_segments": [
                {
                    "from_waypoint": origin_location.name,
                    "to_waypoint": f"Border {origin_location.country_code}/{destination_location.country_code}",
                    "highway_name": f"Motorway {origin_location.country_code}-Autobahn",
                    "distance_km": round(actual_driving_distance_km * 0.5, 1),
                    "estimated_minutes": duration_minutes // 2,
                },
                {
                    "from_waypoint": f"Border {origin_location.country_code}/{destination_location.country_code}",
                    "to_waypoint": destination_location.name,
                    "highway_name": f"Autoroute {destination_location.country_code}-Corridor",
                    "distance_km": round(actual_driving_distance_km * 0.5, 1),
                    "estimated_minutes": duration_minutes - (duration_minutes // 2),
                },
            ],
        }

        option = self._mapper.map_raw_payload_to_transport_option(raw_payload)
        return [option]

