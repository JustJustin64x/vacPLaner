from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING
from src.vacation_planner.core.domain.models.VacationPackage import VacationPackage
from src.vacation_planner.entrypoints.gui.DashboardViewInterface import DashboardViewInterface

if TYPE_CHECKING:
    from src.vacation_planner.entrypoints.gui.DashboardApplicationContext import (
        DashboardApplicationContext,
    )


class SavedPackagesDashboardView(DashboardViewInterface):
    """
    Dashboard view for inspecting saved and generated vacation packages.
    Provides persistence inspection and historical record browsing.
    """

    def __init__(self) -> None:
        self._context: DashboardApplicationContext | None = None
        self._packages: list[VacationPackage] = []
        self._tree: ttk.Treeview | None = None
        self._detail_text: tk.Text | None = None

    def get_view_identifier(self) -> str:
        return "saved_packages_inspector"

    def get_display_title(self) -> str:
        return "💾 Gespeicherte Pakete"

    def get_sort_order(self) -> int:
        return 50

    def build_view_component(
        self,
        parent_container: tk.Widget,
        application_context: DashboardApplicationContext,
    ) -> tk.Widget:
        self._context = application_context

        root_frame = ttk.Frame(parent_container, padding="10")
        root_frame.columnconfigure(0, weight=1)
        root_frame.rowconfigure(1, weight=1)

        # Header Bar
        header_frame = ttk.Frame(root_frame)
        header_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        header_frame.columnconfigure(0, weight=1)

        ttk.Label(
            header_frame,
            text="Persistierte Urlaubspakete im Speicher",
            font=("Helvetica", 12, "bold"),
        ).grid(row=0, column=0, sticky="w")

        ttk.Button(
            header_frame,
            text="🔄 Liste aktualisieren",
            command=self.refresh_view,
        ).grid(row=0, column=1, sticky="e")

        # Paned Window
        paned = ttk.PanedWindow(root_frame, orient="vertical")
        paned.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        table_frame = ttk.Frame(paned)
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        cols = ("id", "origin", "destination", "dates", "cost", "budget_status")
        self._tree = ttk.Treeview(table_frame, columns=cols, show="headings", selectmode="browse")
        self._tree.heading("id", text="Paket-ID")
        self._tree.heading("origin", text="Startort")
        self._tree.heading("destination", text="Zielort")
        self._tree.heading("dates", text="Reisezeitraum")
        self._tree.heading("cost", text="Gesamtkosten")
        self._tree.heading("budget_status", text="Budget-Status")

        self._tree.column("id", width=140, anchor="center")
        self._tree.column("origin", width=120, anchor="w")
        self._tree.column("destination", width=120, anchor="w")
        self._tree.column("dates", width=200, anchor="center")
        self._tree.column("cost", width=110, anchor="e")
        self._tree.column("budget_status", width=130, anchor="center")

        scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=scroll.set)
        self._tree.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")

        self._tree.bind("<<TreeviewSelect>>", self._on_select)
        paned.add(table_frame, weight=3)

        detail_frame = ttk.LabelFrame(paned, text="Zusammenfassung", padding="8")
        detail_frame.rowconfigure(0, weight=1)
        detail_frame.columnconfigure(0, weight=1)

        self._detail_text = tk.Text(detail_frame, wrap="word", height=5, font=("Courier", 11))
        det_scroll = ttk.Scrollbar(detail_frame, orient="vertical", command=self._detail_text.yview)
        self._detail_text.configure(yscrollcommand=det_scroll.set)
        self._detail_text.grid(row=0, column=0, sticky="nsew")
        det_scroll.grid(row=0, column=1, sticky="ns")
        paned.add(detail_frame, weight=2)

        self.refresh_view()
        return root_frame

    def refresh_view(self) -> None:
        if not self._context or not self._tree:
            return

        self._packages = self._context.package_repository.list_all_vacation_packages()

        for item in self._tree.get_children():
            self._tree.delete(item)

        for pkg in self._packages:
            budget_str = "✓ Im Budget" if pkg.is_within_budget else "✗ Überschritten"
            self._tree.insert(
                "",
                "end",
                iid=pkg.package_id,
                values=(
                    pkg.package_id,
                    pkg.origin_location.name,
                    pkg.destination_location.name,
                    str(pkg.date_range),
                    f"{pkg.total_package_cost.amount:.2f} €",
                    budget_str,
                ),
            )

    def _on_select(self, event: tk.Event) -> None:
        if not self._tree or not self._detail_text:
            return
        selected = self._tree.selection()
        if not selected:
            return
        pkg_id = selected[0]
        pkg = next((p for p in self._packages if p.package_id == pkg_id), None)
        if not pkg:
            return

        self._detail_text.delete("1.0", tk.END)
        lines = [
            f"Paket-ID:      {pkg.package_id}",
            f"Start / Ziel:  {pkg.origin_location.name} -> {pkg.destination_location.name}",
            f"Gesamtkosten:  {pkg.total_package_cost} | Budgetprüfung: {pkg.validation_notes[0]}",
            f"Hinreise:      {pkg.outbound_transport_option.transport_type.value} ({pkg.outbound_transport_option.total_price})",
            f"Rückreise:     {pkg.return_transport_option.transport_type.value} ({pkg.return_transport_option.total_price})",
            f"Unterkunft:    {pkg.accommodation_option.name} ({pkg.accommodation_option.total_price})",
            f"Attraktionen:  {', '.join(a.name for a in pkg.recommended_attractions)}",
        ]
        self._detail_text.insert("1.0", "\n".join(lines))
