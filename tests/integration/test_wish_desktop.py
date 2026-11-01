import copy
from pathlib import Path
import tempfile
import threading
import time
import tkinter as tk
import unittest
from src.vacation_planner.entrypoints.gui.SurprisePlannerApplication import SurprisePlannerApplication
from src.vacation_planner.infrastructure.planning.TripStore import TripStore
from src.vacation_planner.infrastructure.local_ai.WishService import WishService
from tests.unit.test_surprise_planning import FixtureProvider
from tests.unit.test_travel_wishes import WishFakeClient


@unittest.skipIf(tk.TkVersion<8.6,'Modern Tk required')
class WishDesktopTests(unittest.TestCase):
    def setUp(self):
        self.directory=tempfile.TemporaryDirectory()
        self.app=SurprisePlannerApplication(TripStore(Path(self.directory.name)/'trips.sqlite3'),FixtureProvider())
        self.root=self.app.create_window();self.root.withdraw();self.panel=self.app.wish_panel
        self.fake=WishFakeClient();self.panel.service=WishService(self.fake)

    def tearDown(self):
        self.app.close()
        for worker in self.app.workers:worker.join(2)
        self.directory.cleanup()

    def text(self,text):
        self.panel.input.delete('1.0','end');self.panel.input.insert('1.0',text);self.root.update()

    def finish(self):
        deadline=time.monotonic()+3
        while self.panel.cancel is not None and time.monotonic()<deadline:self.root.update();time.sleep(.005)
        self.assertIsNone(self.panel.cancel)

    def preview(self,text):self.text(text);self.panel.start();self.finish()

    def choose(self,*fields):
        rows=[p['id'] for p in self.panel.result['accepted'] if p['field'] in fields]
        self.panel.tree.selection_set(rows);self.panel.toggle()

    def test_explicit_preview_unselected_then_subset_apply_without_search(self):
        before=self.app.read_request().to_dict();self.assertFalse(self.fake.calls)
        self.preview('4 Erwachsene; 2 Zimmer; Gruppenbudget: 2400 Euro')
        self.assertEqual(self.app.read_request().to_dict(),before);self.assertFalse(self.panel.selected)
        self.assertEqual(len(self.panel.tree.get_children()),3)
        self.choose('adults');self.panel.apply()
        after=self.app.read_request().to_dict();self.assertEqual(after['adults'],4)
        self.assertEqual(after['rooms'],before['rooms']);self.assertEqual(after['budget'],before['budget'])
        self.assertFalse(self.app.running);self.assertFalse(self.app.trips)
        self.assertEqual(self.app.store.list(),[])

    def test_invalid_selected_combination_has_no_partial_updates(self):
        before=self.panel.snapshot();self.preview('4 Erwachsene; 5 Zimmer');self.choose('adults','rooms');self.panel.apply()
        self.assertEqual(self.panel.snapshot(),before);self.assertIn('Nicht übernommen',self.panel.status.get())
        self.assertIsNotNone(self.panel.result)

    def test_text_change_invalidates_completed_preview(self):
        self.preview('4 Erwachsene');self.choose('adults');self.text('3 Erwachsene')
        self.assertIsNone(self.panel.result);self.assertFalse(self.panel.tree.get_children())
        self.panel.apply();self.assertEqual(self.app.vars['adults'].get(),'2')

    def test_form_change_even_changed_back_invalidates_preview(self):
        self.preview('4 Erwachsene');self.choose('adults')
        old=self.app.vars['budget'].get();self.app.vars['budget'].set('2500');self.app.vars['budget'].set(old)
        self.assertIsNone(self.panel.result);self.panel.apply();self.assertEqual(self.app.vars['adults'].get(),'2')

    def test_late_result_after_new_search_is_discarded(self):
        self.text('4 Erwachsene');serial=self.panel.serial;snapshot=self.panel.snapshot()
        reply=self.panel.service.evaluate('4 Erwachsene');self.app.start_search()
        self.panel.events.put((serial,'4 Erwachsene',snapshot,reply,None));self.panel.poll()
        self.assertIsNone(self.panel.result);self.assertFalse(self.panel.tree.get_children());self.app.cancel_search()

    def test_active_cancel_and_gui_heartbeat(self):
        entered=threading.Event()
        class Slow(WishFakeClient):
            def chat(self,messages,schema=None,cancel=None):
                entered.set()
                while not cancel.wait(.01):pass
                raise InterruptedError('cancelled')
        self.panel.service=WishService(Slow());self.text('4 Erwachsene');before=self.panel.snapshot()
        begin=time.monotonic();self.panel.start();self.assertLess(time.monotonic()-begin,.2);self.assertTrue(entered.wait(1))
        beats=[];self.root.after(1,lambda:beats.append(True));time.sleep(.01);self.root.update();self.assertTrue(beats)
        self.panel.abort();self.app.workers[-1].join(1);self.panel.poll()
        self.assertIsNone(self.panel.result);self.assertEqual(self.panel.snapshot(),before)
        self.assertEqual(self.panel.input.get('1.0','end-1c'),'4 Erwachsene')

    def test_offline_failure_retains_text_form_and_manual_search(self):
        self.fake.error=OSError('offline');before=self.panel.snapshot()
        self.preview('4 Erwachsene');self.assertIsNone(self.panel.result)
        self.assertEqual(self.panel.snapshot(),before);self.assertEqual(self.panel.input.get('1.0','end-1c'),'4 Erwachsene')
        self.assertIn('scripts/local_ai.py start',self.panel.status.get())
        self.app.start_search();deadline=time.monotonic()+3
        while self.app.running and time.monotonic()<deadline:self.root.update();time.sleep(.005)
        self.assertFalse(self.app.running);self.assertTrue(self.app.trips)

    def test_oversize_rejected_without_silent_truncation_or_request(self):
        self.text('x'*2501);self.panel.start()
        self.assertFalse(self.fake.calls);self.assertEqual(len(self.panel.input.get('1.0','end-1c')),2501)
        self.assertIn('2500',self.panel.status.get())

    def test_unknowns_rejections_omissions_visible_and_not_persisted(self):
        self.preview('Im Juli; keine Großstadt; Nicht wandern; 2 Kinder')
        notes=self.panel.notes.get('1.0','end')
        self.assertIn('Jahr',notes);self.assertIn('Großstadt',notes);self.assertIn('Kinder',notes)
        self.assertFalse(self.panel.result['accepted']);self.assertFalse(self.panel.tree.get_children())
        self.assertNotIn('Nicht wandern',self.app.source_log.get('1.0','end'))
        self.assertEqual(self.app.store.list(),[]);self.assertIsNone(self.app.diagnostic)

    def test_edit_during_inference_cancels_and_rejects_late_result(self):
        entered=threading.Event()
        class Pending(WishFakeClient):
            def chat(self,messages,schema=None,cancel=None):
                entered.set()
                while not cancel.wait(.01):pass
                raise InterruptedError('cancelled')
        for edit in ('text','form'):
            with self.subTest(edit=edit):
                entered.clear();self.panel.service=WishService(Pending());self.text('4 Erwachsene')
                self.panel.start();worker=self.app.workers[-1];self.assertTrue(entered.wait(1))
                serial=self.panel.serial;snapshot=self.panel.snapshot()
                if edit=='text':self.text('3 Erwachsene')
                else:self.app.vars['budget'].set('2600')
                worker.join(1);self.panel.poll()
                self.assertFalse(worker.is_alive());self.assertIsNone(self.panel.result)
                reply=WishService(WishFakeClient()).evaluate('4 Erwachsene')
                self.panel.events.put((serial,'4 Erwachsene',snapshot,reply,None));self.panel.poll()
                self.assertFalse(self.panel.tree.get_children());self.assertEqual(self.app.vars['adults'].get(),'2')
