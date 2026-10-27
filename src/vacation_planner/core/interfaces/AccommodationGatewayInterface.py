from __future__ import annotations

from abc import ABC, abstractmethod
from src.vacation_planner.core.domain.models.AccommodationOption import AccommodationOption
from src.vacation_planner.core.domain.models.Location import Location
from src.vacation_planner.core.domain.value_objects.AccommodationType import AccommodationType
from src.vacation_planner.core.domain.value_objects.DateRange import DateRange


class AccommodationGatewayInterface(ABC):
    """
    Port interface defining the contract for querying lodging and hotel options
    at a specific destination for a requested date range.
    """

    @abstractmethod
    def search_accommodation_options(
        self,
        destination_location: Location,
        date_range: DateRange,
        number_of_guests: int,
        preferred_accommodation_type: AccommodationType | None = None,
    ) -> list[AccommodationOption]:
        """
        Queries and returns available accommodation options that match the search criteria.
        """
        pass
