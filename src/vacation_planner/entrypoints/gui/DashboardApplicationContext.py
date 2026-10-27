from __future__ import annotations

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


class DashboardApplicationContext:
    """
    Dependency injection container providing access to Clean Architecture domain use cases,
    gateways, and repositories for all dashboard views.
    """

    def __init__(
        self,
        transport_gateway: TransportGatewayInterface | None = None,
        accommodation_gateway: AccommodationGatewayInterface | None = None,
        location_gateway: LocationGatewayInterface | None = None,
        package_repository: PackageRepositoryInterface | None = None,
        cost_calculation_service: CostCalculationService | None = None,
    ) -> None:
        self._transport_gateway: TransportGatewayInterface = (
            transport_gateway or CompositeTransportAdapter()
        )
        self._accommodation_gateway: AccommodationGatewayInterface = (
            accommodation_gateway or HotelAccommodationAdapter()
        )
        self._location_gateway: LocationGatewayInterface = (
            location_gateway or CompositeLocationGatewayAdapter()
        )
        self._package_repository: PackageRepositoryInterface = (
            package_repository or InMemoryPackageRepository()
        )
        self._cost_calculation_service: CostCalculationService = (
            cost_calculation_service or CostCalculationService()
        )

        self._aggregator_service = TravelPackageAggregatorService(
            transport_gateway=self._transport_gateway,
            accommodation_gateway=self._accommodation_gateway,
            location_gateway=self._location_gateway,
            package_repository=self._package_repository,
            cost_calculation_service=self._cost_calculation_service,
        )

        self._package_details_use_case = GetVacationPackageDetailsUseCase(
            package_repository=self._package_repository
        )

    @property
    def aggregator_service(self) -> TravelPackageAggregatorService:
        return self._aggregator_service

    @property
    def package_details_use_case(self) -> GetVacationPackageDetailsUseCase:
        return self._package_details_use_case

    @property
    def package_repository(self) -> PackageRepositoryInterface:
        return self._package_repository

    @property
    def transport_gateway(self) -> TransportGatewayInterface:
        return self._transport_gateway

    @property
    def accommodation_gateway(self) -> AccommodationGatewayInterface:
        return self._accommodation_gateway

    @property
    def location_gateway(self) -> LocationGatewayInterface:
        return self._location_gateway

    @property
    def cost_calculation_service(self) -> CostCalculationService:
        return self._cost_calculation_service
