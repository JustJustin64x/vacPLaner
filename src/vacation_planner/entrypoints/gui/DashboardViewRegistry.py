from __future__ import annotations

import importlib
import inspect
import os
import pkgutil
from typing import Type
from src.vacation_planner.entrypoints.gui.DashboardViewInterface import DashboardViewInterface


class DashboardViewRegistry:
    """
    Registry and auto-discovery service for dashboard views.
    Automatically scans the 'views' package and instantiates all classes implementing
    DashboardViewInterface, enabling new roadmap features to appear automatically in the UI.
    """

    def __init__(self) -> None:
        self._registered_views: list[DashboardViewInterface] = []

    def register_view(self, view_instance: DashboardViewInterface) -> None:
        """Explicitly registers a view instance."""
        if not any(
            v.get_view_identifier() == view_instance.get_view_identifier()
            for v in self._registered_views
        ):
            self._registered_views.append(view_instance)
            self._registered_views.sort(key=lambda view: view.get_sort_order())

    def discover_and_register_views(self) -> list[DashboardViewInterface]:
        """
        Dynamically discovers all view classes in 'src.vacation_planner.entrypoints.gui.views'
        and instantiates them.
        """
        import src.vacation_planner.entrypoints.gui.views as views_package

        package_path = os.path.dirname(views_package.__file__)
        discovered_classes: list[Type[DashboardViewInterface]] = []

        for _, module_name, is_pkg in pkgutil.iter_modules([package_path]):
            if not is_pkg and not module_name.startswith("__"):
                full_module_name = f"src.vacation_planner.entrypoints.gui.views.{module_name}"
                try:
                    module = importlib.import_module(full_module_name)
                    for attribute_name in dir(module):
                        attribute_val = getattr(module, attribute_name)
                        if (
                            inspect.isclass(attribute_val)
                            and issubclass(attribute_val, DashboardViewInterface)
                            and attribute_val is not DashboardViewInterface
                        ):
                            if attribute_val not in discovered_classes:
                                discovered_classes.append(attribute_val)
                except Exception as import_error:
                    print(f"Warning: could not load dashboard view module '{module_name}': {import_error}")

        for view_class in discovered_classes:
            try:
                view_instance = view_class()
                self.register_view(view_instance)
            except Exception as instantiation_error:
                print(f"Warning: could not instantiate view '{view_class.__name__}': {instantiation_error}")

        return list(self._registered_views)

    def get_registered_views(self) -> list[DashboardViewInterface]:
        """Returns the registered views sorted by sort order."""
        return list(self._registered_views)
