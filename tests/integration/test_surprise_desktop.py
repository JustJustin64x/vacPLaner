import json
import tempfile
import time
import tkinter as tk
import unittest
from pathlib import Path
from unittest.mock import patch

from src.vacation_planner.entrypoints.gui.SurprisePlannerApplication import SurprisePlannerApplication
from src.vacation_planner.infrastructure.planning.TripStore import TripStore
from src.vacation_planner.infrastructure.planning.TripPdfExporter import TripPdfExporter
from src.vacation_planner.entrypoints.gui.TripPresenter import TripPresenter
from tests.unit.test_surprise_planning import fixture_trip, FixtureProvider


@unittest.skipIf(tk.TkVersion < 8.6,'Desktop needs Tk >= 8.6; system Tk 8.5 is intentionally unsupported')
class DesktopTests(unittest.TestCase):
    def setUp(self):
        self.directory=tempfile.TemporaryDirectory()
        self.path=Path(self.directory.name)
        self.app=SurprisePlannerApplication(TripStore(self.path/'trips.sqlite3'),FixtureProvider())
        self.root=self.app.create_window()
        self.root.withdraw()

    def tearDown(self):
        self.app.close()
        for worker in self.app.workers:worker.join(timeout=2)
        self.directory.cleanup()

    def load_trip(self):
        trip=fixture_trip()
        self.app.trips[trip['id']]=trip
        self.app.update_row(trip)
        self.app.tree.selection_set(trip['id']);self.app.select_trip()
        return trip

    def test_filters_roundtrip_and_swap(self):
        trip=self.load_trip()
        self.app.populate_request(trip['request'])
        self.assertEqual(self.app.read_request().to_dict(),trip['request'])
        self.app.lodging_box.current(1)
        self.app.transport_box.current(1)
        self.app.swap()
        self.assertEqual(trip['selected_lodging'],1)
        self.assertEqual(trip['selected_transport'],1)
        self.assertIn('Alternative: Auto',self.app.details.get('1.0','end'))
        self.assertIsNone(trip['cost_summary']['budget_ok'])

    def test_save_reopen_change_and_pdf_dialog(self):
        trip=self.load_trip()
        with patch('tkinter.simpledialog.askstring',return_value='Prüfreise Juli'):
            self.app.save_trip()
        identifier=self.app.saved_id
        self.app.store=TripStore(self.path/'trips.sqlite3')
        self.app.saved_tree.selection_set(identifier)
        self.app.open_saved()
        self.app.transport_box.current(1);self.app.swap()
        with patch('tkinter.simpledialog.askstring',return_value='Geändert'):
            self.app.save_trip()
        self.assertEqual(self.app.store.load(identifier)['selected_transport'],1)
        destination=self.path/'reise.pdf'
        with patch('tkinter.filedialog.asksaveasfilename',return_value=str(destination)):
            self.app.export_pdf()
        from pypdf import PdfReader
        pdf=PdfReader(destination)
        text='\n'.join(page.extract_text() for page in pdf.pages)
        self.assertGreater(len(pdf.pages),1)
        self.assertIn('Überraschungsreise',text)
        self.assertIn('5 Erwachsene',text)
        self.assertIn('unbestätigt',text)
        self.assertGreater(sum(len(p.get('/Annots',[])) for p in pdf.pages),10)

    def test_late_results_cannot_replace_new_search(self):
        trip=fixture_trip()
        old_generation=self.app.generation
        self.app.cancel_search()
        self.app.events.put((old_generation,'result',trip))
        self.app.events.put((old_generation,'done',None))
        self.app.poll()
        self.assertEqual(self.app.trips,{})
        self.assertFalse(self.app.running)

    def test_worker_search_keeps_tk_responsive_and_cancels(self):
        class SlowProvider(FixtureProvider):
            def places(self,destination,context):
                context.wait(5)
                return super().places(destination,context)
        self.app.provider=SlowProvider()
        self.app.populate_request(fixture_trip()['request'])
        start=time.monotonic()
        self.app.start_search()
        self.assertLess(time.monotonic()-start,.2)
        self.root.update()
        self.assertTrue(self.app.running)
        self.app.cancel_search()
        self.app.workers[-1].join(timeout=1)
        self.assertFalse(self.app.workers[-1].is_alive())
        self.root.update()
        self.assertEqual(self.app.trips,{})


if __name__=='__main__':unittest.main()
