from datetime import datetime
from typing import Sequence
from src.vacation_planner.core.domain.value_objects.MonetaryAmount import MonetaryAmount
from src.vacation_planner.core.domain.value_objects.RouteSegment import RouteSegment
from src.vacation_planner.core.domain.value_objects.TransportType import TransportType


class TransportOption:
    """
    Domain entity representing an end-to-end transportation journey between
    an origin and a destination, composed of one or more connected segments.
    """

    def __init__(
        self,
        transport_option_id: str,
        transport_type: TransportType,
        origin_location_name: str,
        destination_location_name: str,
        departure_time: datetime,
        arrival_time: datetime,
        segments: Sequence[RouteSegment],
        total_price: MonetaryAmount,
        carbon_dioxide_emission_in_kilograms: float,
        booking_reference_url: str = "",
    ) -> None:
        if not transport_option_id.strip():
            raise ValueError("Transport option identifier cannot be empty.")
        if departure_time >= arrival_time:
            raise ValueError(
                f"Departure time ({departure_time}) must precede arrival time ({arrival_time})."
            )
        if not segments:
            raise ValueError("A transport option must contain at least one route segment.")

        self._transport_option_id: str = transport_option_id.strip()
        self._transport_type: TransportType = transport_type
        self._origin_location_name: str = origin_location_name.strip()
        self._destination_location_name: str = destination_location_name.strip()
        self._departure_time: datetime = departure_time
        self._arrival_time: datetime = arrival_time
        self._segments: tuple[RouteSegment, ...] = tuple(segments)
        self._total_price: MonetaryAmount = total_price
        self._carbon_dioxide_emission_in_kilograms: float = round(
            carbon_dioxide_emission_in_kilograms, 2
        )
        self._booking_reference_url: str = booking_reference_url.strip()

    @property
    def transport_option_id(self) -> str:
        return self._transport_option_id

    @property
    def transport_type(self) -> TransportType:
        return self._transport_type

    @property
    def origin_location_name(self) -> str:
        return self._origin_location_name

    @property
    def destination_location_name(self) -> str:
        return self._destination_location_name

    @property
    def departure_time(self) -> datetime:
        return self._departure_time

    @property
    def arrival_time(self) -> datetime:
        return self._arrival_time

    @property
    def segments(self) -> tuple[RouteSegment, ...]:
        return self._segments

    @property
    def total_price(self) -> MonetaryAmount:
        return self._total_price

    @property
    def carbon_dioxide_emission_in_kilograms(self) -> float:
        return self._carbon_dioxide_emission_in_kilograms

    @property
    def booking_reference_url(self) -> str:
        return self._booking_reference_url

    def calculate_total_duration_in_minutes(self) -> int:
        return int((self._arrival_time - self._departure_time).total_seconds() // 60)

    def count_transfers(self) -> int:
        return max(0, len(self._segments) - 1)

    def is_direct_connection(self) -> bool:
        return len(self._segments) == 1

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, TransportOption):
            return False
        return self._transport_option_id == other.transport_option_id

    def __repr__(self) -> str:
        return (
            f"TransportOption(id='{self._transport_option_id}', type={self._transport_type}, "
            f"from='{self._origin_location_name}', to='{self._destination_location_name}', "
            f"price={self._total_price}, transfers={self.count_transfers()})"
        )

