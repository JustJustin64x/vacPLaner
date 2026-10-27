from __future__ import annotations

import sys
from src.vacation_planner.core.domain.models.VacationSearchCriteria import VacationSearchCriteria
from src.vacation_planner.core.domain.value_objects.DateRange import DateRange
from src.vacation_planner.core.domain.value_objects.MonetaryAmount import MonetaryAmount
from src.vacation_planner.core.domain.value_objects.TransportType import TransportType
from src.vacation_planner.core.use_cases.CostCalculationService import CostCalculationService
from src.vacation_planner.core.use_cases.GetVacationPackageDetailsUseCase import (
    GetVacationPackageDetailsUseCase,
)
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


class VacationPlannerCliApplication:
    """
    Console CLI Entry Point for the modular vacation planning tool.
    Allows interactive or argument-driven query execution and formatted terminal output.
    """

    def __init__(self) -> None:
        self._transport_adapter = CompositeTransportAdapter()
        self._accommodation_adapter = HotelAccommodationAdapter()
        self._location_adapter = CompositeLocationGatewayAdapter()
        self._package_repository = InMemoryPackageRepository()
        self._cost_service = CostCalculationService()

        self._aggregator_service = TravelPackageAggregatorService(
            transport_gateway=self._transport_adapter,
            accommodation_gateway=self._accommodation_adapter,
            location_gateway=self._location_adapter,
            package_repository=self._package_repository,
            cost_calculation_service=self._cost_service,
        )

        self._details_use_case = GetVacationPackageDetailsUseCase(
            package_repository=self._package_repository
        )

    def run_interactive(
        self,
        origin: str = "Berlin",
        destination: str = "Paris",
        start_date: str = "2026-07-01",
        end_date: str = "2026-07-07",
        maximum_budget: float = 1200.0,
        travelers: int = 1,
    ) -> None:
        """
        Executes a vacation package search and prints formatted summary tables.
        """
        print("=" * 75)
        print("  MODULARES URLAUBSPLANUNGS-TOOL (Clean Architecture Reiseplaner)")
        print("=" * 75)
        print(f"  Startort:          {origin}")
        print(f"  Zielort:           {destination}")
        print(f"  Reisezeitraum:     {start_date} bis {end_date}")
        print(f"  Maximales Budget:  {maximum_budget:.2f} EUR")
        print(f"  Reisende:          {travelers} Person(en)")
        print("-" * 75)
        print("  Suche nach Flügen, Bahn- und Pkw-Verbindungen sowie Hotels...")

        criteria = VacationSearchCriteria(
            origin_location_name=origin,
            destination_location_name=destination,
            date_range=DateRange(start_date=start_date, end_date=end_date),
            maximum_budget=MonetaryAmount(maximum_budget, "EUR"),
            allowed_transport_types=[
                TransportType.FLIGHT,
                TransportType.TRAIN,
                TransportType.CAR,
            ],
            number_of_travelers=travelers,
        )

        packages = self._aggregator_service.generate_vacation_packages(criteria)

        print(f"  -> {len(packages)} synchronisierte Urlaubspaket(e) generiert!\n")

        for index, pkg in enumerate(packages[:5], start=1):
            budget_flag = "✓ IM BUDGET" if pkg.is_within_budget else "✗ BUDGET ÜBERSCHRITTEN"
            print(f"┌─── Paket #{index}: {pkg.package_id} [{budget_flag}] " + "─" * (35 - len(pkg.package_id)))
            print(f"│ Gesamtkosten:     {pkg.total_package_cost} (Budget-Check: {pkg.validation_notes[0]})")
            print(f"│ CO2-Emission:     {pkg.calculate_total_carbon_dioxide_emission_in_kilograms()} kg CO2 (Hin & Rück)")
            print(f"│ Hinreise:         {pkg.outbound_transport_option.transport_type.value} mit {pkg.outbound_transport_option.segments[0].carrier_or_operator_name} ({pkg.outbound_transport_option.total_price})")
            print(f"│                   Abfahrt: {pkg.outbound_transport_option.departure_time.strftime('%Y-%m-%d %H:%M')} -> Ankunft: {pkg.outbound_transport_option.arrival_time.strftime('%Y-%m-%d %H:%M')}")
            print(f"│ Rückreise:        {pkg.return_transport_option.transport_type.value} mit {pkg.return_transport_option.segments[0].carrier_or_operator_name} ({pkg.return_transport_option.total_price})")
            print(f"│                   Abfahrt: {pkg.return_transport_option.departure_time.strftime('%Y-%m-%d %H:%M')} -> Ankunft: {pkg.return_transport_option.arrival_time.strftime('%Y-%m-%d %H:%M')}")
            print(f"│ Unterkunft:       {pkg.accommodation_option.name} [{pkg.accommodation_option.accommodation_type.value}] ({pkg.accommodation_option.total_price} für {pkg.date_range.calculate_total_nights()} Nächte)")
            print(f"│                   Bewertung: {pkg.accommodation_option.star_rating}★ | Adresse: {pkg.accommodation_option.address_line}")
            print(f"│ Top-Attraktionen: {', '.join(attr.name for attr in pkg.recommended_attractions[:3])}")
            print("└" + "─" * 74)
            print()


if __name__ == "__main__":
    app = VacationPlannerCliApplication()
    app.run_interactive()
