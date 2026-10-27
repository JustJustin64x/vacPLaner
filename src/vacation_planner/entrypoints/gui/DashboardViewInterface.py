from __future__ import annotations

from abc import ABC, abstractmethod
import tkinter as tk
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.vacation_planner.entrypoints.gui.DashboardApplicationContext import (
        DashboardApplicationContext,
    )


class DashboardViewInterface(ABC):
    """
    Abstract interface contract defining a pluggable dashboard view or tab component.
    Any new domain module or roadmap feature can implement this contract to be
    automatically integrated into the dashboard window without modifying core application code.
    """

    @abstractmethod
    def get_view_identifier(self) -> str:
        """Unique machine-readable identifier for the dashboard view."""
        pass

    @abstractmethod
    def get_display_title(self) -> str:
        """Human-readable title displayed on the dashboard tab or navigation button."""
        pass

    @abstractmethod
    def get_sort_order(self) -> int:
        """Determines the tab ordering position in the dashboard (ascending order)."""
        pass

    @abstractmethod
    def build_view_component(
        self,
        parent_container: tk.Widget,
        application_context: DashboardApplicationContext,
    ) -> tk.Widget:
        """
        Constructs and returns the root Tkinter widget or frame for this view.
        """
        pass

    @abstractmethod
    def refresh_view(self) -> None:
        """
        Triggered when the view becomes active or when global application state is updated.
        """
        pass
