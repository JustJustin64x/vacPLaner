from __future__ import annotations

import os
import tkinter as tk
from tkinter import ttk
from src.vacation_planner.entrypoints.gui.DashboardApplicationContext import (
    DashboardApplicationContext,
)
from src.vacation_planner.entrypoints.gui.DashboardViewRegistry import DashboardViewRegistry


class VacationPlannerDashboardApplication:
    """
    Main Visual Dashboard Application window.
    Constructs the desktop GUI, discovers and dynamically mounts all registered
    dashboard views into a tabbed interface, and manages the application event loop.
    """

    def __init__(
        self,
        application_context: DashboardApplicationContext | None = None,
        view_registry: DashboardViewRegistry | None = None,
    ) -> None:
        # Suppress macOS Tk 8.5 deprecation warning in terminal
        os.environ["TK_SILENCE_DEPRECATION"] = "1"

        self._context: DashboardApplicationContext = (
            application_context or DashboardApplicationContext()
        )
        self._registry: DashboardViewRegistry = (
            view_registry or DashboardViewRegistry()
        )
        self._root: tk.Tk | None = None
        self._notebook: ttk.Notebook | None = None
        self._status_bar_var: tk.StringVar | None = None

    def create_window(self) -> tk.Tk:
        """
        Creates and configures the Tkinter root window and mounts all views.
        """
        self._root = tk.Tk()
        self._root.title("Modulares Urlaubsplanungs-Tool — Reiseplaner Dashboard")
        self._root.geometry("1180x800")
        self._root.minsize(980, 650)

        self._status_bar_var = tk.StringVar(
            master=self._root, value="Bereit | Clean Architecture Backend aktiv"
        )

        # Apply clean theme
        style = ttk.Style(self._root)
        available_themes = style.theme_names()
        if "aqua" in available_themes:
            style.theme_use("aqua")
        elif "clam" in available_themes:
            style.theme_use("clam")

        self._root.columnconfigure(0, weight=1)
        self._root.rowconfigure(1, weight=1)

        # 1. Top Header Banner
        header_frame = ttk.Frame(self._root, padding="10")
        header_frame.grid(row=0, column=0, sticky="ew")
        header_frame.columnconfigure(0, weight=1)

        title_label = ttk.Label(
            header_frame,
            text="🌍 Modulares Urlaubsplanungs-Tool",
            font=("Helvetica", 16, "bold"),
        )
        title_label.grid(row=0, column=0, sticky="w")

        subtitle_label = ttk.Label(
            header_frame,
            text="Clean Architecture Reiseplanungs-Aggregator: Flüge, Bahn, Pkw & Unterkünfte",
            font=("Helvetica", 10),
        )
        subtitle_label.grid(row=1, column=0, sticky="w")

        # 2. Main Tabbed Notebook Container
        self._notebook = ttk.Notebook(self._root)
        self._notebook.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 5))

        # Dynamically discover and mount all view components
        discovered_views = self._registry.discover_and_register_views()

        for view in discovered_views:
            view_widget = view.build_view_component(
                parent_container=self._notebook,
                application_context=self._context,
            )
            self._notebook.add(view_widget, text=view.get_display_title())

        self._notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

        # 3. Bottom Status Bar
        status_frame = ttk.Frame(self._root, relief="sunken", padding="4")
        status_frame.grid(row=2, column=0, sticky="ew")
        status_frame.columnconfigure(0, weight=1)

        status_label = ttk.Label(
            status_frame,
            textvariable=self._status_bar_var,
            font=("Helvetica", 9),
        )
        status_label.grid(row=0, column=0, sticky="w")

        modules_count_label = ttk.Label(
            status_frame,
            text=f"Aktive Module: {len(discovered_views)} | Status: Verbunden",
            font=("Helvetica", 9),
        )
        modules_count_label.grid(row=0, column=1, sticky="e")

        return self._root

    def _on_tab_changed(self, event: tk.Event) -> None:
        """Invoked when switching between tabs."""
        if not self._notebook:
            return
        current_tab_index = self._notebook.index(self._notebook.select())
        views = self._registry.get_registered_views()
        if 0 <= current_tab_index < len(views):
            active_view = views[current_tab_index]
            active_view.refresh_view()
            if self._status_bar_var:
                self._status_bar_var.set(
                    f"Aktives Modul: {active_view.get_display_title()} | Modul-ID: {active_view.get_view_identifier()}"
                )

    def start_dashboard(self) -> None:
        """
        Initializes and runs the graphical dashboard main loop.
        """
        root = self.create_window()
        root.mainloop()
