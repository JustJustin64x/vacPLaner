from __future__ import annotations

import tkinter as tk
from tkinter import ttk
import unittest
from src.vacation_planner.entrypoints.gui.DashboardThemeManager import DashboardThemeManager


class TestDashboardThemeManager(unittest.TestCase):
    def test_theme_application(self) -> None:
        root = tk.Tk()
        theme_manager = DashboardThemeManager()
        theme_manager.apply_theme(root)

        # Verify background
        self.assertEqual(root.cget("bg"), theme_manager.COLOR_BACKGROUND)

        # Verify text widget styling
        text_widget = tk.Text(root)
        theme_manager.style_text_widget(text_widget)
        self.assertEqual(text_widget.cget("bg"), theme_manager.COLOR_INPUT_BACKGROUND)
        self.assertEqual(text_widget.cget("fg"), theme_manager.COLOR_TEXT_PRIMARY)

        root.destroy()


if __name__ == "__main__":
    unittest.main()

