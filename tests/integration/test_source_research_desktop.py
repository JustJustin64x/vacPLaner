import copy
import threading
import time
import tkinter as tk
import unittest
from unittest.mock import patch
from src.vacation_planner.entrypoints.gui.SurprisePlannerApplication import SurprisePlannerApplication
from tests.unit.test_source_research import trip,Model
import tests.unit.test_source_research as research_fixture
from tests.unit.test_surprise_planning import FixtureProvider

MODULE='src.vacation_planner.entrypoints.gui.SurprisePlannerApplication.TripEnrichmentService'


@unittest.skipIf(tk.TkVersion<8.6,'Modern Tk required')
class SourceDesktopTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):research_fixture.ResearchTests.setUpClass()
    @classmethod
    def tearDownClass(cls):research_fixture.ResearchTests.tearDownClass()
    def setUp(self):
        self.fixture=research_fixture.ResearchTests('test_real_fixture_http_identity_provenance_and_no_trip_mutation');self.fixture.setUp()
        self.app=SurprisePlannerApplication(self.fixture.store,FixtureProvider());self.root=self.app.create_window();self.root.withdraw()
        self.original=trip();self.load(self.original)
    def tearDown(self):
        self.app.close()
        for worker in self.app.workers:worker.join(2)
        self.fixture.tearDown()
    def load(self,value):
        self.app.trips[value['id']]=value;self.app.update_row(value);self.app.tree.selection_set(value['id']);self.app.select_trip()
    def wait(self):
        deadline=time.monotonic()+3
        while self.app.enrichment_context and time.monotonic()<deadline:self.root.update();time.sleep(.005)
        self.assertIsNone(self.app.enrichment_context)
    def test_explicit_action_renders_proof_without_automatic_save_or_ranking(self):
        saved=self.app.store.save('Bestehend',self.original);before=self.app.store.load(saved)
        result=self.fixture.enrich(self.original)
        with patch(MODULE) as factory:
            factory.return_value.enrich.return_value=result
            self.app.enrich_active();self.wait()
            self.assertTrue(factory.return_value.enrich.call_args.kwargs['research'])
        self.assertIn('Originalnachweis',self.app.details.get('1.0','end'))
        self.assertIn('Testmuseum',self.app.details.get('1.0','end'))
        self.assertEqual(self.app.active['score'],before['score']);self.assertEqual(self.app.active['cost_summary'],before['cost_summary'])
        self.assertEqual(self.app.store.load(saved),before)
        self.app.saved_id=saved
        with patch('tkinter.simpledialog.askstring',return_value='Bewusst gespeichert'):self.app.save_trip()
        self.assertEqual(self.app.store.load(saved)['source_research'],result['source_research'])
    def test_late_answer_for_previous_target_ignored(self):
        result=self.fixture.enrich(self.original);release=threading.Event();entered=threading.Event()
        def slow(*args,**kwargs):entered.set();release.wait(2);return result
        with patch(MODULE) as factory:
            factory.return_value.enrich.side_effect=slow;self.app.enrich_active();self.assertTrue(entered.wait(1))
            other=copy.deepcopy(self.original);other['id']='other';other['destination']['name']='Anderes Ziel';self.load(other)
            release.set();self.app.workers[-1].join(1);self.app.poll()
        self.assertEqual(self.app.active['id'],'other');self.assertNotIn('source_research',self.app.active)
    def test_changed_working_trip_cannot_be_overwritten(self):
        result=self.fixture.enrich(self.original);release=threading.Event();entered=threading.Event()
        def slow(*args,**kwargs):entered.set();release.wait(2);return result
        with patch(MODULE) as factory:
            factory.return_value.enrich.side_effect=slow;self.app.enrich_active();self.assertTrue(entered.wait(1))
            self.app.active['notes'].append('Zwischenzeitliche Änderung')
            release.set();self.app.workers[-1].join(1);self.app.poll()
        self.assertIsNone(self.app.enrichment_context);self.assertIn('Zwischenzeitliche Änderung',self.app.active['notes'])
        self.assertNotIn('source_research',self.app.active)
    def test_cancel_stops_context_and_discards_response(self):
        entered=threading.Event()
        def slow(original,context,emit,research=False):
            entered.set()
            while not context.cancel.wait(.01):pass
            raise InterruptedError('cancelled')
        with patch(MODULE) as factory:
            factory.return_value.enrich.side_effect=slow;self.app.enrich_active();self.assertTrue(entered.wait(1))
            beats=[];self.root.after(1,lambda:beats.append(True));time.sleep(.01);self.root.update();self.assertTrue(beats)
            self.app.cancel_search();self.app.workers[-1].join(1);self.app.poll()
        self.assertFalse(self.app.workers[-1].is_alive());self.assertNotIn('source_research',self.app.active)
    def test_no_model_keeps_deterministic_source_hints(self):
        result=self.fixture.enrich(self.original,Model(error=OSError('offline')))
        with patch(MODULE) as factory:
            factory.return_value.enrich.return_value=result;self.app.enrich_active();self.wait()
        self.assertIn('nicht verfügbar',self.app.details.get('1.0','end'));self.assertEqual(len(self.app.active['source_research']['evidence']),3)
    def test_new_search_invalidates_pending_research(self):
        result=self.fixture.enrich(self.original);release=threading.Event();entered=threading.Event()
        def slow(*args,**kwargs):entered.set();release.wait(2);return result
        with patch(MODULE) as factory:
            factory.return_value.enrich.side_effect=slow;self.app.enrich_active();self.assertTrue(entered.wait(1))
            self.app.start_search();release.set()
            deadline=time.monotonic()+3
            while self.app.running and time.monotonic()<deadline:self.root.update();time.sleep(.005)
            self.app.poll()
        self.assertFalse(self.app.running);self.assertTrue(self.app.trips)
        self.assertTrue(all('source_research' not in row for row in self.app.trips.values()))
