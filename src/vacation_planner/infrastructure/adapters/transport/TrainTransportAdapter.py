from __future__ import annotations

from datetime import date, datetime, time, timedelta
from typing import Any
from src.vacation_planner.core.domain.models.Location import Location
from src.vacation_planner.core.domain.models.TransportOption import TransportOption
from src.vacation_planner.infrastructure.mappers.TrainDataMapper import TrainDataMapper


class TrainTransportAdapter:
    """
    Adapter responsible for querying rail connections and schedules across European railway networks
    (e.g., Deutsche Bahn ICE, French TGV, Austrian ÖBB). Uses TrainDataMapper.
    """

    def __init__(self, mapper: TrainDataMapper | None = None) -> None:
        self._mapper: TrainDataMapper = mapper or TrainDataMapper()

    def find_trains(
        self,
        origin_location: Location,
        destination_location: Location,
        travel_date: date,
        number_of_passengers: int,
    ) -> list[TransportOption]:
        """
        Calculates realistic high-speed and regional rail connections based on origin/destination.
        """
        distance_km = origin_location.calculate_distance_in_kilometers_to(destination_location)
        # Average train speed: ~150-180 km/h on high-speed rail corridor
        train_duration_minutes = max(45, int((distance_km / 160.0) * 60) + 20)

        results: list[TransportOption] = []

        # Rail options: Early ICE, Midday EuroCity, Afternoon Express
        schedules = [
            ("ICE Morning Sprinter", time(7, 15), "Deutsche Bahn", "ICE", 1.0, 16.5),
            ("EuroCity Direct", time(11, 45), "ÖBB / SBB Railjet", "EC", 0.90, 14.8),
            ("TGV Evening Express", time(16, 30), "SNCF / DB", "TGV", 1.10, 15.2),
        ]

        base_fare = max(29.0, (distance_km * 0.08))

        for index, (label, departure_slot, operator, category, price_modifier, co2_per_person) in enumerate(schedules):
            dep_datetime = datetime.combine(travel_date, departure_slot)
            arr_datetime = dep_datetime + timedelta(minutes=train_duration_minutes)

            total_fare = round(base_fare * price_modifier * number_of_passengers, 2)
            connection_id = f"RAIL-{category}-{origin_location.country_code}{destination_location.country_code}-{index + 1}-{travel_date.strftime('%Y%m%d')}"

            # If journey duration exceeds 4 hours, model a realistic intermediate transfer
            legs: list[dict[str, Any]] = []
            if train_duration_minutes > 240:
                half_duration = train_duration_minutes // 2
                midpoint_arrival = dep_datetime + timedelta(minutes=half_duration)
                midpoint_departure = midpoint_arrival + timedelta(minutes=20)  # 20 min transfer

                legs.append({
                    "from_station": f"{origin_location.name} Hbf",
                    "to_station": "Frankfurt(Main) Hbf",
                    "departure": dep_datetime.isoformat(),
                    "arrival": midpoint_arrival.isoformat(),
                    "train_category": category,
                    "line_number": f"{category} {100 + index * 10}",
                })
                legs.append({
                    "from_station": "Frankfurt(Main) Hbf",
                    "to_station": f"{destination_location.name} Central Station",
                    "departure": midpoint_departure.isoformat(),
                    "arrival": (midpoint_departure + timedelta(minutes=half_duration)).isoformat(),
                    "train_category": category,
                    "line_number": f"{category} {500 + index * 10}",
                })
                arr_datetime = midpoint_departure + timedelta(minutes=half_duration)
            else:
                legs.append({
                    "from_station": f"{origin_location.name} Hbf",
                    "to_station": f"{destination_location.name} Central Station",
                    "departure": dep_datetime.isoformat(),
                    "arrival": arr_datetime.isoformat(),
                    "train_category": category,
                    "line_number": f"{category} {300 + index * 10}",
                })

            raw_payload: dict[str, Any] = {
                "connection_id": connection_id,
                "train_operator": operator,
                "departure_station_name": f"{origin_location.name} Hbf",
                "arrival_station_name": f"{destination_location.name} Central Station",
                "origin_city_name": origin_location.name,
                "destination_city_name": destination_location.name,
                "departure_timestamp": dep_datetime.isoformat(),
                "arrival_timestamp": arr_datetime.isoformat(),
                "ticket_price_eur": total_fare,
                "train_legs": legs,
                "eco_carbon_kg": round(co2_per_person * number_of_passengers, 2),
                "booking_link": f"https://railways.example.com/tickets/{connection_id}",
            }

            option = self._mapper.map_raw_payload_to_transport_option(raw_payload)
            results.append(option)

        return results

