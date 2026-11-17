import tempfile,time,unittest,copy
from pathlib import Path
from unittest.mock import patch
from src.vacation_planner.entrypoints.gui.SurprisePlannerApplication import SurprisePlannerApplication
from src.vacation_planner.infrastructure.planning.TripStore import TripStore
from src.vacation_planner.infrastructure.planning.OpenTravelProvider import OpenTravelProvider
from src.vacation_planner.infrastructure.planning.LodgingOfferProvider import LodgingOfferProvider
from src.vacation_planner.core.planning.LodgingResearch import initialize,finish
from tests.unit.test_surprise_planning import FixtureProvider,fixture_trip
from tests.unit.test_general_lodging import item

class ResearchJobsDesktopTests(unittest.TestCase):
 def test_real_service_checkpoint_restart_open_then_resume_with_fair_progress(self):
  with tempfile.TemporaryDirectory() as folder:
   store=TripStore(Path(folder)/'trips.db');trip=fixture_trip();trip.pop('lodging_research',None);trip['lodgings']=[item(1),item(2)]
   initialize(trip,[item(i) for i in range(1,71)]);saved=store.save('Existing trip',trip);before=store.load(saved)
   seen=[]
   def source(self,e,q,t,c):
    c.check();seen.append(e['id']);finish(e,'source_error','Temporary public-source failure')
   def load(app,trip):
    app.trips[trip['id']]=trip;app.update_row(trip);app.tree.selection_set(trip['id']);app.select_trip()
   def wait(app):
    until=time.monotonic()+5
    while app.price_context and time.monotonic()<until:app.root.update();time.sleep(.01)
    self.assertFalse(app.price_context)
   app=SurprisePlannerApplication(store,FixtureProvider());root=app.create_window();root.withdraw()
   app.provider=OpenTravelProvider(store,catalog=app.catalog);load(app,trip);app.price_category.set('Unterkunft')
   with patch.object(LodgingOfferProvider,'check_property',source):app.research_prices();wait(app)
   jobs=app.research_jobs.store.list();self.assertEqual(len(jobs),1);first=set(seen);self.assertEqual(len(first),64)
   self.assertEqual(store.load(saved),before);self.assertEqual(len(store.list()),1)
   app.close()
   for w in app.workers:w.join(2)
   restarted=SurprisePlannerApplication(TripStore(store.path),FixtureProvider());root=restarted.create_window();root.withdraw();restarted.provider=OpenTravelProvider(restarted.store,catalog=restarted.catalog)
   panel=restarted.research_jobs;self.assertEqual(len(panel.tree.get_children()),1);panel.tree.selection_set(jobs[0]['id']);count=len(seen)
   panel.open();self.assertEqual(len(seen),count);self.assertEqual(len(restarted.active['lodging_research']['entries']),70);self.assertIsNone(restarted.saved_id)
   with patch.object(LodgingOfferProvider,'check_property',source):restarted.research_prices(lodging_continue=True);wait(restarted)
   self.assertTrue(any(x not in first for x in seen[count:]));self.assertEqual(store.load(saved),before)
   restarted.close()
   for w in restarted.workers:w.join(2)

class ResearchCancellationDesktopTests(unittest.TestCase):
 def test_close_cancel_and_late_event_preserve_durable_work_and_saved_snapshot(self):
  import threading
  with tempfile.TemporaryDirectory() as folder:
   store=TripStore(Path(folder)/'trips.db');app=SurprisePlannerApplication(store,FixtureProvider());root=app.create_window();root.withdraw()
   app.provider=OpenTravelProvider(store,catalog=app.catalog);trip=fixture_trip();trip.pop('lodging_research',None);trip['lodgings']=[item(1),item(2)];initialize(trip)
   app.trips[trip['id']]=trip;app.update_row(trip);app.tree.selection_set(trip['id']);app.select_trip()
   entered=threading.Event();seen=[]
   def waiting(self,e,q,t,c):
    seen.append(e['id'])
    if len(seen)>1:
     entered.set()
     while True:c.wait(.01)
    finish(e,'source_error','First completed source')
   app.price_category.set('Unterkunft')
   with patch.object(LodgingOfferProvider,'check_property',waiting):
    app.research_prices();until=time.monotonic()+4
    while not entered.is_set() and time.monotonic()<until:root.update();time.sleep(.01)
    self.assertTrue(entered.is_set());app.cancel_search();app.close()
    for worker in app.workers:worker.join(2);self.assertFalse(worker.is_alive())
   jobs=app.research_jobs.store.list();self.assertEqual(jobs[0]['state'],'paused')
   loaded=app.research_jobs.store.load(jobs[0]['id']);entries=loaded['lodging_research']['entries']
   self.assertEqual(entries[0]['reason'],'First completed source');self.assertEqual(entries[1]['state'],'cancelled')
   self.assertEqual(store.list(),[])
