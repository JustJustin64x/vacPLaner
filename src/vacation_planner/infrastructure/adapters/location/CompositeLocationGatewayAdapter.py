from __future__ import annotations

from src.vacation_planner.core.domain.models.Attraction import Attraction
from src.vacation_planner.core.domain.models.Location import Location
from src.vacation_planner.core.interfaces.LocationGatewayInterface import (
    LocationGatewayInterface,
)
from src.vacation_planner.infrastructure.adapters.location.GeographicLocationAdapter import (
    GeographicLocationAdapter,
)
from src.vacation_planner.infrastructure.adapters.location.LocalAttractionAdapter import (
    LocalAttractionAdapter,
)


class CompositeLocationGatewayAdapter(LocationGatewayInterface):
    """
    Composite adapter implementing LocationGatewayInterface.
    Coordinates geographic location resolution and local attraction retrieval.
    """

    def __init__(
        self,
        location_adapter: GeographicLocationAdapter | None = None,
        attraction_adapter: LocalAttractionAdapter | None = None,
    ) -> None:
        self._location_adapter: GeographicLocationAdapter = (
            location_adapter or GeographicLocationAdapter()
        )
        self._attraction_adapter: LocalAttractionAdapter = (
            attraction_adapter or LocalAttractionAdapter()
        )

    def resolve_location_by_name(self, location_name: str) -> Location:
        """
        Delegates location geocoding to GeographicLocationAdapter.
        """
        return self._location_adapter.resolve_location(location_name)

    def fetch_local_attractions_for_location(
        self, destination_location: Location, maximum_results: int = 10
    ) -> list[Attraction]:
        """
        Delegates point-of-interest retrieval to LocalAttractionAdapter.
        """
        return self._attraction_adapter.fetch_attractions(
            destination_location=destination_location,
            maximum_results=maximum_results,
        )
