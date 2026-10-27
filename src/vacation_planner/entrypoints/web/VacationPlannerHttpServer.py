from __future__ import annotations

from http.server import HTTPServer
import threading
from typing import Type
from src.vacation_planner.core.use_cases.CostCalculationService import CostCalculationService
from src.vacation_planner.core.use_cases.GetVacationPackageDetailsUseCase import (
    GetVacationPackageDetailsUseCase,
)
from src.vacation_planner.core.use_cases.TravelPackageAggregatorService import (
    TravelPackageAggregatorService,
)
from src.vacation_planner.entrypoints.web.VacationPlannerHttpHandler import (
    VacationPlannerHttpHandler,
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


class VacationPlannerHttpServer:
    """
    Wrapper managing the lifecycle of the Vacation Planner HTTP REST API server.
    Wires Clean Architecture dependencies and spins up the HTTP server.
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 8080) -> None:
        self._host: str = host
        self._port: int = port
        self._server: HTTPServer | None = None
        self._server_thread: threading.Thread | None = None

        # Wire Clean Architecture dependencies
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

    @property
    def port(self) -> int:
        if self._server:
            return self._server.server_port
        return self._port

    def start(self, run_in_background: bool = False) -> None:
        """
        Starts the HTTP server. If run_in_background is True, starts in a separate daemon thread.
        """
        # Create a customized handler subclass with injected services
        handler_class: Type[VacationPlannerHttpHandler] = type(
            "ConfiguredVacationPlannerHttpHandler",
            (VacationPlannerHttpHandler,),
            {
                "aggregator_service": self._aggregator_service,
                "package_details_use_case": self._details_use_case,
            },
        )

        self._server = HTTPServer((self._host, self._port), handler_class)

        if run_in_background:
            self._server_thread = threading.Thread(
                target=self._server.serve_forever, daemon=True
            )
            self._server_thread.start()
        else:
            self._server.serve_forever()

    def stop(self) -> None:
        """
        Shuts down the HTTP server cleanly.
        """
        if self._server:
            self._server.shutdown()
            self._server.server_close()
            if self._server_thread and self._server_thread.is_alive():
                self._server_thread.join(timeout=2.0)
            self._server = None

