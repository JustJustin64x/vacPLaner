from enum import Enum


class AccommodationType(str, Enum):
    """
    Defines the structural categories of accommodations available for travelers,
    ranging from full-service hotels to self-catering vacation apartments.
    """
    HOTEL = "HOTEL"
    APARTMENT = "APARTMENT"
    HOSTEL = "HOSTEL"
    RESORT = "RESORT"

    def __str__(self) -> str:
        return self.value
