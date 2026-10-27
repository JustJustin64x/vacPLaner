from typing import Sequence
from src.vacation_planner.core.domain.models.AccommodationOption import AccommodationOption
from src.vacation_planner.core.domain.models.Attraction import Attraction
from src.vacation_planner.core.domain.models.Location import Location
from src.vacation_planner.core.domain.models.TransportOption import TransportOption
from src.vacation_planner.core.domain.value_objects.DateRange import DateRange
from src.vacation_planner.core.domain.value_objects.MonetaryAmount import MonetaryAmount


class VacationPackage:
    """
    Domain aggregate root representing a complete, synchronized vacation package.
    Combines origin and destination locations, date range, outbound and return transportation,
    accommodation, recommended attractions, and the total cost validation status.
    """

    def __init__(
        self,
        package_id: str,
        origin_location: Location,
        destination_location: Location,
        date_range: DateRange,
        outbound_transport_option: TransportOption,
        return_transport_option: TransportOption,
        accommodation_option: AccommodationOption,
        recommended_attractions: Sequence[Attraction],
        total_package_cost: MonetaryAmount,
        is_within_budget: bool,
        validation_notes: Sequence[str] = (),
    ) -> None:
        if not package_id.strip():
            raise ValueError("Vacation package identifier cannot be empty.")

        self._package_id: str = package_id.strip()
        self._origin_location: Location = origin_location
        self._destination_location: Location = destination_location
        self._date_range: DateRange = date_range
        self._outbound_transport_option: TransportOption = outbound_transport_option
        self._return_transport_option: TransportOption = return_transport_option
        self._accommodation_option: AccommodationOption = accommodation_option
        self._recommended_attractions: tuple[Attraction, ...] = tuple(recommended_attractions)
        self._total_package_cost: MonetaryAmount = total_package_cost
        self._is_within_budget: bool = is_within_budget
        self._validation_notes: tuple[str, ...] = tuple(validation_notes)

    @property
    def package_id(self) -> str:
        return self._package_id

    @property
    def origin_location(self) -> Location:
        return self._origin_location

    @property
    def destination_location(self) -> Location:
        return self._destination_location

    @property
    def date_range(self) -> DateRange:
        return self._date_range

    @property
    def outbound_transport_option(self) -> TransportOption:
        return self._outbound_transport_option

    @property
    def return_transport_option(self) -> TransportOption:
        return self._return_transport_option

    @property
    def accommodation_option(self) -> AccommodationOption:
        return self._accommodation_option

    @property
    def recommended_attractions(self) -> tuple[Attraction, ...]:
        return self._recommended_attractions

    @property
    def total_package_cost(self) -> MonetaryAmount:
        return self._total_package_cost

    @property
    def is_within_budget(self) -> bool:
        return self._is_within_budget

    @property
    def validation_notes(self) -> tuple[str, ...]:
        return self._validation_notes

    def calculate_total_carbon_dioxide_emission_in_kilograms(self) -> float:
        return round(
            self._outbound_transport_option.carbon_dioxide_emission_in_kilograms
            + self._return_transport_option.carbon_dioxide_emission_in_kilograms,
            2,
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, VacationPackage):
            return False
        return self._package_id == other.package_id

    def __repr__(self) -> str:
        return (
            f"VacationPackage(id='{self._package_id}', origin='{self._origin_location.name}', "
            f"destination='{self._destination_location.name}', dates={self._date_range}, "
            f"total_cost={self._total_package_cost}, valid_budget={self._is_within_budget})"
        )

