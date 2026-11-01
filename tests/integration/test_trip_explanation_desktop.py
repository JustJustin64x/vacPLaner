import copy
import tempfile
import threading
import time
import tkinter as tk
import unittest
from pathlib import Path
from unittest.mock import patch
from src.vacation_planner.entrypoints.gui.SurprisePlannerApplication import SurprisePlannerApplication
from src.vacation_planner.infrastructure.local_ai.ExplanationService import ExplanationService
from src.vacation_planner.infrastructure.planning.TripStore import TripStore
from tests.unit.test_surprise_planning import FixtureProvider, fixture_trip
from tests.unit.test_trip_explanation import FakeClient, sample_trip


def full_trip():
    trip=fixture_trip();synthetic=sample_trip()
    trip['request']['interests']=synthetic['request']['interests']
    trip['interest_evidence']=synthetic['interest_evidence']
    return trip


@unittest.skipIf(tk.TkVersion<8.6,'Modern Tk required')
class ExplanationDesktopTests(unittest.TestCase):
    def setUp(self):
        self.directory=tempfile.TemporaryDirectory()
        self.app=SurprisePlannerApplication(TripStore(Path(self.directory.name)/'trips.sqlite3'),FixtureProvider())
        self.root=self.app.create_window();self.root.withdraw()
        self.panel=self.app.explanation_panel
        self.fake=FakeClient();self.panel.service=ExplanationService(self.fake)
        self.trip=full_trip();self.load(self.trip)

    def tearDown(self):
        self.app.close()
        for w in self.app.workers:w.join(2)
        self.directory.cleanup()

    def load(self,trip):
        self.app.trips[trip['id']]=trip;self.app.update_row(trip)
        self.app.tree.selection_set(trip['id']);self.app.select_trip()

    def finish(self):
        deadline=time.monotonic()+3
        while self.panel.cancel is not None and time.monotonic()<deadline:
            self.root.update();self.panel.poll();time.sleep(.005)
        self.assertIsNone(self.panel.cancel)

    def test_explicit_action_async_render_cache_and_no_trip_mutation(self):
        before=copy.deepcopy(self.trip)
        self.assertEqual(self.fake.calls,0)
        self.panel.start();self.finish()
        self.assertEqual(self.panel.result['status'],'local_ai')
        self.assertIn('Testmuseum',self.panel.text.get('1.0','end'))
        self.assertIn('Quellenstand',self.panel.text.get('1.0','end'))
        self.assertEqual(self.trip,before)
        self.panel.start();self.finish();self.assertEqual(self.fake.calls,1)
        self.assertTrue(self.panel.result['cached'])

    def test_offline_keeps_existing_details_and_trip_unchanged(self):
        self.fake.error=OSError('Dienst nicht erreichbar')
        before=copy.deepcopy(self.trip);details=self.app.details.get('1.0','end')
        self.panel.start();self.finish()
        self.assertIn('scripts/local_ai.py start',self.panel.status.get())
        self.assertEqual(self.app.details.get('1.0','end'),details)
        self.assertEqual(self.trip,before)
        self.assertIn('Belegübersicht ohne KI',self.panel.status.get())

    def test_late_result_after_selection_change_is_discarded(self):
        oldkey=self.panel.key;oldserial=self.panel.serial
        other=copy.deepcopy(self.trip);other['id']='second';other['destination']['name']='Anderes Ziel'
        self.load(other)
        self.panel.events.put((oldserial,oldkey,dict(status='local_ai',cached=False,text='VERALTET',links=[]),None))
        self.panel.poll()
        self.assertNotIn('VERALTET',self.panel.text.get('1.0','end'))
        self.assertIn('Anderes Ziel',self.panel.heading.get())

    def test_new_search_discards_queued_old_answer(self):
        oldkey=self.panel.key;oldserial=self.panel.serial
        self.app.populate_request(self.trip['request']);self.app.start_search()
        self.panel.events.put((oldserial,oldkey,dict(status='local_ai',cached=False,text='VERALTET',links=[]),None))
        self.panel.poll()
        self.assertNotIn('VERALTET',self.panel.text.get('1.0','end'))
        self.app.cancel_search()

    def test_active_cancellation_and_gui_events(self):
        entered=threading.Event()
        class SlowClient(FakeClient):
            def chat(self,messages,schema=None,cancel=None):
                entered.set()
                while not cancel.wait(.01):pass
                raise InterruptedError('cancelled')
        self.panel.service=ExplanationService(SlowClient())
        begin=time.monotonic();self.panel.start()
        self.assertLess(time.monotonic()-begin,.2);self.assertTrue(entered.wait(1))
        callbacks=[];self.root.after(1,lambda:callbacks.append(True));time.sleep(.01);self.root.update()
        self.assertTrue(callbacks)
        self.panel.abort();self.app.workers[-1].join(1);self.panel.poll()
        self.assertFalse(self.app.workers[-1].is_alive());self.assertIsNone(self.panel.result)
        self.assertIn('Keine ungeprüfte',self.panel.text.get('1.0','end'))

    def test_updated_evidence_resets_view_and_source_links_require_click(self):
        with patch('webbrowser.open') as opened:
            self.panel.start();self.finish();opened.assert_not_called()
        self.trip['interest_evidence']['Kultur']['evidence'][0]['retrieved_at']='2090-01-01'
        self.app.show_details()
        self.assertIsNone(self.panel.result)
        self.assertIn('Noch keine Erklärung',self.panel.status.get())
        self.panel.start();self.finish();self.assertEqual(self.fake.calls,2)
