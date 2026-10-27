from src.vacation_planner.core.domain.models.VacationPackage import VacationPackage
from src.vacation_planner.core.interfaces.PackageRepositoryInterface import (
    PackageRepositoryInterface,
)


class GetVacationPackageDetailsUseCase:
    """
    Use case responsible for retrieving details of a previously generated
    and persisted vacation package by its unique identifier.
    """

    def __init__(self, package_repository: PackageRepositoryInterface) -> None:
        self._package_repository: PackageRepositoryInterface = package_repository

    def execute(self, vacation_package_id: str) -> VacationPackage:
        """
        Retrieves the vacation package. Raises KeyError if the package is not found.
        """
        package = self._package_repository.get_vacation_package_by_id(vacation_package_id)
        if package is None:
            raise KeyError(f"Vacation package with identifier '{vacation_package_id}' not found.")
        return package
