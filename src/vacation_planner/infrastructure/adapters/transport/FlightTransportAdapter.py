from __future__ import annotations

from datetime import date, datetime, time
from typing import Any
from src.vacation_planner.core.domain.models.Location import Location
from src.vacation_planner.core.domain.models.TransportOption import TransportOption
from src.vacation_planner.core.domain.value_objects.TransportType import TransportType
from src.vacation_planner.infrastructure.mappers.FlightDataMapper import FlightDataMapper


class FlightTransportAdapter:
    """
    Adapter responsible for querying and synthesizing flight transportation alternatives
    between origin and destination airports. Uses FlightDataMapper to convert external payload structures.
    """

    AIRPORT_CODES: dict[str, str] = {
        "Berlin": "BER",
        "Paris": "CDG",
        "Rome": "FCO",
        "Barcelona": "BCN",
        "Vienna": "VIE",
        "Amsterdam": "AMS",
        "Zurich": "ZRH",
        "London": "LHR",
        "Madrid": "MAD",
        "Prague": "PRG",
        "Munich": "MUC",
        "Venice": "VCE",
        "Lisbon": "LIS",
    }

    def __init__(self, mapper: FlightDataMapper | None = None) -> None:
        self._mapper: FlightDataMapper = mapper or FlightDataMapper()

    def find_flights(
        self,
        origin_location: Location,
        destination_location: Location,
        travel_date: date,
        number_of_passengers: int,
    ) -> list[TransportOption]:
        """
        Simulates and maps real-world scheduled commercial flight itineraries
        between major European hubs based on geographic distances and passenger count.
        """
        origin_code = self.AIRPORT_CODES.get(origin_location.name, "ORG")
        dest_code = self.AIRPORT_CODES.get(destination_location.name, "DST")

        distance_km = origin_location.calculate_distance_in_kilometers_to(destination_location)
        flight_duration_minutes = max(60, int((distance_km / 750.0) * 60) + 30)

        results: list[TransportOption] = []

        # Departure schedules: Morning, Midday, Evening
        time_slots = [
            ("Morning Express", time(8, 0), "Lufthansa", 1.0, 110.0),
            ("Afternoon Economy", time(13, 30), "Eurowings", 0.85, 115.0),
            ("Evening Premier", time(18, 45), "Air France", 1.15, 108.0),
        ]

        base_fare = max(49.0, (distance_km * 0.12))

        for index, (label, departure_time_slot, airline, price_modifier, co2_per_passenger) in enumerate(time_slots):
            dep_datetime = datetime.combine(travel_date, departure_time_slot)
            hours_to_add = flight_duration_minutes // 60
            minutes_to_add = flight_duration_minutes % 60
            arr_datetime = dep_datetime.replace(
                hour=(dep_datetime.hour + hours_to_add) % 24,
                minute=(dep_datetime.minute + minutes_to_add) % 60,
            )

            total_fare = round(base_fare * price_modifier * number_of_passengers, 2)
            flight_id = f"FL-{origin_code}{dest_code}-{index + 1}-{travel_date.strftime('%Y%m%d')}"

            raw_payload: dict[str, Any] = {
                "flight_id": flight_id,
                "airline_name": airline,
                "departure_airport_code": origin_code,
                "arrival_airport_code": dest_code,
                "origin_city_name": origin_location.name,
                "destination_city_name": destination_location.name,
                "scheduled_departure_iso": dep_datetime.isoformat(),
                "scheduled_arrival_iso": arr_datetime.isoformat(),
                "fare_amount": total_fare,
                "currency_code": "EUR",
                "estimated_co2_kg": round(co2_per_passenger * number_of_passengers, 2),
                "booking_deep_link": f"https://flights.example.com/booking/{flight_id}",
                "flight_legs": [
                    {
                        "origin_airport": origin_code,
                        "destination_airport": dest_code,
                        "departure_time": dep_datetime.isoformat(),
                        "arrival_time": arr_datetime.isoformat(),
                        "operating_carrier": airline,
                        "flight_number": f"{airline[:2].upper()}{index * 100 + 201}",
                    }
                ],
            }

            option = self._mapper.map_raw_payload_to_transport_option(raw_payload)
            results.append(option)

        return results
