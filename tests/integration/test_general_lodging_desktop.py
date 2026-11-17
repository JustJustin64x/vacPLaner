import copy,tempfile,time,tkinter as tk,unittest
from pathlib import Path
from unittest.mock import patch
from src.vacation_planner.entrypoints.gui.SurprisePlannerApplication import SurprisePlannerApplication
from src.vacation_planner.infrastructure.planning.TripStore import TripStore
from src.vacation_planner.infrastructure.planning.LodgingOfferProvider import LodgingOfferProvider
from src.vacation_planner.core.planning.LodgingResearch import initialize
from tests.unit.test_surprise_planning import FixtureProvider,fixture_trip
from tests.unit.test_general_lodging import item

@unittest.skipIf(tk.TkVersion<8.6,'Modern Tk required')
class GeneralLodgingDesktopTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.store=TripStore(Path(self.temp.name)/'trips.sqlite3')
  self.app=SurprisePlannerApplication(self.store,FixtureProvider());self.root=self.app.create_window();self.root.withdraw()
  t=fixture_trip();t.pop('lodging_research',None)
  t['lodgings']=[item(1),item(2)];t['selected_lodging']=0
  for row in t['lodgings']:row['url']=row['source']
  for n in range(1,21):
   row=item(n);row['url']=row['source']
   initialize(t,[row])
  self.app.trips[t['id']]=t;self.app.update_row(t);self.app.tree.selection_set(t['id']);self.app.select_trip()
 def tearDown(self):
  self.app.close()
  for w in self.app.workers:w.join(2)
  self.temp.cleanup()
 def test_normal_continue_action_updates_all_rows_and_keeps_saved_snapshot(self):
  app=self.app;saved=self.store.save('Before',app.active);before=self.store.load(saved);seen=[]
  class Provider(FixtureProvider):
   def research_offers(_,trip,context,emit,categories,samples=False):
    seen.append((context.lodging_continue,categories))
    from src.vacation_planner.core.planning.OfferResearchService import OfferResearchService
    return OfferResearchService([LodgingOfferProvider(self.store,emit)]).research(trip,context,emit,categories)
  app.provider=Provider();app.research_prices(lodging_continue=True)
  until=time.monotonic()+5
  while app.price_context and time.monotonic()<until:self.root.update();time.sleep(.01)
  self.assertFalse(app.price_context);self.assertEqual(seen,[(True,['lodging'])])
  self.assertEqual(app.active['lodging_research']['metrics']['found'],20)
  self.assertIn('Independent House 20',app.details.get('1.0','end'))
  self.assertEqual(self.store.load(saved),before)
  with patch('src.vacation_planner.entrypoints.gui.SurprisePlannerApplication.simpledialog.askstring',return_value='After'):
   app.save_trip()
  self.assertEqual(len(self.store.load(app.saved_id)['lodging_research']['entries']),20)
 def test_cancelled_late_ledger_cannot_replace_current_target(self):
  app=self.app;old=app.generation;t=copy.deepcopy(app.active);t['lodging_research']['entries'][0]['reason']='LATE'
  app.cancel_search();app.events.put((old,'price_offer_partial',t));app.poll()
  self.assertNotEqual(app.active['lodging_research']['entries'][0]['reason'],'LATE')
 def test_all_properties_window_has_every_row_and_updates_same_target(self):
  app=self.app;app.show_lodging_research();view=app.lodging_window;view.window.withdraw()
  self.assertEqual(len(view.tree.get_children()),20)
  view.tree.selection_set('directory:20');view.show_entry();self.assertIn('Independent House 20',view.detail.get('1.0','end'))
  other=copy.deepcopy(app.active);other['id']='other';other['lodging_research']['entries']=[]
  view.refresh(other);self.assertEqual(len(view.tree.get_children()),20)
 def test_reordered_progress_preserves_selected_property(self):
  app=self.app;t=copy.deepcopy(app.active);t['lodgings'].reverse()
  selected=app.active['lodgings'][app.active['selected_lodging']]['id']
  app.events.put((app.generation,'offer_partial',t));app.poll()
  self.assertEqual(app.active['lodgings'][app.active['selected_lodging']]['id'],selected)
 def test_responsive_quote_fees_and_saved_rooms_in_normal_price_action(self):
  from tests.unit.test_responsive_lodging import fixture as responsive_fixture
  from src.vacation_planner.infrastructure.planning.Beds24ResponsiveQuote import Beds24ResponsiveQuote
  from src.vacation_planner.core.planning.TravelOffers import OfferQuery
  from src.vacation_planner.core.planning.LodgingResearch import finish
  from src.vacation_planner.infrastructure.planning.TripStore import timestamp
  class Prices(LodgingOfferProvider):
   def check_property(_,e,q,t,c):
    if e['id']!='directory:1':finish(e,'no_booking_source','Fixture without source');return
    choice={'718':(2,2),'729':(1,1)}
    o=Beds24ResponsiveQuote.parse(responsive_fixture(q,choice),q,e['lodging'],choice,timestamp(),'https://beds24.com/booking2.php?propid=876543',{'propid':'876543'})
    e.update(offers=[o.to_dict()],system='Beds24',variant= Beds24ResponsiveQuote.variant);finish(e,'partial','Fixture selection')
  class Provider(FixtureProvider):
   def research_offers(_,trip,context,emit,categories,samples=False):
    from src.vacation_planner.core.planning.OfferResearchService import OfferResearchService
    return OfferResearchService([Prices(self.store,emit)]).research(trip,context,emit,categories)
  app=self.app;app.provider=Provider();app.price_category.set('Unterkunft');app.research_prices()
  until=time.monotonic()+5
  while app.price_context and time.monotonic()<until:self.root.update();time.sleep(.01)
  self.assertFalse(app.price_context)
  text=app.details.get('1.0','end');self.assertIn('325.00',text);self.assertIn('Cleaning',text);self.assertIn('25.00',text)
  with patch('src.vacation_planner.entrypoints.gui.SurprisePlannerApplication.simpledialog.askstring',return_value='Responsive'):
   app.save_trip()
  saved=self.store.load(app.saved_id);o=saved['lodging_research']['entries'][0]['offers'][0]
  self.assertEqual(o['details']['units'],3);self.assertEqual(o['evidence']['system_variant'],'responsive-selection-v1')
