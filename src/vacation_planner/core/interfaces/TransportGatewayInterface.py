from abc import ABC, abstractmethod
from datetime import date
from typing import Sequence
from src.vacation_planner.core.domain.models.Location import Location
from src.vacation_planner.core.domain.models.TransportOption import TransportOption
from src.vacation_planner.core.domain.value_objects.TransportType import TransportType


class TransportGatewayInterface(ABC):
    """
    Port interface defining the contract for retrieving passenger transport alternatives
    (flights, train routes, car connections) between two geographic locations.
    """

    @abstractmethod
    def search_transport_options(
        self,
        origin_location: Location,
        destination_location: Location,
        travel_date: date,
        allowed_transport_types: Sequence[TransportType],
        number_of_passengers: int,
    ) -> list[TransportOption]:
        """
        Searches and returns all available transport options matching the criteria.
        """
        pass
