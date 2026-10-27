from __future__ import annotations

import tkinter as tk
from tkinter import ttk


class DashboardThemeManager:
    """
    Manages custom visual themes and styling for the Tkinter desktop dashboard.
    Forces the reliable 'clam' engine to avoid macOS Dark Mode rendering bugs
    in ancient system Tk 8.5, and applies a modern, cohesive dark aesthetic.
    """

    COLOR_BACKGROUND: str = "#181824"
    COLOR_CARD_BACKGROUND: str = "#222533"
    COLOR_CARD_BORDER: str = "#35394d"
    COLOR_PRIMARY_BUTTON: str = "#3b82f6"
    COLOR_PRIMARY_ACTIVE: str = "#2563eb"
    COLOR_TEXT_PRIMARY: str = "#f8fafc"
    COLOR_TEXT_SECONDARY: str = "#94a3b8"
    COLOR_TEXT_HIGHLIGHT: str = "#38bdf8"
    COLOR_INPUT_BACKGROUND: str = "#12131d"
    COLOR_INPUT_BORDER: str = "#475569"
    COLOR_SELECTED_TAB: str = "#3b82f6"
    COLOR_UNSELECTED_TAB: str = "#2c3044"
    COLOR_TREE_EVEN: str = "#1e212f"
    COLOR_TREE_ODD: str = "#262a3b"

    def apply_theme(self, root_window: tk.Tk) -> None:
        """
        Configures root window colors and applies ttk widget styles.
        """
        root_window.configure(bg=self.COLOR_BACKGROUND)

        style = ttk.Style(root_window)
        available_themes = style.theme_names()
        if "clam" in available_themes:
            style.theme_use("clam")
        elif "alt" in available_themes:
            style.theme_use("alt")

        # 1. Base Frames
        style.configure("TFrame", background=self.COLOR_BACKGROUND)
        style.configure("Card.TFrame", background=self.COLOR_CARD_BACKGROUND)

        # 2. Labels
        style.configure(
            "TLabel",
            background=self.COLOR_BACKGROUND,
            foreground=self.COLOR_TEXT_PRIMARY,
            font=("Helvetica", 10),
        )
        style.configure(
            "Card.TLabel",
            background=self.COLOR_CARD_BACKGROUND,
            foreground=self.COLOR_TEXT_PRIMARY,
            font=("Helvetica", 10),
        )
        style.configure(
            "Header.TLabel",
            background=self.COLOR_BACKGROUND,
            foreground=self.COLOR_TEXT_PRIMARY,
            font=("Helvetica", 16, "bold"),
        )
        style.configure(
            "SubHeader.TLabel",
            background=self.COLOR_BACKGROUND,
            foreground=self.COLOR_TEXT_SECONDARY,
            font=("Helvetica", 10),
        )
        style.configure(
            "Status.TLabel",
            background=self.COLOR_CARD_BACKGROUND,
            foreground=self.COLOR_TEXT_SECONDARY,
            font=("Helvetica", 9),
        )

        # 3. LabelFrames (Cards)
        style.configure(
            "TLabelframe",
            background=self.COLOR_CARD_BACKGROUND,
            foreground=self.COLOR_TEXT_PRIMARY,
            bordercolor=self.COLOR_CARD_BORDER,
            borderwidth=1,
            relief="solid",
        )
        style.configure(
            "TLabelframe.Label",
            background=self.COLOR_CARD_BACKGROUND,
            foreground=self.COLOR_TEXT_HIGHLIGHT,
            font=("Helvetica", 10, "bold"),
        )

        # 4. Buttons
        style.configure(
            "TButton",
            background=self.COLOR_PRIMARY_BUTTON,
            foreground="#ffffff",
            font=("Helvetica", 10, "bold"),
            borderwidth=0,
            padding=[10, 6],
            relief="flat",
        )
        style.map(
            "TButton",
            background=[("active", self.COLOR_PRIMARY_ACTIVE), ("pressed", "#1d4ed8")],
            foreground=[("active", "#ffffff"), ("pressed", "#ffffff")],
        )

        # 5. Notebook (Tabs)
        style.configure(
            "TNotebook",
            background=self.COLOR_BACKGROUND,
            tabmargins=[2, 4, 2, 0],
            borderwidth=0,
        )
        style.configure(
            "TNotebook.Tab",
            background=self.COLOR_UNSELECTED_TAB,
            foreground=self.COLOR_TEXT_SECONDARY,
            padding=[16, 8],
            font=("Helvetica", 10, "bold"),
            borderwidth=0,
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", self.COLOR_SELECTED_TAB)],
            foreground=[("selected", "#ffffff")],
        )

        # 6. Inputs: Combobox, Entry, Spinbox, Checkbutton
        style.configure(
            "TCombobox",
            fieldbackground=self.COLOR_INPUT_BACKGROUND,
            background=self.COLOR_CARD_BACKGROUND,
            foreground="#ffffff",
            arrowcolor="#ffffff",
            borderwidth=1,
            relief="solid",
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", self.COLOR_INPUT_BACKGROUND)],
            foreground=[("readonly", "#ffffff")],
        )

        style.configure(
            "TEntry",
            fieldbackground=self.COLOR_INPUT_BACKGROUND,
            foreground="#ffffff",
            insertcolor="#ffffff",
            borderwidth=1,
        )

        style.configure(
            "TSpinbox",
            fieldbackground=self.COLOR_INPUT_BACKGROUND,
            background=self.COLOR_CARD_BACKGROUND,
            foreground="#ffffff",
            arrowcolor="#ffffff",
            borderwidth=1,
        )

        style.configure(
            "TCheckbutton",
            background=self.COLOR_CARD_BACKGROUND,
            foreground=self.COLOR_TEXT_PRIMARY,
            font=("Helvetica", 10),
        )

        # 7. Tables: Treeview
        style.configure(
            "Treeview",
            background=self.COLOR_INPUT_BACKGROUND,
            fieldbackground=self.COLOR_INPUT_BACKGROUND,
            foreground=self.COLOR_TEXT_PRIMARY,
            rowheight=26,
            borderwidth=0,
            font=("Helvetica", 10),
        )
        style.configure(
            "Treeview.Heading",
            background=self.COLOR_CARD_BACKGROUND,
            foreground="#ffffff",
            font=("Helvetica", 9, "bold"),
            padding=[6, 4],
            relief="flat",
        )
        style.map(
            "Treeview",
            background=[("selected", self.COLOR_PRIMARY_ACTIVE)],
            foreground=[("selected", "#ffffff")],
        )
        style.map(
            "Treeview.Heading",
            background=[("active", self.COLOR_CARD_BORDER)],
            foreground=[("active", "#ffffff")],
        )

        # 8. Scrollbar
        style.configure(
            "Vertical.TScrollbar",
            background=self.COLOR_CARD_BACKGROUND,
            troughcolor=self.COLOR_BACKGROUND,
            borderwidth=0,
            arrowcolor="#ffffff",
        )

    def style_text_widget(self, text_widget: tk.Text) -> None:
        """
        Applies dark theme colors, padding, and font to a standard Tk Text widget.
        """
        text_widget.configure(
            bg=self.COLOR_INPUT_BACKGROUND,
            fg=self.COLOR_TEXT_PRIMARY,
            insertbackground="#ffffff",
            selectbackground=self.COLOR_PRIMARY_BUTTON,
            selectforeground="#ffffff",
            relief="flat",
            borderwidth=1,
            highlightthickness=1,
            highlightbackground=self.COLOR_CARD_BORDER,
            highlightcolor=self.COLOR_PRIMARY_BUTTON,
            padx=10,
            pady=8,
            font=("Courier", 11),
        )

