from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler
from typing import Any
from urllib.parse import parse_qs, urlparse
from src.vacation_planner.core.domain.models.VacationSearchCriteria import VacationSearchCriteria
from src.vacation_planner.core.domain.value_objects.AccommodationType import AccommodationType
from src.vacation_planner.core.domain.value_objects.DateRange import DateRange
from src.vacation_planner.core.domain.value_objects.MonetaryAmount import MonetaryAmount
from src.vacation_planner.core.domain.value_objects.TransportType import TransportType
from src.vacation_planner.core.use_cases.GetVacationPackageDetailsUseCase import (
    GetVacationPackageDetailsUseCase,
)
from src.vacation_planner.core.use_cases.TravelPackageAggregatorService import (
    TravelPackageAggregatorService,
)
from src.vacation_planner.entrypoints.web.VacationPackageDtoMapper import VacationPackageDtoMapper


class VacationPlannerHttpHandler(BaseHTTPRequestHandler):
    """
    HTTP Request Handler managing REST Web API endpoints for the vacation planner backend.
    Enforces that all external API integrations remain strictly within the backend boundary
    so that frontend clients interact exclusively through this mediating API.
    """

    aggregator_service: TravelPackageAggregatorService
    package_details_use_case: GetVacationPackageDetailsUseCase
    dto_mapper: VacationPackageDtoMapper = VacationPackageDtoMapper()

    def do_OPTIONS(self) -> None:
        """Handle CORS pre-flight inquiries."""
        self.send_response(204)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self) -> None:
        """Route incoming GET requests."""
        parsed_url = urlparse(self.path)
        path = parsed_url.path

        if path == "/api/v1/health":
            self._respond_json(200, {"status": "HEALTHY", "service": "vacation-planner-api"})
            return

        if path == "/api/v1/packages":
            # List all packages in repository
            packages = self.package_details_use_case._package_repository.list_all_vacation_packages()
            payload = [self.dto_mapper.map_vacation_package_to_dto(pkg) for pkg in packages]
            self._respond_json(200, {"packages": payload, "count": len(payload)})
            return

        if path.startswith("/api/v1/packages/"):
            package_id = path.split("/api/v1/packages/")[-1].strip()
            try:
                package = self.package_details_use_case.execute(package_id)
                self._respond_json(200, self.dto_mapper.map_vacation_package_to_dto(package))
            except KeyError:
                self._respond_json(404, {"error": f"Package with ID '{package_id}' not found."})
            return

        self._respond_json(404, {"error": "Endpoint not found."})

    def do_POST(self) -> None:
        """Route incoming POST requests."""
        parsed_url = urlparse(self.path)
        path = parsed_url.path

        if path == "/api/v1/packages/search":
            content_length = int(self.headers.get("Content-Length", 0))
            if content_length <= 0:
                self._respond_json(400, {"error": "Missing or empty request body."})
                return

            raw_body = self.rfile.read(content_length).decode("utf-8")
            try:
                request_data = json.loads(raw_body)
            except json.JSONDecodeError as decode_error:
                self._respond_json(400, {"error": f"Malformed JSON request body: {decode_error}."})
                return

            try:
                # Parse criteria parameters
                origin = str(request_data["origin"])
                destination = str(request_data["destination"])
                start_date = str(request_data["start_date"])
                end_date = str(request_data["end_date"])
                date_range = DateRange(start_date=start_date, end_date=end_date)

                budget_amount = request_data.get("maximum_budget", 1500.0)
                budget_currency = str(request_data.get("currency", "EUR"))
                max_budget = MonetaryAmount(budget_amount, budget_currency)

                travelers = int(request_data.get("number_of_travelers", 1))

                # Parse transport types
                raw_transport_types = request_data.get("allowed_transport_types")
                if raw_transport_types:
                    allowed_types = [TransportType(t.upper()) for t in raw_transport_types]
                else:
                    allowed_types = [TransportType.FLIGHT, TransportType.TRAIN, TransportType.CAR]

                # Parse preferred accommodation type
                raw_acc_type = request_data.get("preferred_accommodation_type")
                pref_acc = (
                    AccommodationType(raw_acc_type.upper()) if raw_acc_type else None
                )

                criteria = VacationSearchCriteria(
                    origin_location_name=origin,
                    destination_location_name=destination,
                    date_range=date_range,
                    maximum_budget=max_budget,
                    allowed_transport_types=allowed_types,
                    preferred_accommodation_type=pref_acc,
                    number_of_travelers=travelers,
                )

                packages = self.aggregator_service.generate_vacation_packages(criteria)
                serialized_packages = [
                    self.dto_mapper.map_vacation_package_to_dto(pkg) for pkg in packages
                ]

                self._respond_json(
                    200,
                    {
                        "search_criteria": {
                            "origin": origin,
                            "destination": destination,
                            "date_range": str(date_range),
                            "travelers": travelers,
                            "budget": str(max_budget),
                        },
                        "total_results": len(serialized_packages),
                        "packages": serialized_packages,
                    },
                )
            except Exception as exception:
                self._respond_json(400, {"error": str(exception)})
            return

        self._respond_json(404, {"error": "Endpoint not found."})

    def _respond_json(self, status_code: int, data: Any) -> None:
        """Sends a JSON response with proper CORS and headers."""
        response_bytes = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status_code)
        self._send_cors_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(response_bytes)))
        self.end_headers()
        self.wfile.write(response_bytes)

    def _send_cors_headers(self) -> None:
        """Injects CORS headers so frontend applications can communicate seamlessly."""
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

    def log_message(self, format: str, *args: Any) -> None:
        """Suppresses default stderr logging during automated testing."""
        pass
