"""UI opt-in, stale optional results, explicit persistence; no live network."""
import copy
import tempfile
import threading
from unittest.mock import patch
import tkinter as tk
import unittest
from pathlib import Path
from src.vacation_planner.entrypoints.gui.SurprisePlannerApplication import SurprisePlannerApplication
from src.vacation_planner.infrastructure.planning.TripStore import TripStore
from src.vacation_planner.core.planning.SearchContext import SearchContext
from src.vacation_planner.core.planning.SearchRequest import SearchRequest
from tests.unit.test_surprise_planning import fixture_trip,FixtureProvider


@unittest.skipIf(tk.TkVersion<8.6,'Modern Tk required')
class CandidateDesktopTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.app=SurprisePlannerApplication(TripStore(Path(self.temp.name)/'trips.sqlite3'),FixtureProvider())
        self.root=self.app.create_window();self.root.withdraw()
    def tearDown(self):
        self.app.close();self.temp.cleanup()
    def test_opt_in_roundtrip_and_old_format_defaults_off(self):
        q=SearchRequest(earliest='2090-07-01',latest='2090-07-31',ai_discovery=True)
        self.app.populate_request(q.to_dict());self.assertTrue(self.app.read_request().ai_discovery)
        old=q.to_dict();old.pop('ai_discovery');self.app.populate_request(old);self.assertFalse(self.app.read_request().ai_discovery)
    def test_changed_form_cancels_optional_search_and_discards_late_results(self):
        app=self.app;entered=threading.Event();release=threading.Event()
        q=SearchRequest(earliest='2090-07-01',latest='2090-07-31',ai_discovery=True)
        app.populate_request(q.to_dict())
        def loading(*args):entered.set();release.wait(2)
        # Before DiscoveryService sees the request, catalog loading can be slow.
        with patch.object(app.catalog,'refresh',side_effect=loading),patch('src.vacation_planner.entrypoints.gui.SurprisePlannerApplication.DiscoveryService.search'):
            app.start_search();old=app.generation
            try:
                self.assertTrue(entered.wait(1));app.vars['countries'].set('DE')
                self.assertTrue(app.context.cancel.is_set());self.assertFalse(app.running)
            finally:
                release.set();app.workers[-1].join(2)
        app.events.put((old,'result',fixture_trip()));app.events.put((old,'done',None));app.poll();self.assertFalse(app.trips)
    def test_new_search_generation_and_close_reject_old_idea(self):
        app=self.app;old=app.generation;app.cancel_search()
        trip=fixture_trip();trip['discovery_origin']=dict(kind='local_model_idea',explanation='Zusätzliche KI-Idee',identity_method='Geprüft',identity_source='https://www.geonames.org/1')
        app.events.put((old,'result',trip));app.poll();self.assertFalse(app.trips)
        app.events.put((app.generation,'result',trip));app.poll();self.assertEqual(app.active['id'],trip['id'])
        self.assertIn('Zusätzliche KI-Idee',app.details.get('1.0','end'))
        saved=app.store.save('Ausdrücklich',app.active);before=app.store.load(saved)
        app.active['discovery_origin']['explanation']='Arbeitskopie'
        self.assertEqual(app.store.load(saved),before)
