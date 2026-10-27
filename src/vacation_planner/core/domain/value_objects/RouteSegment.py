from datetime import datetime
from typing import Any


class RouteSegment:
    """
    Immutable value object representing an individual connected leg or segment
    of a broader passenger travel route.
    """

    __slots__ = (
        "_departure_station_or_airport",
        "_arrival_station_or_airport",
        "_departure_time",
        "_arrival_time",
        "_duration_in_minutes",
        "_carrier_or_operator_name",
        "_segment_identifier",
    )

    def __init__(
        self,
        departure_station_or_airport: str,
        arrival_station_or_airport: str,
        departure_time: datetime,
        arrival_time: datetime,
        carrier_or_operator_name: str,
        segment_identifier: str,
    ) -> None:
        if departure_time >= arrival_time:
            raise ValueError(
                f"Invalid travel times: departure_time ({departure_time}) must precede arrival_time ({arrival_time})."
            )

        duration_seconds = (arrival_time - departure_time).total_seconds()
        duration_minutes = int(duration_seconds // 60)

        object.__setattr__(
            self, "_departure_station_or_airport", departure_station_or_airport.strip()
        )
        object.__setattr__(
            self, "_arrival_station_or_airport", arrival_station_or_airport.strip()
        )
        object.__setattr__(self, "_departure_time", departure_time)
        object.__setattr__(self, "_arrival_time", arrival_time)
        object.__setattr__(self, "_duration_in_minutes", duration_minutes)
        object.__setattr__(
            self, "_carrier_or_operator_name", carrier_or_operator_name.strip()
        )
        object.__setattr__(self, "_segment_identifier", segment_identifier.strip())

    @property
    def departure_station_or_airport(self) -> str:
        return self._departure_station_or_airport

    @property
    def arrival_station_or_airport(self) -> str:
        return self._arrival_station_or_airport

    @property
    def departure_time(self) -> datetime:
        return self._departure_time

    @property
    def arrival_time(self) -> datetime:
        return self._arrival_time

    @property
    def duration_in_minutes(self) -> int:
        return self._duration_in_minutes

    @property
    def carrier_or_operator_name(self) -> str:
        return self._carrier_or_operator_name

    @property
    def segment_identifier(self) -> str:
        return self._segment_identifier

    def __setattr__(self, key: str, value: Any) -> None:
        raise AttributeError("RouteSegment instances are immutable.")

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, RouteSegment):
            return False
        return (
            self._departure_station_or_airport == other.departure_station_or_airport
            and self._arrival_station_or_airport == other.arrival_station_or_airport
            and self._departure_time == other.departure_time
            and self._arrival_time == other.arrival_time
            and self._segment_identifier == other.segment_identifier
        )

    def __repr__(self) -> str:
        return (
            f"RouteSegment(from='{self._departure_station_or_airport}', "
            f"to='{self._arrival_station_or_airport}', "
            f"carrier='{self._carrier_or_operator_name}', "
            f"identifier='{self._segment_identifier}', "
            f"duration_minutes={self._duration_in_minutes})"
        )
