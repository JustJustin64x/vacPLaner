from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
from typing import TYPE_CHECKING
from src.vacation_planner.core.domain.models.Attraction import Attraction
from src.vacation_planner.core.domain.models.Location import Location
from src.vacation_planner.entrypoints.gui.DashboardViewInterface import DashboardViewInterface

if TYPE_CHECKING:
    from src.vacation_planner.entrypoints.gui.DashboardApplicationContext import (
        DashboardApplicationContext,
    )


class LocationAttractionsDashboardView(DashboardViewInterface):
    """
    Dashboard view for the Location & Attractions Module.
    Enables users to examine geodata, city profiles, and local tourist attractions.
    """

    def __init__(self) -> None:
        self._context: DashboardApplicationContext | None = None
        self._current_location: Location | None = None
        self._attractions: list[Attraction] = []

        self._city_var: tk.StringVar | None = None
        self._city_info_var: tk.StringVar | None = None

        self._tree: ttk.Treeview | None = None
        self._detail_text: tk.Text | None = None

    def get_view_identifier(self) -> str:
        return "location_attractions"

    def get_display_title(self) -> str:
        return "📍 Lokations- & Attraktionen-Modul"

    def get_sort_order(self) -> int:
        return 40

    def build_view_component(
        self,
        parent_container: tk.Widget,
        application_context: DashboardApplicationContext,
    ) -> tk.Widget:
        self._context = application_context

        self._city_var = tk.StringVar(master=parent_container, value="Paris")
        self._city_info_var = tk.StringVar(master=parent_container, value="")

        root_frame = ttk.Frame(parent_container, padding="10")
        root_frame.columnconfigure(0, weight=1)
        root_frame.rowconfigure(1, weight=1)

        # Controls
        ctrl_frame = ttk.LabelFrame(root_frame, text="Stadt / Reiseziel auswählen", padding="12")
        ctrl_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        ctrl_frame.columnconfigure(1, weight=1)

        ttk.Label(ctrl_frame, text="Reiseziel:", style="Card.TLabel").grid(row=0, column=0, sticky="w", padx=4, pady=4)
        city_combo = ttk.Combobox(
            ctrl_frame,
            textvariable=self._city_var,
            values=["Paris", "Berlin", "Rome", "Barcelona", "Vienna", "Amsterdam", "Munich", "Zurich", "London"],
            width=16,
        )
        city_combo.grid(row=0, column=1, sticky="w", padx=4, pady=4)

        ttk.Button(
            ctrl_frame,
            text="🌍 Geodaten & Attraktionen laden",
            command=self._on_load_clicked,
        ).grid(row=0, column=2, sticky="e", padx=4, pady=4)

        ttk.Label(
            ctrl_frame,
            textvariable=self._city_info_var,
            style="Card.TLabel",
            font=("Helvetica", 10, "italic"),
        ).grid(row=1, column=0, columnspan=3, sticky="w", padx=4, pady=4)

        # Paned Window
        paned = ttk.PanedWindow(root_frame, orient="vertical")
        paned.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        table_frame = ttk.Frame(paned)
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        cols = ("id", "name", "category", "fee", "duration", "rating")
        self._tree = ttk.Treeview(table_frame, columns=cols, show="headings", selectmode="browse")
        self._tree.heading("id", text="ID")
        self._tree.heading("name", text="Sehenswürdigkeit")
        self._tree.heading("category", text="Kategorie")
        self._tree.heading("fee", text="Eintritt")
        self._tree.heading("duration", text="Besuchsdauer")
        self._tree.heading("rating", text="Bewertung")

        self._tree.column("id", width=120, anchor="center")
        self._tree.column("name", width=250, anchor="w")
        self._tree.column("category", width=160, anchor="w")
        self._tree.column("fee", width=100, anchor="e")
        self._tree.column("duration", width=100, anchor="center")
        self._tree.column("rating", width=80, anchor="center")

        scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=scroll.set)
        self._tree.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")

        self._tree.bind("<<TreeviewSelect>>", self._on_select)
        paned.add(table_frame, weight=3)

        detail_frame = ttk.LabelFrame(paned, text="Beschreibung & Details", padding="8")
        detail_frame.rowconfigure(0, weight=1)
        detail_frame.columnconfigure(0, weight=1)

        self._detail_text = tk.Text(detail_frame, wrap="word", height=5)
        application_context.theme_manager.style_text_widget(self._detail_text)
        det_scroll = ttk.Scrollbar(detail_frame, orient="vertical", command=self._detail_text.yview)
        self._detail_text.configure(yscrollcommand=det_scroll.set)
        self._detail_text.grid(row=0, column=0, sticky="nsew")
        det_scroll.grid(row=0, column=1, sticky="ns")
        paned.add(detail_frame, weight=2)

        return root_frame

    def _on_load_clicked(self) -> None:
        if not self._context:
            return

        try:
            city_name = self._city_var.get().strip()
            self._current_location = self._context.location_gateway.resolve_location_by_name(city_name)
            self._attractions = self._context.location_gateway.fetch_local_attractions_for_location(
                self._current_location, maximum_results=15
            )
        except Exception as e:
            messagebox.showerror("Fehler", f"Ort konnte nicht geladen werden:\n{e}")
            return

        self._city_info_var.set(
            f"Ort: {self._current_location.name} ({self._current_location.country_name} [{self._current_location.country_code}]) "
            f"| Koordinaten: {self._current_location.coordinates} | {self._current_location.description}"
        )

        if not self._tree or not self._context:
            return

        self._tree.tag_configure("evenrow", background=self._context.theme_manager.COLOR_TREE_EVEN)
        self._tree.tag_configure("oddrow", background=self._context.theme_manager.COLOR_TREE_ODD)

        for item in self._tree.get_children():
            self._tree.delete(item)

        for idx, attr in enumerate(self._attractions):
            fee_str = "Kostenlos" if attr.is_admission_free() else f"{attr.admission_fee.amount:.2f} €"
            row_tag = "evenrow" if idx % 2 == 0 else "oddrow"
            self._tree.insert(
                "",
                "end",
                iid=attr.attraction_id,
                tags=(row_tag,),
                values=(
                    attr.attraction_id,
                    attr.name,
                    attr.category,
                    fee_str,
                    f"{attr.estimated_visit_duration_in_minutes} Min.",
                    f"{attr.user_rating} ★",
                ),
            )

    def _on_select(self, event: tk.Event) -> None:
        if not self._tree or not self._detail_text:
            return
        selected = self._tree.selection()
        if not selected:
            return
        attr_id = selected[0]
        attr = next((a for a in self._attractions if a.attraction_id == attr_id), None)
        if not attr:
            return

        self._detail_text.delete("1.0", tk.END)
        fee_str = "Kostenfrei" if attr.is_admission_free() else str(attr.admission_fee)
        lines = [
            f"Sehenswürdigkeit: {attr.name} [{attr.category}]",
            f"Standort:         {attr.location_name} | Koordinaten: {attr.coordinates}",
            f"Eintrittspreis:   {fee_str} | Empfohlene Besuchsdauer: {attr.estimated_visit_duration_in_minutes} Minuten",
            f"Bewertung:        {attr.user_rating} von 5.0 Sternen",
            f"",
            f"Beschreibung:",
            f"  {attr.description}",
        ]
        self._detail_text.insert("1.0", "\n".join(lines))

    def refresh_view(self) -> None:
        pass
