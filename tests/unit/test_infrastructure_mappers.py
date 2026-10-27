import unittest
from src.vacation_planner.core.domain.value_objects.DateRange import DateRange
from src.vacation_planner.core.domain.value_objects.TransportType import TransportType
from src.vacation_planner.infrastructure.mappers.AttractionDataMapper import AttractionDataMapper
from src.vacation_planner.infrastructure.mappers.CarRouteDataMapper import CarRouteDataMapper
from src.vacation_planner.infrastructure.mappers.FlightDataMapper import FlightDataMapper
from src.vacation_planner.infrastructure.mappers.GeographicLocationDataMapper import (
    GeographicLocationDataMapper,
)
from src.vacation_planner.infrastructure.mappers.HotelAccommodationDataMapper import (
    HotelAccommodationDataMapper,
)
from src.vacation_planner.infrastructure.mappers.TrainDataMapper import TrainDataMapper


class TestInfrastructureMappers(unittest.TestCase):
    def test_flight_data_mapper(self) -> None:
        mapper = FlightDataMapper()
        payload = {
            "flight_id": "LH-1234",
            "airline_name": "Lufthansa",
            "departure_airport_code": "BER",
            "arrival_airport_code": "CDG",
            "origin_city_name": "Berlin",
            "destination_city_name": "Paris",
            "scheduled_departure_iso": "2026-07-01T08:00:00",
            "scheduled_arrival_iso": "2026-07-01T09:45:00",
            "fare_amount": 149.90,
            "currency_code": "EUR",
            "estimated_co2_kg": 110.0,
            "flight_legs": [
                {
                    "origin_airport": "BER",
                    "destination_airport": "CDG",
                    "departure_time": "2026-07-01T08:00:00",
                    "arrival_time": "2026-07-01T09:45:00",
                    "operating_carrier": "Lufthansa",
                    "flight_number": "LH1234",
                }
            ],
        }
        option = mapper.map_raw_payload_to_transport_option(payload)
        self.assertEqual(option.transport_option_id, "LH-1234")
        self.assertEqual(option.transport_type, TransportType.FLIGHT)
        self.assertEqual(option.total_price.to_float(), 149.90)
        self.assertTrue(option.is_direct_connection())

    def test_train_data_mapper(self) -> None:
        mapper = TrainDataMapper()
        payload = {
            "connection_id": "ICE-501",
            "train_operator": "Deutsche Bahn",
            "departure_station_name": "Berlin Hbf",
            "arrival_station_name": "Paris Est",
            "origin_city_name": "Berlin",
            "destination_city_name": "Paris",
            "departure_timestamp": "2026-07-01T07:00:00",
            "arrival_timestamp": "2026-07-01T15:30:00",
            "ticket_price_eur": 89.50,
            "eco_carbon_kg": 18.5,
            "train_legs": [
                {
                    "from_station": "Berlin Hbf",
                    "to_station": "Frankfurt Hbf",
                    "departure": "2026-07-01T07:00:00",
                    "arrival": "2026-07-01T11:00:00",
                    "train_category": "ICE",
                    "line_number": "ICE 501",
                },
                {
                    "from_station": "Frankfurt Hbf",
                    "to_station": "Paris Est",
                    "departure": "2026-07-01T11:30:00",
                    "arrival": "2026-07-01T15:30:00",
                    "train_category": "ICE",
                    "line_number": "ICE 9552",
                },
            ],
        }
        option = mapper.map_raw_payload_to_transport_option(payload)
        self.assertEqual(option.transport_option_id, "ICE-501")
        self.assertEqual(option.transport_type, TransportType.TRAIN)
        self.assertEqual(option.count_transfers(), 1)
        self.assertFalse(option.is_direct_connection())

    def test_car_route_data_mapper(self) -> None:
        mapper = CarRouteDataMapper()
        payload = {
            "route_id": "CAR-BER-PAR",
            "departure_location": "Berlin",
            "destination_location": "Paris",
            "start_time_iso": "2026-07-01T06:00:00",
            "distance_in_kilometers": 1050.0,
            "duration_in_minutes": 630,
            "estimated_fuel_cost_eur": 140.0,
            "estimated_toll_cost_eur": 35.0,
        }
        option = mapper.map_raw_payload_to_transport_option(payload)
        self.assertEqual(option.transport_type, TransportType.CAR)
        self.assertEqual(option.total_price.to_float(), 175.0)

    def test_hotel_data_mapper(self) -> None:
        mapper = HotelAccommodationDataMapper()
        dr = DateRange("2026-07-01", "2026-07-05")  # 4 nights
        payload = {
            "property_id": "HTL-01",
            "hotel_name": "Hotel Parisien",
            "type": "HOTEL",
            "city": "Paris",
            "latitude": 48.85,
            "longitude": 2.35,
            "nightly_rate_eur": 100.0,
            "star_rating": 4.0,
            "address": "12 Rue de Paris",
            "amenity_list": ["WiFi", "Breakfast"],
        }
        acc = mapper.map_raw_payload_to_accommodation_option(payload, dr)
        self.assertEqual(acc.accommodation_id, "HTL-01")
        self.assertEqual(acc.total_price.to_float(), 400.0)  # 4 nights * 100 EUR
        self.assertTrue(acc.has_amenity("wifi"))

    def test_geographic_location_mapper(self) -> None:
        mapper = GeographicLocationDataMapper()
        payload = {
            "place_id": "LOC-BER",
            "city_name": "Berlin",
            "country": "Germany",
            "country_code": "DE",
            "lat": 52.52,
            "lon": 13.40,
            "summary": "Capital of Germany",
        }
        loc = mapper.map_raw_payload_to_location(payload)
        self.assertEqual(loc.location_id, "LOC-BER")
        self.assertEqual(loc.country_code, "DE")

    def test_attraction_mapper(self) -> None:
        mapper = AttractionDataMapper()
        payload = {
            "attraction_id": "ATTR-01",
            "name": "Eiffel Tower",
            "city": "Paris",
            "category": "HISTORICAL_MONUMENT",
            "latitude": 48.8584,
            "longitude": 2.2945,
            "admission_fee_eur": 25.0,
            "duration_minutes": 120,
            "rating": 4.8,
        }
        attr = mapper.map_raw_payload_to_attraction(payload)
        self.assertEqual(attr.attraction_id, "ATTR-01")
        self.assertFalse(attr.is_admission_free())
        self.assertEqual(attr.admission_fee.to_float(), 25.0)


if __name__ == "__main__":
    unittest.main()
