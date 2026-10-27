import unittest
from src.vacation_planner.core.domain.models.VacationSearchCriteria import VacationSearchCriteria
from src.vacation_planner.core.domain.value_objects.DateRange import DateRange
from src.vacation_planner.core.domain.value_objects.MonetaryAmount import MonetaryAmount
from src.vacation_planner.core.domain.value_objects.TransportType import TransportType
from src.vacation_planner.core.use_cases.CostCalculationService import CostCalculationService
from src.vacation_planner.core.use_cases.TravelPackageAggregatorService import (
    TravelPackageAggregatorService,
)
from src.vacation_planner.infrastructure.adapters.accommodation.HotelAccommodationAdapter import (
    HotelAccommodationAdapter,
)
from src.vacation_planner.infrastructure.adapters.location.CompositeLocationGatewayAdapter import (
    CompositeLocationGatewayAdapter,
)
from src.vacation_planner.infrastructure.adapters.persistence.InMemoryPackageRepository import (
    InMemoryPackageRepository,
)
from src.vacation_planner.infrastructure.adapters.transport.CompositeTransportAdapter import (
    CompositeTransportAdapter,
)


class TestTravelPackageAggregatorServiceIntegration(unittest.TestCase):
    def setUp(self) -> None:
        self.transport_adapter = CompositeTransportAdapter()
        self.accommodation_adapter = HotelAccommodationAdapter()
        self.location_adapter = CompositeLocationGatewayAdapter()
        self.repository = InMemoryPackageRepository()
        self.cost_service = CostCalculationService()

        self.aggregator = TravelPackageAggregatorService(
            transport_gateway=self.transport_adapter,
            accommodation_gateway=self.accommodation_adapter,
            location_gateway=self.location_adapter,
            package_repository=self.repository,
            cost_calculation_service=self.cost_service,
        )

    def test_generate_vacation_packages_berlin_to_paris(self) -> None:
        criteria = VacationSearchCriteria(
            origin_location_name="Berlin",
            destination_location_name="Paris",
            date_range=DateRange("2026-08-01", "2026-08-05"),  # 4 nights
            maximum_budget=MonetaryAmount("1500.00", "EUR"),
            allowed_transport_types=[TransportType.FLIGHT, TransportType.TRAIN, TransportType.CAR],
            number_of_travelers=2,
        )

        packages = self.aggregator.generate_vacation_packages(criteria)

        self.assertGreater(len(packages), 0)
        # Packages should be saved to repository
        self.assertEqual(len(self.repository.list_all_vacation_packages()), len(packages))

        # Check first package
        first_pkg = packages[0]
        self.assertEqual(first_pkg.origin_location.name, "Berlin")
        self.assertEqual(first_pkg.destination_location.name, "Paris")
        self.assertGreater(len(first_pkg.recommended_attractions), 0)
        self.assertIsNotNone(first_pkg.total_package_cost)
        self.assertTrue(first_pkg.is_within_budget)

        # Check cost integrity
        expected_cost = (
            first_pkg.outbound_transport_option.total_price.add(
                first_pkg.return_transport_option.total_price
            ).add(first_pkg.accommodation_option.total_price)
        )
        self.assertEqual(first_pkg.total_package_cost, expected_cost)

    def test_budget_exceeded_packages_flagged_correctly(self) -> None:
        # Strict low budget that cannot cover hotel + transport
        criteria = VacationSearchCriteria(
            origin_location_name="Berlin",
            destination_location_name="Paris",
            date_range=DateRange("2026-08-01", "2026-08-08"),
            maximum_budget=MonetaryAmount("50.00", "EUR"),  # Impossibly low
            allowed_transport_types=[TransportType.FLIGHT],
            number_of_travelers=2,
        )

        packages = self.aggregator.generate_vacation_packages(criteria)
        self.assertGreater(len(packages), 0)
        for pkg in packages:
            self.assertFalse(pkg.is_within_budget)
            self.assertTrue(any("exceeds maximum budget" in note for note in pkg.validation_notes))


if __name__ == "__main__":
    unittest.main()

