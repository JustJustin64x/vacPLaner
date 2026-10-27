from abc import ABC, abstractmethod
from src.vacation_planner.core.domain.models.Attraction import Attraction
from src.vacation_planner.core.domain.models.Location import Location


class LocationGatewayInterface(ABC):
    """
    Port interface defining the contract for geocoding location names into structured
    Location domain entities and querying local tourist sights and attractions.
    """

    @abstractmethod
    def resolve_location_by_name(self, location_name: str) -> Location:
        """
        Resolves a free-text location name (e.g. 'Berlin', 'Paris') into a validated Location domain model.
        Raises an exception if the location cannot be resolved.
        """
        pass

    @abstractmethod
    def fetch_local_attractions_for_location(
        self, destination_location: Location, maximum_results: int = 10
    ) -> list[Attraction]:
        """
        Retrieves cultural, historic, and recreational attractions at or near the given destination.
        """
        pass
