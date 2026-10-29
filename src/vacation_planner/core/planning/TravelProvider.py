from typing import Protocol


class TravelProvider(Protocol):
    """Infrastructure returns identities, evidence and unknowns, never fabricated offers.

    lodging/activities: id, name, source, retrieved_at, latitude/longitude,
    amenities (true/false/null), price (CostItem dict), booking_status.
    route: two directional legs with distance (metres) and duration (seconds).
    """
    def places(self, destination, context): ...
    def route(self, origin, destination, context): ...
    def origin(self, name, address, context): ...
    def research_offers(self, trip, context, emit, categories=None): ...
