from __future__ import annotations

import unittest
from src.vacation_planner.entrypoints.gui.DashboardApplicationContext import (
    DashboardApplicationContext,
)
from src.vacation_planner.entrypoints.gui.DashboardViewInterface import DashboardViewInterface
from src.vacation_planner.entrypoints.gui.DashboardViewRegistry import DashboardViewRegistry
from src.vacation_planner.entrypoints.gui.VacationPlannerDashboardApplication import (
    VacationPlannerDashboardApplication,
)


class TestDashboardGui(unittest.TestCase):
    def setUp(self) -> None:
        self.context = DashboardApplicationContext()
        self.registry = DashboardViewRegistry()

    def test_view_auto_discovery(self) -> None:
        views = self.registry.discover_and_register_views()
        self.assertGreaterEqual(len(views), 5)

        # Check view IDs
        view_ids = [v.get_view_identifier() for v in views]
        self.assertIn("vacation_package_planner", view_ids)
        self.assertIn("transport_explorer", view_ids)
        self.assertIn("accommodation_explorer", view_ids)
        self.assertIn("location_attractions", view_ids)
        self.assertIn("saved_packages_inspector", view_ids)

        # Ensure unique IDs
        self.assertEqual(len(view_ids), len(set(view_ids)))

        # Ensure correct sort ordering
        sort_orders = [v.get_sort_order() for v in views]
        self.assertEqual(sort_orders, sorted(sort_orders))

    def test_dashboard_window_creation(self) -> None:
        app = VacationPlannerDashboardApplication(
            application_context=self.context,
            view_registry=self.registry,
        )
        root = app.create_window()
        self.assertIsNotNone(root)
        self.assertIn("Reiseplaner Dashboard", root.title())

        # Verify notebook tabs count
        self.assertIsNotNone(app._notebook)
        tabs_count = len(app._notebook.tabs())
        self.assertGreaterEqual(tabs_count, 5)

        # Cleanly destroy window after test
        root.destroy()


if __name__ == "__main__":
    unittest.main()
