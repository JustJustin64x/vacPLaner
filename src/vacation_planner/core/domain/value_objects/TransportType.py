from enum import Enum


class TransportType(str, Enum):
    """
    Represents the supported modes of passenger transportation within the travel planner.
    This enumeration is used to categorize transport options such as flights, train rides,
    and automobile routes.
    """
    FLIGHT = "FLIGHT"
    TRAIN = "TRAIN"
    CAR = "CAR"

    def __str__(self) -> str:
        return self.value
