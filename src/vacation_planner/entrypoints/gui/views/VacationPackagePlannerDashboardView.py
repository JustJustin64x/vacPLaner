from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
from typing import TYPE_CHECKING
from src.vacation_planner.core.domain.models.VacationPackage import VacationPackage
from src.vacation_planner.core.domain.models.VacationSearchCriteria import VacationSearchCriteria
from src.vacation_planner.core.domain.value_objects.DateRange import DateRange
from src.vacation_planner.core.domain.value_objects.MonetaryAmount import MonetaryAmount
from src.vacation_planner.core.domain.value_objects.TransportType import TransportType
from src.vacation_planner.entrypoints.gui.DashboardViewInterface import DashboardViewInterface

if TYPE_CHECKING:
    from src.vacation_planner.entrypoints.gui.DashboardApplicationContext import (
        DashboardApplicationContext,
    )


class VacationPackagePlannerDashboardView(DashboardViewInterface):
    """
    Primary dashboard view integrating the Aggregator Service.
    Enables users to specify trip requirements, triggers synchronized package generation,
    and displays structured comparisons and detailed trip breakdowns.
    """

    def __init__(self) -> None:
        self._context: DashboardApplicationContext | None = None
        self._current_packages: list[VacationPackage] = []
        self._tree: ttk.Treeview | None = None
        self._detail_text: tk.Text | None = None

        # Form variables (initialized lazily when widget tree is built)
        self._origin_var: tk.StringVar | None = None
        self._destination_var: tk.StringVar | None = None
        self._start_date_var: tk.StringVar | None = None
        self._end_date_var: tk.StringVar | None = None
        self._budget_var: tk.StringVar | None = None
        self._travelers_var: tk.StringVar | None = None

        self._allow_flight_var: tk.BooleanVar | None = None
        self._allow_train_var: tk.BooleanVar | None = None
        self._allow_car_var: tk.BooleanVar | None = None

    def get_view_identifier(self) -> str:
        return "vacation_package_planner"

    def get_display_title(self) -> str:
        return "✈️ Urlaubsplaner & Pakete"

    def get_sort_order(self) -> int:
        return 10

    def build_view_component(
        self,
        parent_container: tk.Widget,
        application_context: DashboardApplicationContext,
    ) -> tk.Widget:
        self._context = application_context

        # Initialize Tkinter variables bound to the parent widget
        self._origin_var = tk.StringVar(master=parent_container, value="Berlin")
        self._destination_var = tk.StringVar(master=parent_container, value="Paris")
        self._start_date_var = tk.StringVar(master=parent_container, value="2026-07-01")
        self._end_date_var = tk.StringVar(master=parent_container, value="2026-07-07")
        self._budget_var = tk.StringVar(master=parent_container, value="1500")
        self._travelers_var = tk.StringVar(master=parent_container, value="2")

        self._allow_flight_var = tk.BooleanVar(master=parent_container, value=True)
        self._allow_train_var = tk.BooleanVar(master=parent_container, value=True)
        self._allow_car_var = tk.BooleanVar(master=parent_container, value=True)

        root_frame = ttk.Frame(parent_container, padding="10")
        root_frame.columnconfigure(0, weight=1)
        root_frame.rowconfigure(1, weight=1)

        # 1. Search Criteria Input Box
        criteria_frame = ttk.LabelFrame(root_frame, text="Reisekriterien & Budget-Vorgaben", padding="12")
        criteria_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        for i in range(6):
            criteria_frame.columnconfigure(i, weight=1)

        # Row 0: Cities and dates
        ttk.Label(criteria_frame, text="Startort:", style="Card.TLabel").grid(row=0, column=0, sticky="w", padx=4, pady=4)
        origin_combo = ttk.Combobox(
            criteria_frame,
            textvariable=self._origin_var,
            values=["Berlin", "Paris", "Rome", "Barcelona", "Vienna", "Amsterdam", "Munich", "Zurich", "London"],
            width=14,
        )
        origin_combo.grid(row=0, column=1, sticky="ew", padx=4, pady=4)

        ttk.Label(criteria_frame, text="Zielort:", style="Card.TLabel").grid(row=0, column=2, sticky="w", padx=4, pady=4)
        dest_combo = ttk.Combobox(
            criteria_frame,
            textvariable=self._destination_var,
            values=["Paris", "Berlin", "Rome", "Barcelona", "Vienna", "Amsterdam", "Munich", "Zurich", "London"],
            width=14,
        )
        dest_combo.grid(row=0, column=3, sticky="ew", padx=4, pady=4)

        ttk.Label(criteria_frame, text="Reisende:", style="Card.TLabel").grid(row=0, column=4, sticky="w", padx=4, pady=4)
        ttk.Spinbox(criteria_frame, from_=1, to=10, textvariable=self._travelers_var, width=5).grid(
            row=0, column=5, sticky="w", padx=4, pady=4
        )

        # Row 1: Dates and Budget
        ttk.Label(criteria_frame, text="Hinreise (JJJJ-MM-TT):", style="Card.TLabel").grid(row=1, column=0, sticky="w", padx=4, pady=4)
        ttk.Entry(criteria_frame, textvariable=self._start_date_var, width=14).grid(
            row=1, column=1, sticky="ew", padx=4, pady=4
        )

        ttk.Label(criteria_frame, text="Rückreise (JJJJ-MM-TT):", style="Card.TLabel").grid(row=1, column=2, sticky="w", padx=4, pady=4)
        ttk.Entry(criteria_frame, textvariable=self._end_date_var, width=14).grid(
            row=1, column=3, sticky="ew", padx=4, pady=4
        )

        ttk.Label(criteria_frame, text="Max. Budget (€):", style="Card.TLabel").grid(row=1, column=4, sticky="w", padx=4, pady=4)
        ttk.Entry(criteria_frame, textvariable=self._budget_var, width=8).grid(
            row=1, column=5, sticky="w", padx=4, pady=4
        )

        # Row 2: Transport checkboxes and Search button
        transport_frame = ttk.Frame(criteria_frame, style="Card.TFrame")
        transport_frame.grid(row=2, column=0, columnspan=4, sticky="w", pady=6)
        ttk.Label(transport_frame, text="Verkehrsmittel:", style="Card.TLabel").pack(side="left", padx=(0, 8))
        ttk.Checkbutton(transport_frame, text="Flug", variable=self._allow_flight_var).pack(side="left", padx=5)
        ttk.Checkbutton(transport_frame, text="Bahn", variable=self._allow_train_var).pack(side="left", padx=5)
        ttk.Checkbutton(transport_frame, text="Auto (Pkw)", variable=self._allow_car_var).pack(side="left", padx=5)

        search_button = ttk.Button(
            criteria_frame,
            text="🔍 Urlaubspakete generieren & synchronisieren",
            command=self._on_search_clicked,
        )
        search_button.grid(row=2, column=4, columnspan=2, sticky="e", padx=4, pady=6)

        # 2. Main split view: Results Table (Top/Left) & Detail Panel (Bottom/Right)
        paned_window = ttk.PanedWindow(root_frame, orient="vertical")
        paned_window.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        # Upper Table Frame
        table_frame = ttk.Frame(paned_window)
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        columns = (
            "id",
            "status",
            "total_cost",
            "co2",
            "outbound",
            "return",
            "accommodation",
            "rating",
        )
        self._tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")
        self._tree.heading("id", text="Paket-ID")
        self._tree.heading("status", text="Budget-Status")
        self._tree.heading("total_cost", text="Gesamtkosten")
        self._tree.heading("co2", text="CO2 (kg)")
        self._tree.heading("outbound", text="Hinreise")
        self._tree.heading("return", text="Rückreise")
        self._tree.heading("accommodation", text="Unterkunft")
        self._tree.heading("rating", text="Bewertung")

        self._tree.column("id", width=120, anchor="center")
        self._tree.column("status", width=120, anchor="center")
        self._tree.column("total_cost", width=110, anchor="e")
        self._tree.column("co2", width=80, anchor="center")
        self._tree.column("outbound", width=130, anchor="w")
        self._tree.column("return", width=130, anchor="w")
        self._tree.column("accommodation", width=190, anchor="w")
        self._tree.column("rating", width=70, anchor="center")

        tree_scroll_y = ttk.Scrollbar(table_frame, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=tree_scroll_y.set)

        self._tree.grid(row=0, column=0, sticky="nsew")
        tree_scroll_y.grid(row=0, column=1, sticky="ns")

        self._tree.bind("<<TreeviewSelect>>", self._on_package_selected)
        paned_window.add(table_frame, weight=3)

        # Lower Detail Panel
        detail_frame = ttk.LabelFrame(paned_window, text="Paket-Details & Reiseplan", padding="8")
        detail_frame.rowconfigure(0, weight=1)
        detail_frame.columnconfigure(0, weight=1)

        self._detail_text = tk.Text(detail_frame, wrap="word", height=8)
        application_context.theme_manager.style_text_widget(self._detail_text)
        detail_scroll = ttk.Scrollbar(detail_frame, orient="vertical", command=self._detail_text.yview)
        self._detail_text.configure(yscrollcommand=detail_scroll.set)

        self._detail_text.grid(row=0, column=0, sticky="nsew")
        detail_scroll.grid(row=0, column=1, sticky="ns")
        paned_window.add(detail_frame, weight=2)

        return root_frame

    def _on_search_clicked(self) -> None:
        if not self._context:
            return

        # Validate inputs
        try:
            budget_val = float(self._budget_var.get())
            travelers_val = int(self._travelers_var.get())
            date_range = DateRange(self._start_date_var.get().strip(), self._end_date_var.get().strip())
        except Exception as e:
            messagebox.showerror("Ungültige Eingabe", f"Bitte Eingabedaten prüfen:\n{e}")
            return

        allowed_types: list[TransportType] = []
        if self._allow_flight_var.get():
            allowed_types.append(TransportType.FLIGHT)
        if self._allow_train_var.get():
            allowed_types.append(TransportType.TRAIN)
        if self._allow_car_var.get():
            allowed_types.append(TransportType.CAR)

        if not allowed_types:
            messagebox.showwarning("Hinweis", "Bitte wählen Sie mindestens ein Verkehrsmittel aus.")
            return

        criteria = VacationSearchCriteria(
            origin_location_name=self._origin_var.get().strip(),
            destination_location_name=self._destination_var.get().strip(),
            date_range=date_range,
            maximum_budget=MonetaryAmount(budget_val, "EUR"),
            allowed_transport_types=allowed_types,
            number_of_travelers=travelers_val,
        )

        try:
            self._current_packages = self._context.aggregator_service.generate_vacation_packages(criteria)
            self._render_packages_table()
        except Exception as search_error:
            messagebox.showerror("Fehler bei der Paketsuche", str(search_error))

    def _render_packages_table(self) -> None:
        if not self._tree or not self._context:
            return

        self._tree.tag_configure("evenrow", background=self._context.theme_manager.COLOR_TREE_EVEN)
        self._tree.tag_configure("oddrow", background=self._context.theme_manager.COLOR_TREE_ODD)

        # Clear existing items
        for item in self._tree.get_children():
            self._tree.delete(item)

        for index, pkg in enumerate(self._current_packages):
            status_text = "✓ Im Budget" if pkg.is_within_budget else "✗ Budget überschritten"
            outbound_desc = f"{pkg.outbound_transport_option.transport_type.value} ({pkg.outbound_transport_option.segments[0].carrier_or_operator_name})"
            return_desc = f"{pkg.return_transport_option.transport_type.value} ({pkg.return_transport_option.segments[0].carrier_or_operator_name})"
            row_tag = "evenrow" if index % 2 == 0 else "oddrow"

            item_id = self._tree.insert(
                "",
                "end",
                iid=pkg.package_id,
                tags=(row_tag,),
                values=(
                    pkg.package_id,
                    status_text,
                    f"{pkg.total_package_cost.amount:.2f} €",
                    f"{pkg.calculate_total_carbon_dioxide_emission_in_kilograms():.1f}",
                    outbound_desc,
                    return_desc,
                    pkg.accommodation_option.name,
                    f"{pkg.accommodation_option.star_rating} ★",
                ),
            )

        if self._current_packages and self._tree:
            first_id = self._current_packages[0].package_id
            self._tree.selection_set(first_id)
            self._tree.focus(first_id)

    def _on_package_selected(self, event: tk.Event) -> None:
        if not self._tree or not self._detail_text:
            return

        selected_items = self._tree.selection()
        if not selected_items:
            return

        package_id = selected_items[0]
        package = next((p for p in self._current_packages if p.package_id == package_id), None)
        if not package:
            return

        self._detail_text.delete("1.0", tk.END)

        lines = [
            f"================================================================================",
            f" URLAUBSPAKET: {package.package_id}  |  STATUS: {'✓ IM BUDGET' if package.is_within_budget else '✗ BUDGET ÜBERSCHRITTEN'}",
            f"================================================================================",
            f" • Route:            {package.origin_location.name} -> {package.destination_location.name}",
            f" • Zeitraum:         {package.date_range.start_date} bis {package.date_range.end_date} ({package.date_range.calculate_total_nights()} Übernachtungen)",
            f" • Gesamtkosten:     {package.total_package_cost}  |  CO2-Fußabdruck: {package.calculate_total_carbon_dioxide_emission_in_kilograms()} kg CO2",
            f" • Budget-Prüfung:   {package.validation_notes[0]}",
            f"",
            f" [HINREISE]: {package.outbound_transport_option.transport_type.value} | Preis: {package.outbound_transport_option.total_price}",
            f"   Abfahrt: {package.outbound_transport_option.departure_time.strftime('%Y-%m-%d %H:%M')} ({package.outbound_transport_option.segments[0].departure_station_or_airport})",
            f"   Ankunft: {package.outbound_transport_option.arrival_time.strftime('%Y-%m-%d %H:%M')} ({package.outbound_transport_option.segments[-1].arrival_station_or_airport})",
            f"   Dauer:   {package.outbound_transport_option.calculate_total_duration_in_minutes()} Min. | Umstiege: {package.outbound_transport_option.count_transfers()}",
            f"",
            f" [RÜCKREISE]: {package.return_transport_option.transport_type.value} | Preis: {package.return_transport_option.total_price}",
            f"   Abfahrt: {package.return_transport_option.departure_time.strftime('%Y-%m-%d %H:%M')} ({package.return_transport_option.segments[0].departure_station_or_airport})",
            f"   Ankunft: {package.return_transport_option.arrival_time.strftime('%Y-%m-%d %H:%M')} ({package.return_transport_option.segments[-1].arrival_station_or_airport})",
            f"   Dauer:   {package.return_transport_option.calculate_total_duration_in_minutes()} Min. | Umstiege: {package.return_transport_option.count_transfers()}",
            f"",
            f" [UNTERKUNFT]: {package.accommodation_option.name} ({package.accommodation_option.accommodation_type.value})",
            f"   Adresse:    {package.accommodation_option.address_line}",
            f"   Kategorie:  {package.accommodation_option.star_rating} Sterne",
            f"   Gesamt:     {package.accommodation_option.total_price} ({package.accommodation_option.price_per_night} pro Nacht)",
            f"   Amenities:  {', '.join(package.accommodation_option.included_amenities)}",
            f"",
            f" [EMPFOHLENE SEHENSWÜRDIGKEITEN AM ZIELORT]:",
        ]

        for attr in package.recommended_attractions:
            fee_str = "Kostenlos" if attr.is_admission_free() else str(attr.admission_fee)
            lines.append(
                f"   ★ {attr.name} ({attr.category}) - Eintritt: {fee_str} | Dauer: {attr.estimated_visit_duration_in_minutes} Min. | Rating: {attr.user_rating}★"
            )

        self._detail_text.insert("1.0", "\n".join(lines))

    def refresh_view(self) -> None:
        pass
