from __future__ import annotations

from datetime import date
import tkinter as tk
from tkinter import ttk, messagebox
from typing import TYPE_CHECKING
from src.vacation_planner.core.domain.models.Location import Location
from src.vacation_planner.core.domain.models.TransportOption import TransportOption
from src.vacation_planner.core.domain.value_objects.TransportType import TransportType
from src.vacation_planner.entrypoints.gui.DashboardViewInterface import DashboardViewInterface

if TYPE_CHECKING:
    from src.vacation_planner.entrypoints.gui.DashboardApplicationContext import (
        DashboardApplicationContext,
    )


class TransportExplorerDashboardView(DashboardViewInterface):
    """
    Dashboard view for the Transport Module.
    Allows isolated comparison of flight, train, and car routing options
    between two destinations, displaying durations, prices, segments, and CO2 emissions.
    """

    def __init__(self) -> None:
        self._context: DashboardApplicationContext | None = None
        self._options: list[TransportOption] = []
        self._tree: ttk.Treeview | None = None
        self._details_text: tk.Text | None = None

        self._origin_var: tk.StringVar | None = None
        self._destination_var: tk.StringVar | None = None
        self._date_var: tk.StringVar | None = None
        self._passengers_var: tk.StringVar | None = None

    def get_view_identifier(self) -> str:
        return "transport_explorer"

    def get_display_title(self) -> str:
        return "🚆 Transport-Modul"

    def get_sort_order(self) -> int:
        return 20

    def build_view_component(
        self,
        parent_container: tk.Widget,
        application_context: DashboardApplicationContext,
    ) -> tk.Widget:
        self._context = application_context

        self._origin_var = tk.StringVar(master=parent_container, value="Berlin")
        self._destination_var = tk.StringVar(master=parent_container, value="Paris")
        self._date_var = tk.StringVar(master=parent_container, value="2026-07-01")
        self._passengers_var = tk.StringVar(master=parent_container, value="1")

        root_frame = ttk.Frame(parent_container, padding="10")
        root_frame.columnconfigure(0, weight=1)
        root_frame.rowconfigure(1, weight=1)

        # Query Controls
        control_frame = ttk.LabelFrame(root_frame, text="Verkehrsverbindungen abfragen", padding="10")
        control_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        for i in range(5):
            control_frame.columnconfigure(i, weight=1)

        ttk.Label(control_frame, text="Start:").grid(row=0, column=0, sticky="w", padx=4, pady=4)
        ttk.Combobox(
            control_frame,
            textvariable=self._origin_var,
            values=["Berlin", "Paris", "Rome", "Barcelona", "Vienna", "Amsterdam", "Munich", "Zurich", "London"],
            width=12,
        ).grid(row=0, column=1, sticky="ew", padx=4, pady=4)

        ttk.Label(control_frame, text="Ziel:").grid(row=0, column=2, sticky="w", padx=4, pady=4)
        ttk.Combobox(
            control_frame,
            textvariable=self._destination_var,
            values=["Paris", "Berlin", "Rome", "Barcelona", "Vienna", "Amsterdam", "Munich", "Zurich", "London"],
            width=12,
        ).grid(row=0, column=3, sticky="ew", padx=4, pady=4)

        ttk.Button(
            control_frame,
            text="🚀 Verbindungen vergleichen",
            command=self._on_search_clicked,
        ).grid(row=0, column=4, rowspan=2, sticky="e", padx=6, pady=4)

        ttk.Label(control_frame, text="Datum:").grid(row=1, column=0, sticky="w", padx=4, pady=4)
        ttk.Entry(control_frame, textvariable=self._date_var, width=12).grid(
            row=1, column=1, sticky="ew", padx=4, pady=4
        )

        ttk.Label(control_frame, text="Personen:").grid(row=1, column=2, sticky="w", padx=4, pady=4)
        ttk.Spinbox(control_frame, from_=1, to=8, textvariable=self._passengers_var, width=6).grid(
            row=1, column=3, sticky="w", padx=4, pady=4
        )

        # Split: Results Table and Segment Details
        paned = ttk.PanedWindow(root_frame, orient="vertical")
        paned.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        table_frame = ttk.Frame(paned)
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        cols = ("id", "type", "carrier", "departure", "arrival", "duration", "transfers", "price", "co2")
        self._tree = ttk.Treeview(table_frame, columns=cols, show="headings", selectmode="browse")
        self._tree.heading("id", text="ID")
        self._tree.heading("type", text="Modus")
        self._tree.heading("carrier", text="Anbieter / Linie")
        self._tree.heading("departure", text="Abfahrt")
        self._tree.heading("arrival", text="Ankunft")
        self._tree.heading("duration", text="Dauer")
        self._tree.heading("transfers", text="Umstiege")
        self._tree.heading("price", text="Preis")
        self._tree.heading("co2", text="CO2 (kg)")

        self._tree.column("id", width=120, anchor="center")
        self._tree.column("type", width=80, anchor="center")
        self._tree.column("carrier", width=140, anchor="w")
        self._tree.column("departure", width=120, anchor="center")
        self._tree.column("arrival", width=120, anchor="center")
        self._tree.column("duration", width=90, anchor="center")
        self._tree.column("transfers", width=70, anchor="center")
        self._tree.column("price", width=90, anchor="e")
        self._tree.column("co2", width=70, anchor="center")

        scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=scroll.set)
        self._tree.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")

        self._tree.bind("<<TreeviewSelect>>", self._on_select)
        paned.add(table_frame, weight=3)

        detail_frame = ttk.LabelFrame(paned, text="Teilstrecken & Segment-Details", padding="8")
        detail_frame.rowconfigure(0, weight=1)
        detail_frame.columnconfigure(0, weight=1)

        self._details_text = tk.Text(detail_frame, wrap="word", height=6, font=("Courier", 11))
        det_scroll = ttk.Scrollbar(detail_frame, orient="vertical", command=self._details_text.yview)
        self._details_text.configure(yscrollcommand=det_scroll.set)
        self._details_text.grid(row=0, column=0, sticky="nsew")
        det_scroll.grid(row=0, column=1, sticky="ns")
        paned.add(detail_frame, weight=2)

        return root_frame

    def _on_search_clicked(self) -> None:
        if not self._context:
            return

        try:
            travel_date = date.fromisoformat(self._date_var.get().strip())
            passengers = int(self._passengers_var.get())
            origin_loc = self._context.location_gateway.resolve_location_by_name(self._origin_var.get())
            dest_loc = self._context.location_gateway.resolve_location_by_name(self._destination_var.get())
        except Exception as e:
            messagebox.showerror("Fehler", f"Ungültige Eingabe:\n{e}")
            return

        self._options = self._context.transport_gateway.search_transport_options(
            origin_location=origin_loc,
            destination_location=dest_loc,
            travel_date=travel_date,
            allowed_transport_types=[TransportType.FLIGHT, TransportType.TRAIN, TransportType.CAR],
            number_of_passengers=passengers,
        )

        if not self._tree:
            return

        for item in self._tree.get_children():
            self._tree.delete(item)

        for opt in self._options:
            carrier_name = opt.segments[0].carrier_or_operator_name if opt.segments else "-"
            dur_hours = opt.calculate_total_duration_in_minutes() // 60
            dur_mins = opt.calculate_total_duration_in_minutes() % 60
            dur_str = f"{dur_hours}h {dur_mins:02d}m"

            self._tree.insert(
                "",
                "end",
                iid=opt.transport_option_id,
                values=(
                    opt.transport_option_id,
                    opt.transport_type.value,
                    carrier_name,
                    opt.departure_time.strftime("%H:%M"),
                    opt.arrival_time.strftime("%H:%M"),
                    dur_str,
                    opt.count_transfers(),
                    f"{opt.total_price.amount:.2f} €",
                    f"{opt.carbon_dioxide_emission_in_kilograms:.1f}",
                ),
            )

    def _on_select(self, event: tk.Event) -> None:
        if not self._tree or not self._details_text:
            return
        selected = self._tree.selection()
        if not selected:
            return
        opt_id = selected[0]
        opt = next((o for o in self._options if o.transport_option_id == opt_id), None)
        if not opt:
            return

        self._details_text.delete("1.0", tk.END)
        lines = [
            f"Verbindung: {opt.transport_option_id} [{opt.transport_type.value}]",
            f"Von: {opt.origin_location_name} -> Nach: {opt.destination_location_name}",
            f"Gesamtpreis: {opt.total_price} | CO2-Bilanz: {opt.carbon_dioxide_emission_in_kilograms} kg",
            f"Teilstrecken ({len(opt.segments)}):",
        ]
        for idx, seg in enumerate(opt.segments, start=1):
            lines.append(
                f"  [{idx}] {seg.departure_station_or_airport} ({seg.departure_time.strftime('%H:%M')}) "
                f"--> {seg.arrival_station_or_airport} ({seg.arrival_time.strftime('%H:%M')}) | "
                f"Betreiber: {seg.carrier_or_operator_name} | Kennung: {seg.segment_identifier} ({seg.duration_in_minutes} Min.)"
            )
        self._details_text.insert("1.0", "\n".join(lines))

    def refresh_view(self) -> None:
        pass
