from __future__ import annotations

from datetime import date
from typing import Sequence
from src.vacation_planner.core.domain.models.Location import Location
from src.vacation_planner.core.domain.models.TransportOption import TransportOption
from src.vacation_planner.core.domain.value_objects.TransportType import TransportType
from src.vacation_planner.core.interfaces.TransportGatewayInterface import (
    TransportGatewayInterface,
)
from src.vacation_planner.infrastructure.adapters.transport.CarRouteTransportAdapter import (
    CarRouteTransportAdapter,
)
from src.vacation_planner.infrastructure.adapters.transport.FlightTransportAdapter import (
    FlightTransportAdapter,
)
from src.vacation_planner.infrastructure.adapters.transport.TrainTransportAdapter import (
    TrainTransportAdapter,
)


class CompositeTransportAdapter(TransportGatewayInterface):
    """
    Composite adapter implementing TransportGatewayInterface. Dispatches queries to
    the specialized Flight, Train, and Car route adapters based on the requested transport types.
    """

    def __init__(
        self,
        flight_adapter: FlightTransportAdapter | None = None,
        train_adapter: TrainTransportAdapter | None = None,
        car_adapter: CarRouteTransportAdapter | None = None,
    ) -> None:
        self._flight_adapter: FlightTransportAdapter = flight_adapter or FlightTransportAdapter()
        self._train_adapter: TrainTransportAdapter = train_adapter or TrainTransportAdapter()
        self._car_adapter: CarRouteTransportAdapter = car_adapter or CarRouteTransportAdapter()

    def search_transport_options(
        self,
        origin_location: Location,
        destination_location: Location,
        travel_date: date,
        allowed_transport_types: Sequence[TransportType],
        number_of_passengers: int,
    ) -> list[TransportOption]:
        """
        Gathers and aggregates transport alternatives across all requested modalities.
        """
        combined_results: list[TransportOption] = []

        if TransportType.FLIGHT in allowed_transport_types:
            flights = self._flight_adapter.find_flights(
                origin_location=origin_location,
                destination_location=destination_location,
                travel_date=travel_date,
                number_of_passengers=number_of_passengers,
            )
            combined_results.extend(flights)

        if TransportType.TRAIN in allowed_transport_types:
            trains = self._train_adapter.find_trains(
                origin_location=origin_location,
                destination_location=destination_location,
                travel_date=travel_date,
                number_of_passengers=number_of_passengers,
            )
            combined_results.extend(trains)

        if TransportType.CAR in allowed_transport_types:
            car_routes = self._car_adapter.find_car_route(
                origin_location=origin_location,
                destination_location=destination_location,
                travel_date=travel_date,
                number_of_passengers=number_of_passengers,
            )
            combined_results.extend(car_routes)

        return combined_results
