from __future__ import annotations

import threading
from src.vacation_planner.core.domain.models.VacationPackage import VacationPackage
from src.vacation_planner.core.interfaces.PackageRepositoryInterface import (
    PackageRepositoryInterface,
)


class InMemoryPackageRepository(PackageRepositoryInterface):
    """
    Thread-safe in-memory persistence adapter implementing PackageRepositoryInterface.
    Provides storage and fast indexed lookup for generated vacation packages.
    """

    def __init__(self) -> None:
        self._storage: dict[str, VacationPackage] = {}
        self._lock: threading.RLock = threading.RLock()

    def save_vacation_package(self, vacation_package: VacationPackage) -> None:
        """
        Stores the given vacation package. Overwrites if identical identifier already exists.
        """
        with self._lock:
            self._storage[vacation_package.package_id] = vacation_package

    def get_vacation_package_by_id(self, vacation_package_id: str) -> VacationPackage | None:
        """
        Retrieves a vacation package by ID, returning None if not found.
        """
        with self._lock:
            return self._storage.get(vacation_package_id)

    def list_all_vacation_packages(self) -> list[VacationPackage]:
        """
        Returns a list of all persisted vacation packages.
        """
        with self._lock:
            return list(self._storage.values())

    def clear(self) -> None:
        """
        Utility method to reset the in-memory repository (convenient for test fixtures).
        """
        with self._lock:
            self._storage.clear()
