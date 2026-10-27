import uuid
from typing import Sequence
from src.vacation_planner.core.domain.models.AccommodationOption import AccommodationOption
from src.vacation_planner.core.domain.models.Attraction import Attraction
from src.vacation_planner.core.domain.models.Location import Location
from src.vacation_planner.core.domain.models.TransportOption import TransportOption
from src.vacation_planner.core.domain.models.VacationPackage import VacationPackage
from src.vacation_planner.core.domain.models.VacationSearchCriteria import VacationSearchCriteria
from src.vacation_planner.core.interfaces.AccommodationGatewayInterface import (
    AccommodationGatewayInterface,
)
from src.vacation_planner.core.interfaces.LocationGatewayInterface import (
    LocationGatewayInterface,
)
from src.vacation_planner.core.interfaces.PackageRepositoryInterface import (
    PackageRepositoryInterface,
)
from src.vacation_planner.core.interfaces.TransportGatewayInterface import (
    TransportGatewayInterface,
)
from src.vacation_planner.core.use_cases.CostCalculationService import CostCalculationService


class TravelPackageAggregatorService:
    """
    Central domain use case service that coordinates transport options, accommodation options,
    and destination attractions to generate synchronized vacation packages.
    Validates total costs, timing alignment, and budget compliance without depending
    on any external framework.
    """

    def __init__(
        self,
        transport_gateway: TransportGatewayInterface,
        accommodation_gateway: AccommodationGatewayInterface,
        location_gateway: LocationGatewayInterface,
        package_repository: PackageRepositoryInterface,
        cost_calculation_service: CostCalculationService,
    ) -> None:
        self._transport_gateway: TransportGatewayInterface = transport_gateway
        self._accommodation_gateway: AccommodationGatewayInterface = accommodation_gateway
        self._location_gateway: LocationGatewayInterface = location_gateway
        self._package_repository: PackageRepositoryInterface = package_repository
        self._cost_calculation_service: CostCalculationService = cost_calculation_service

    def generate_vacation_packages(
        self, search_criteria: VacationSearchCriteria
    ) -> list[VacationPackage]:
        """
        Executes the end-to-end package aggregation pipeline:
        1. Resolves origin and destination locations.
        2. Retrieves outbound and return transport options.
        3. Retrieves matching accommodations for the requested date range.
        4. Fetches destination attractions.
        5. Synchronizes components, validates costs, and compiles complete packages.
        6. Persists valid packages into the repository and returns them sorted by price.
        """
        # 1. Resolve locations
        origin_location: Location = self._location_gateway.resolve_location_by_name(
            search_criteria.origin_location_name
        )
        destination_location: Location = self._location_gateway.resolve_location_by_name(
            search_criteria.destination_location_name
        )

        # 2. Query outbound and return transport options
        outbound_options: list[TransportOption] = (
            self._transport_gateway.search_transport_options(
                origin_location=origin_location,
                destination_location=destination_location,
                travel_date=search_criteria.date_range.start_date,
                allowed_transport_types=search_criteria.allowed_transport_types,
                number_of_passengers=search_criteria.number_of_travelers,
            )
        )

        return_options: list[TransportOption] = (
            self._transport_gateway.search_transport_options(
                origin_location=destination_location,
                destination_location=origin_location,
                travel_date=search_criteria.date_range.end_date,
                allowed_transport_types=search_criteria.allowed_transport_types,
                number_of_passengers=search_criteria.number_of_travelers,
            )
        )

        # 3. Query accommodation options
        accommodation_options: list[AccommodationOption] = (
            self._accommodation_gateway.search_accommodation_options(
                destination_location=destination_location,
                date_range=search_criteria.date_range,
                number_of_guests=search_criteria.number_of_travelers,
                preferred_accommodation_type=search_criteria.preferred_accommodation_type,
            )
        )

        # 4. Query destination attractions
        recommended_attractions: list[Attraction] = (
            self._location_gateway.fetch_local_attractions_for_location(
                destination_location=destination_location,
                maximum_results=8,
            )
        )

        # 5. Synchronize and combine into packages
        generated_packages: list[VacationPackage] = []

        for outbound in outbound_options:
            for inbound in return_options:
                # Synchronization rule: Outbound arrival must be before return departure
                if outbound.arrival_time >= inbound.departure_time:
                    continue

                for accommodation in accommodation_options:
                    validation_notes: list[str] = []

                    total_cost = self._cost_calculation_service.calculate_total_package_cost(
                        outbound_transport=outbound,
                        return_transport=inbound,
                        accommodation=accommodation,
                    )

                    is_within_budget, budget_message = (
                        self._cost_calculation_service.evaluate_budget_compliance(
                            total_cost=total_cost,
                            maximum_budget=search_criteria.maximum_budget,
                        )
                    )
                    validation_notes.append(budget_message)

                    # Check transport mode harmony
                    if outbound.transport_type == inbound.transport_type:
                        validation_notes.append(
                            f"Consistent round-trip transport mode: {outbound.transport_type.value}."
                        )
                    else:
                        validation_notes.append(
                            f"Mixed transport modes: outbound {outbound.transport_type.value}, "
                            f"return {inbound.transport_type.value}."
                        )

                    package_unique_id = f"PKG-{uuid.uuid4().hex[:10].upper()}"

                    package = VacationPackage(
                        package_id=package_unique_id,
                        origin_location=origin_location,
                        destination_location=destination_location,
                        date_range=search_criteria.date_range,
                        outbound_transport_option=outbound,
                        return_transport_option=inbound,
                        accommodation_option=accommodation,
                        recommended_attractions=recommended_attractions,
                        total_package_cost=total_cost,
                        is_within_budget=is_within_budget,
                        validation_notes=validation_notes,
                    )

                    generated_packages.append(package)
                    self._package_repository.save_vacation_package(package)

        # 6. Sort packages: First within-budget packages, then sorted by total price ascending
        generated_packages.sort(
            key=lambda pkg: (
                0 if pkg.is_within_budget else 1,
                pkg.total_package_cost.amount,
            )
        )

        return generated_packages
