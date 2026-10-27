from __future__ import annotations

import io
import json
import unittest
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


class DummySocket:
    """Simulates a network socket using BytesIO for in-memory HTTP testing."""

    def __init__(self, request_bytes: bytes) -> None:
        self.rfile = io.BytesIO(request_bytes)
        self.wfile = io.BytesIO()

    def makefile(self, mode: str, *args, **kwargs):
        if "b" in mode:
            if "r" in mode:
                return self.rfile
            return self.wfile
        raise ValueError("Only binary mode is supported.")

    def sendall(self, data: bytes) -> None:
        self.wfile.write(data)


class TestApiEndpoints(unittest.TestCase):
    def setUp(self) -> None:
        self.transport_adapter = CompositeTransportAdapter()
        self.accommodation_adapter = HotelAccommodationAdapter()
        self.location_adapter = CompositeLocationGatewayAdapter()
        self.package_repository = InMemoryPackageRepository()
        self.cost_service = CostCalculationService()

        self.aggregator_service = TravelPackageAggregatorService(
            transport_gateway=self.transport_adapter,
            accommodation_gateway=self.accommodation_adapter,
            location_gateway=self.location_adapter,
            package_repository=self.package_repository,
            cost_calculation_service=self.cost_service,
        )

        self.details_use_case = GetVacationPackageDetailsUseCase(
            package_repository=self.package_repository
        )

        self.handler_class: Type[VacationPlannerHttpHandler] = type(
            "TestHttpHandler",
            (VacationPlannerHttpHandler,),
            {
                "aggregator_service": self.aggregator_service,
                "package_details_use_case": self.details_use_case,
            },
        )

    def _execute_http_request(
        self, method: str, path: str, body: dict | None = None
    ) -> tuple[int, dict]:
        request_lines = [f"{method} {path} HTTP/1.1", "Host: localhost"]
        body_bytes = b""
        if body is not None:
            body_bytes = json.dumps(body).encode("utf-8")
            request_lines.append(f"Content-Length: {len(body_bytes)}")
            request_lines.append("Content-Type: application/json")

        raw_request = "\r\n".join(request_lines).encode("utf-8") + b"\r\n\r\n" + body_bytes
        mock_socket = DummySocket(raw_request)

        # Instantiate handler with mock socket
        handler = self.handler_class(mock_socket, ("127.0.0.1", 12345), None)  # type: ignore

        # Parse response
        response_bytes = mock_socket.wfile.getvalue()
        parts = response_bytes.split(b"\r\n\r\n", 1)
        header_text = parts[0].decode("utf-8")
        body_text = parts[1].decode("utf-8") if len(parts) > 1 else ""

        status_code = int(header_text.splitlines()[0].split()[1])
        json_body = json.loads(body_text) if body_text else {}
        return status_code, json_body

    def test_health_check_endpoint(self) -> None:
        status_code, response_json = self._execute_http_request("GET", "/api/v1/health")
        self.assertEqual(status_code, 200)
        self.assertEqual(response_json["status"], "HEALTHY")

    def test_search_and_get_vacation_package(self) -> None:
        payload = {
            "origin": "Berlin",
            "destination": "Paris",
            "start_date": "2026-08-01",
            "end_date": "2026-08-05",
            "maximum_budget": 1600.0,
            "currency": "EUR",
            "number_of_travelers": 2,
            "allowed_transport_types": ["FLIGHT", "TRAIN", "CAR"],
        }
        status_code, response_json = self._execute_http_request(
            "POST", "/api/v1/packages/search", payload
        )
        self.assertEqual(status_code, 200)
        self.assertGreater(response_json["total_results"], 0)

        first_package = response_json["packages"][0]
        package_id = first_package["package_id"]

        # Fetch detail
        detail_status, detail_json = self._execute_http_request(
            "GET", f"/api/v1/packages/{package_id}"
        )
        self.assertEqual(detail_status, 200)
        self.assertEqual(detail_json["package_id"], package_id)

    def test_search_invalid_dates_returns_400(self) -> None:
        payload = {
            "origin": "Berlin",
            "destination": "Paris",
            "start_date": "2026-08-10",
            "end_date": "2026-08-01",  # Invalid chronological order
            "maximum_budget": 1000.0,
        }
        status_code, response_json = self._execute_http_request(
            "POST", "/api/v1/packages/search", payload
        )
        self.assertEqual(status_code, 400)
        self.assertIn("error", response_json)


if __name__ == "__main__":
    unittest.main()
