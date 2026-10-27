from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
from typing import TYPE_CHECKING
from src.vacation_planner.core.domain.models.AccommodationOption import AccommodationOption
from src.vacation_planner.core.domain.value_objects.AccommodationType import AccommodationType
from src.vacation_planner.core.domain.value_objects.DateRange import DateRange
from src.vacation_planner.entrypoints.gui.DashboardViewInterface import DashboardViewInterface

if TYPE_CHECKING:
    from src.vacation_planner.entrypoints.gui.DashboardApplicationContext import (
        DashboardApplicationContext,
    )


class AccommodationExplorerDashboardView(DashboardViewInterface):
    """
    Dashboard view for the Accommodation Module.
    Enables users to explore hotels, apartments, hostels, and resorts by destination,
    date range, guest count, and property classification.
    """

    def __init__(self) -> None:
        self._context: DashboardApplicationContext | None = None
        self._accommodations: list[AccommodationOption] = []
        self._tree: ttk.Treeview | None = None
        self._detail_text: tk.Text | None = None

        self._destination_var: tk.StringVar | None = None
        self._start_date_var: tk.StringVar | None = None
        self._end_date_var: tk.StringVar | None = None
        self._guests_var: tk.StringVar | None = None
        self._type_filter_var: tk.StringVar | None = None

    def get_view_identifier(self) -> str:
        return "accommodation_explorer"

    def get_display_title(self) -> str:
        return "🏨 Unterkunfts-Modul"

    def get_sort_order(self) -> int:
        return 30

    def build_view_component(
        self,
        parent_container: tk.Widget,
        application_context: DashboardApplicationContext,
    ) -> tk.Widget:
        self._context = application_context

        self._destination_var = tk.StringVar(master=parent_container, value="Paris")
        self._start_date_var = tk.StringVar(master=parent_container, value="2026-07-01")
        self._end_date_var = tk.StringVar(master=parent_container, value="2026-07-07")
        self._guests_var = tk.StringVar(master=parent_container, value="2")
        self._type_filter_var = tk.StringVar(master=parent_container, value="ALLE")

        root_frame = ttk.Frame(parent_container, padding="10")
        root_frame.columnconfigure(0, weight=1)
        root_frame.rowconfigure(1, weight=1)

        # Search Controls
        filter_frame = ttk.LabelFrame(root_frame, text="Unterkünfte filtern & durchsuchen", padding="12")
        filter_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        for i in range(5):
            filter_frame.columnconfigure(i, weight=1)

        ttk.Label(filter_frame, text="Zielort:", style="Card.TLabel").grid(row=0, column=0, sticky="w", padx=4, pady=4)
        ttk.Combobox(
            filter_frame,
            textvariable=self._destination_var,
            values=["Paris", "Berlin", "Rome", "Barcelona", "Vienna", "Amsterdam", "Munich", "Zurich", "London"],
            width=12,
        ).grid(row=0, column=1, sticky="ew", padx=4, pady=4)

        ttk.Label(filter_frame, text="Kategorie:", style="Card.TLabel").grid(row=0, column=2, sticky="w", padx=4, pady=4)
        ttk.Combobox(
            filter_frame,
            textvariable=self._type_filter_var,
            values=["ALLE", "HOTEL", "APARTMENT", "HOSTEL", "RESORT"],
            width=12,
        ).grid(row=0, column=3, sticky="ew", padx=4, pady=4)

        ttk.Button(
            filter_frame,
            text="🔎 Unterkünfte abfragen",
            command=self._on_search_clicked,
        ).grid(row=0, column=4, rowspan=2, sticky="e", padx=6, pady=4)

        ttk.Label(filter_frame, text="Check-in:", style="Card.TLabel").grid(row=1, column=0, sticky="w", padx=4, pady=4)
        ttk.Entry(filter_frame, textvariable=self._start_date_var, width=12).grid(
            row=1, column=1, sticky="ew", padx=4, pady=4
        )

        ttk.Label(filter_frame, text="Check-out:", style="Card.TLabel").grid(row=1, column=2, sticky="w", padx=4, pady=4)
        ttk.Entry(filter_frame, textvariable=self._end_date_var, width=12).grid(
            row=1, column=3, sticky="ew", padx=4, pady=4
        )

        # Paned Window
        paned = ttk.PanedWindow(root_frame, orient="vertical")
        paned.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        table_frame = ttk.Frame(paned)
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        cols = ("id", "name", "type", "stars", "nightly", "total", "address")
        self._tree = ttk.Treeview(table_frame, columns=cols, show="headings", selectmode="browse")
        self._tree.heading("id", text="ID")
        self._tree.heading("name", text="Name der Unterkunft")
        self._tree.heading("type", text="Typ")
        self._tree.heading("stars", text="Sterne")
        self._tree.heading("nightly", text="Preis / Nacht")
        self._tree.heading("total", text="Gesamtpreis")
        self._tree.heading("address", text="Adresse")

        self._tree.column("id", width=110, anchor="center")
        self._tree.column("name", width=220, anchor="w")
        self._tree.column("type", width=90, anchor="center")
        self._tree.column("stars", width=70, anchor="center")
        self._tree.column("nightly", width=90, anchor="e")
        self._tree.column("total", width=90, anchor="e")
        self._tree.column("address", width=240, anchor="w")

        scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=scroll.set)
        self._tree.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")

        self._tree.bind("<<TreeviewSelect>>", self._on_select)
        paned.add(table_frame, weight=3)

        detail_frame = ttk.LabelFrame(paned, text="Ausstattung & Merkmale", padding="8")
        detail_frame.rowconfigure(0, weight=1)
        detail_frame.columnconfigure(0, weight=1)

        self._detail_text = tk.Text(detail_frame, wrap="word", height=6)
        application_context.theme_manager.style_text_widget(self._detail_text)
        det_scroll = ttk.Scrollbar(detail_frame, orient="vertical", command=self._detail_text.yview)
        self._detail_text.configure(yscrollcommand=det_scroll.set)
        self._detail_text.grid(row=0, column=0, sticky="nsew")
        det_scroll.grid(row=0, column=1, sticky="ns")
        paned.add(detail_frame, weight=2)

        return root_frame

    def _on_search_clicked(self) -> None:
        if not self._context:
            return

        try:
            date_range = DateRange(self._start_date_var.get().strip(), self._end_date_var.get().strip())
            guests = int(self._guests_var.get())
            dest_loc = self._context.location_gateway.resolve_location_by_name(self._destination_var.get())
        except Exception as e:
            messagebox.showerror("Fehler", f"Ungültige Eingabe:\n{e}")
            return

        pref_type: AccommodationType | None = None
        type_str = self._type_filter_var.get().strip().upper()
        if type_str != "ALLE":
            pref_type = AccommodationType(type_str)

        self._accommodations = self._context.accommodation_gateway.search_accommodation_options(
            destination_location=dest_loc,
            date_range=date_range,
            number_of_guests=guests,
            preferred_accommodation_type=pref_type,
        )

        if not self._tree or not self._context:
            return

        self._tree.tag_configure("evenrow", background=self._context.theme_manager.COLOR_TREE_EVEN)
        self._tree.tag_configure("oddrow", background=self._context.theme_manager.COLOR_TREE_ODD)

        for item in self._tree.get_children():
            self._tree.delete(item)

        for idx, acc in enumerate(self._accommodations):
            row_tag = "evenrow" if idx % 2 == 0 else "oddrow"
            self._tree.insert(
                "",
                "end",
                iid=acc.accommodation_id,
                tags=(row_tag,),
                values=(
                    acc.accommodation_id,
                    acc.name,
                    acc.accommodation_type.value,
                    f"{acc.star_rating} ★",
                    f"{acc.price_per_night.amount:.2f} €",
                    f"{acc.total_price.amount:.2f} €",
                    acc.address_line,
                ),
            )

    def _on_select(self, event: tk.Event) -> None:
        if not self._tree or not self._detail_text:
            return
        selected = self._tree.selection()
        if not selected:
            return
        acc_id = selected[0]
        acc = next((a for a in self._accommodations if a.accommodation_id == acc_id), None)
        if not acc:
            return

        self._detail_text.delete("1.0", tk.END)
        lines = [
            f"Unterkunft: {acc.name} [{acc.accommodation_type.value}] - {acc.star_rating} Sterne",
            f"Standort:   {acc.location_name} | Koordinaten: {acc.coordinates}",
            f"Adresse:    {acc.address_line}",
            f"Preise:     {acc.price_per_night} pro Nacht | {acc.total_price} Gesamt für {acc.date_range.calculate_total_nights()} Übernachtungen",
            f"Inkludierte Ausstattungsmerkmale (Amenities):",
        ]
        for amenity in acc.included_amenities:
            lines.append(f"  ✓ {amenity}")
        self._detail_text.insert("1.0", "\n".join(lines))

    def refresh_view(self) -> None:
        pass
