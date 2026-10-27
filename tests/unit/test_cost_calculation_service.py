import unittest
from datetime import datetime
from src.vacation_planner.core.domain.models.AccommodationOption import AccommodationOption
from src.vacation_planner.core.domain.models.TransportOption import TransportOption
from src.vacation_planner.core.domain.value_objects.AccommodationType import AccommodationType
from src.vacation_planner.core.domain.value_objects.DateRange import DateRange
from src.vacation_planner.core.domain.value_objects.GeographicCoordinates import (
    GeographicCoordinates,
)
from src.vacation_planner.core.domain.value_objects.MonetaryAmount import MonetaryAmount
from src.vacation_planner.core.domain.value_objects.RouteSegment import RouteSegment
from src.vacation_planner.core.domain.value_objects.TransportType import TransportType
from src.vacation_planner.core.use_cases.CostCalculationService import CostCalculationService


class TestCostCalculationService(unittest.TestCase):
    def setUp(self) -> None:
        self.service = CostCalculationService()

        segment_outbound = RouteSegment(
            departure_station_or_airport="BER",
            arrival_station_or_airport="CDG",
            departure_time=datetime(2026, 7, 1, 8, 0),
            arrival_time=datetime(2026, 7, 1, 9, 45),
            carrier_or_operator_name="Air France",
            segment_identifier="AF123",
        )
        self.outbound_transport = TransportOption(
            transport_option_id="TR-001",
            transport_type=TransportType.FLIGHT,
            origin_location_name="Berlin",
            destination_location_name="Paris",
            departure_time=datetime(2026, 7, 1, 8, 0),
            arrival_time=datetime(2026, 7, 1, 9, 45),
            segments=[segment_outbound],
            total_price=MonetaryAmount("120.00", "EUR"),
            carbon_dioxide_emission_in_kilograms=110.0,
        )

        segment_return = RouteSegment(
            departure_station_or_airport="CDG",
            arrival_station_or_airport="BER",
            departure_time=datetime(2026, 7, 7, 18, 0),
            arrival_time=datetime(2026, 7, 7, 19, 45),
            carrier_or_operator_name="Air France",
            segment_identifier="AF124",
        )
        self.return_transport = TransportOption(
            transport_option_id="TR-002",
            transport_type=TransportType.FLIGHT,
            origin_location_name="Paris",
            destination_location_name="Berlin",
            departure_time=datetime(2026, 7, 7, 18, 0),
            arrival_time=datetime(2026, 7, 7, 19, 45),
            segments=[segment_return],
            total_price=MonetaryAmount("130.00", "EUR"),
            carbon_dioxide_emission_in_kilograms=110.0,
        )

        self.accommodation = AccommodationOption(
            accommodation_id="ACC-001",
            name="Hotel Montmartre",
            accommodation_type=AccommodationType.HOTEL,
            location_name="Paris",
            coordinates=GeographicCoordinates(48.8867, 2.3431),
            date_range=DateRange("2026-07-01", "2026-07-07"),
            total_price=MonetaryAmount("600.00", "EUR"),
            price_per_night=MonetaryAmount("100.00", "EUR"),
            star_rating=4.0,
            address_line="10 Rue Custine, 75018 Paris",
            included_amenities=["WiFi", "Breakfast"],
        )

    def test_calculate_total_package_cost(self) -> None:
        # Outbound: 120 + Return: 130 + Accommodation: 600 = 850 EUR
        total = self.service.calculate_total_package_cost(
            outbound_transport=self.outbound_transport,
            return_transport=self.return_transport,
            accommodation=self.accommodation,
        )
        self.assertEqual(total.amount, MonetaryAmount("850.00", "EUR").amount)

    def test_evaluate_budget_compliance_within_budget(self) -> None:
        total = MonetaryAmount("850.00", "EUR")
        max_budget = MonetaryAmount("1000.00", "EUR")
        is_compliant, message = self.service.evaluate_budget_compliance(total, max_budget)
        self.assertTrue(is_compliant)
        self.assertIn("Remaining balance: 150.00 EUR", message)

    def test_evaluate_budget_compliance_exceeds_budget(self) -> None:
        total = MonetaryAmount("850.00", "EUR")
        max_budget = MonetaryAmount("700.00", "EUR")
        is_compliant, message = self.service.evaluate_budget_compliance(total, max_budget)
        self.assertFalse(is_compliant)
        self.assertIn("exceeds maximum budget by 150.00 EUR", message)


if __name__ == "__main__":
    unittest.main()
