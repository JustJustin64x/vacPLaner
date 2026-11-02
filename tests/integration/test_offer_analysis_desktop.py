import copy,tempfile,threading,time,tkinter as tk,unittest
from pathlib import Path
from src.vacation_planner.entrypoints.gui.SurprisePlannerApplication import SurprisePlannerApplication
from src.vacation_planner.infrastructure.planning.TripStore import TripStore
from src.vacation_planner.core.planning.SearchRequest import SearchRequest
from tests.unit.test_surprise_planning import FixtureProvider,fixture_trip


@unittest.skipIf(tk.TkVersion<8.6,'Modern Tk required')
class OfferDesktopTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.app=SurprisePlannerApplication(TripStore(Path(self.temp.name)/'trip.sqlite3'),FixtureProvider());self.root=self.app.create_window();self.root.withdraw()
  t=fixture_trip();self.app.trips[t['id']]=t;self.app.update_row(t);self.app.tree.selection_set(t['id']);self.app.select_trip()
 def tearDown(self):
  self.app.close()
  for w in self.app.workers:w.join(2)
  self.temp.cleanup()
 def test_old_form_defaults_off_and_option_roundtrip(self):
  q=SearchRequest(earliest='2090-07-01',latest='2090-07-31',ai_offer_analysis=True);self.app.populate_request(q.to_dict());self.assertTrue(self.app.read_request().ai_offer_analysis)
  old=q.to_dict();old.pop('ai_offer_analysis');self.app.populate_request(old);self.assertFalse(self.app.read_request().ai_offer_analysis)
 def test_explicit_price_action_and_unchanged_saved_snapshot(self):
  app=self.app;saved=app.store.save('Before',app.active);before=app.store.load(saved);app.vars['ai_offer_analysis'].set('ja');seen=[]
  class Provider(FixtureProvider):
   def research_offers(self,t,c,emit,categories,samples=False):
    seen.append(t['request']['ai_offer_analysis']);t['offer_analysis']=dict(status='selected',accepted=[],model_calls=1);return t
  app.provider=Provider();app.research_prices();app.workers[-1].join(2);app.poll()
  self.assertEqual(seen,[True]);self.assertIn('Vorhandene Fundstellen lokal ausgewählt',app.details.get('1.0','end'));self.assertEqual(app.store.load(saved),before)
 def test_late_price_analysis_after_cancel_cannot_replace_new_result(self):
  app=self.app;old=app.generation;t=copy.deepcopy(app.active);t['offer_analysis']=dict(status='selected',accepted=[])
  app.cancel_search();app.events.put((old,'price_result',t));app.events.put((old,'price_done',None));app.poll();self.assertNotIn('offer_analysis',app.active)
 def test_result_for_another_target_does_not_replace_selection(self):
  app=self.app;old=copy.deepcopy(app.active);other=copy.deepcopy(old);other['id']='other';other['destination']['name']='Other'
  app.trips[other['id']]=other;app.update_row(other);app.tree.selection_set(other['id']);app.select_trip();old['offer_analysis']=dict(status='selected',accepted=[])
  app.events.put((app.generation,'price_result',old));app.poll();self.assertEqual(app.active['id'],'other');self.assertNotIn('offer_analysis',app.active)
