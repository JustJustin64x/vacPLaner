from __future__ import annotations

from abc import ABC, abstractmethod
from src.vacation_planner.core.domain.models.VacationPackage import VacationPackage


class PackageRepositoryInterface(ABC):
    """
    Port interface defining persistence operations for vacation packages.
    """

    @abstractmethod
    def save_vacation_package(self, vacation_package: VacationPackage) -> None:
        """
        Persists a vacation package into the storage layer.
        """
        pass

    @abstractmethod
    def get_vacation_package_by_id(self, vacation_package_id: str) -> VacationPackage | None:
        """
        Retrieves a persisted vacation package by its unique identifier, or returns None if not found.
        """
        pass

    @abstractmethod
    def list_all_vacation_packages(self) -> list[VacationPackage]:
        """
        Lists all stored vacation packages.
        """
        pass
