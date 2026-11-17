import copy,tempfile,unittest
from pathlib import Path
from src.vacation_planner.infrastructure.planning.TripStore import TripStore
from src.vacation_planner.infrastructure.planning.LodgingJobStore import LodgingJobStore
from src.vacation_planner.core.planning.LodgingResearch import initialize,finish
from tests.unit.test_surprise_planning import fixture_trip
from tests.unit.test_general_lodging import item

class LodgingJobTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.store=TripStore(Path(self.temp.name)/'trips.db');self.jobs=LodgingJobStore(self.store)
  self.trip=fixture_trip();self.trip.pop('lodging_research',None);self.trip['lodgings']=[item(1),item(2)];initialize(self.trip,[item(i) for i in range(1,26)])
 def tearDown(self):self.temp.cleanup()
 def test_progress_survives_new_store_and_does_not_save_or_modify_trip(self):
  saved=self.store.save('Before',self.trip);before=self.store.load(saved);h=self.jobs.begin(self.trip)
  self.trip['lodging_research']['entries'][3]['state']='running'
  self.jobs.checkpoint(h,self.trip,'paused')
  restarted=LodgingJobStore(TripStore(self.store.path));loaded=restarted.load(h[0])
  self.assertEqual(len(loaded['lodging_research']['entries']),25);self.assertEqual(loaded['lodging_research']['entries'][3]['state'],'cancelled')
  self.assertEqual(self.store.load(saved),before);self.assertEqual(len(self.store.list()),1)
 def test_new_query_and_target_do_not_inherit_ledger(self):
  h=self.jobs.begin(self.trip)
  changed=copy.deepcopy(self.trip);changed['start']='2090-04-01';changed['end']='2090-04-05'
  with self.assertRaises(ValueError):self.jobs.checkpoint(h,changed)
  other=self.jobs.begin(changed);self.assertNotEqual(h[0],other[0]);self.assertEqual(len(self.jobs.list()),2)
  changed=copy.deepcopy(self.trip);changed['destination']['id']='another-target'
  with self.assertRaises(ValueError):self.jobs.checkpoint(h,changed)
 def test_superseded_worker_cannot_overwrite_new_checkpoint(self):
  first=self.jobs.begin(self.trip);second=self.jobs.begin(self.trip)
  finish(self.trip['lodging_research']['entries'][0],'source_error','New result')
  self.assertTrue(self.jobs.checkpoint(second,self.trip,'paused'))
  old=copy.deepcopy(self.trip);old['lodging_research']['entries'][0]['reason']='LATE'
  self.assertFalse(self.jobs.checkpoint(first,old));self.assertEqual(self.jobs.load(first[0])['lodging_research']['entries'][0]['reason'],'New result')
 def test_changed_selection_preserved_while_latest_evidence_arrives(self):
  h=self.jobs.begin(self.trip);selected=copy.deepcopy(self.trip);selected['selected_lodging']=1
  self.jobs.remember_selection(selected)
  finish(self.trip['lodging_research']['entries'][0],'blocked','Source blocked')
  self.jobs.checkpoint(h,self.trip)
  loaded=self.jobs.load(h[0]);self.assertEqual(loaded['selected_lodging'],1);self.assertEqual(loaded['lodging_research']['entries'][0]['state'],'blocked')
 def test_duplicate_ids_and_unrelated_job_delete(self):
  initialize(self.trip,[item(1),item(1)]);self.assertEqual(len(self.trip['lodging_research']['entries']),25)
  h=self.jobs.begin(self.trip);self.jobs.delete(h[0]);self.assertEqual(self.jobs.list(),[])
  self.assertFalse(self.jobs.checkpoint(h,self.trip))

if __name__=='__main__':unittest.main()

class LodgingResumeTests(unittest.TestCase):
 def test_new_process_continuation_keeps_fresh_quote_and_advances_budget_rest(self):
  from src.vacation_planner.infrastructure.planning.LodgingOfferProvider import LodgingOfferProvider
  from src.vacation_planner.core.planning.SearchContext import SearchContext
  from src.vacation_planner.core.planning.OfferResearchService import OfferResearchService
  from src.vacation_planner.infrastructure.planning.Beds24ResponsiveQuote import Beds24ResponsiveQuote
  from tests.unit.test_responsive_lodging import fixture
  from src.vacation_planner.infrastructure.planning.TripStore import timestamp
  seen=[]
  class Sources(LodgingOfferProvider):
   def check_property(self,e,q,t,ctx):
    ctx.check();ctx.calls+=1;seen.append(e['id'])
    if e['id']=='directory:1':
     choice={'718':(2,2),'729':(1,1)}
     o=Beds24ResponsiveQuote.parse(fixture(q,choice),q,e['lodging'],choice,timestamp(),'https://beds24.com/booking2.php?propid=876543',{'propid':'876543'})
     e['offers']=[o.to_dict()];finish(e,'partial','Actual fixture group quote')
    else:finish(e,'source_error','Transient fixture failure')
  with tempfile.TemporaryDirectory() as folder:
   store=TripStore(Path(folder)/'trips.db');jobs=LodgingJobStore(store);trip=fixture_trip();trip.pop('lodging_research',None);trip['lodgings']=[item(1),item(2)]
   initialize(trip,[item(i) for i in range(1,8)])
   result=OfferResearchService([Sources(store)]).research(trip,SearchContext(budget=3),categories=['lodging'])
   h=jobs.begin(result);jobs.checkpoint(h,result,'paused');count=len(seen)
   loaded=LodgingJobStore(TripStore(store.path)).load(h[0]);ctx=SearchContext(budget=3);ctx.lodging_continue=True
   resumed=OfferResearchService([Sources(store)]).research(loaded,ctx,categories=['lodging'])
   self.assertNotIn('directory:1',seen[count:]);self.assertTrue(any(x not in seen[:count] for x in seen[count:]))
   quote=resumed['lodging_research']['entries'][0]['offers'][0]
   self.assertEqual(quote['retrieved_at'],result['lodging_research']['entries'][0]['offers'][0]['retrieved_at'])
   self.assertEqual(resumed['lodging_research']['metrics']['found'],7)

class ChangedQuoteTests(unittest.TestCase):
 def test_date_and_destination_change_invalidate_price_even_before_ttl(self):
  from src.vacation_planner.core.planning.TravelOffers import OfferQuery,expire_offers
  from src.vacation_planner.infrastructure.planning.Beds24ResponsiveQuote import Beds24ResponsiveQuote
  from src.vacation_planner.infrastructure.planning.TripStore import timestamp
  from tests.unit.test_responsive_lodging import fixture
  trip=fixture_trip();q=OfferQuery.from_trip(trip);choice={'718':(2,2),'729':(1,1)}
  offer=Beds24ResponsiveQuote.parse(fixture(q,choice),q,item(),choice,timestamp(),'https://beds24.com/',{'propid':'876543'}).to_dict()
  trip['lodgings'][0].update(offer=offer,price=dict(low=offer['eur_amount'],high=offer['eur_amount'],status='aktuell abgerufen'))
  for field,value in [('start','2090-01-01'),('destination',dict(trip['destination'],name='Another Town'))]:
   changed=copy.deepcopy(trip);changed[field]=value;expire_offers(changed)
   self.assertEqual(changed['lodgings'][0]['price']['status'],'veraltet')

class JobMigrationTests(unittest.TestCase):
 def test_old_progress_table_is_migrated_without_changing_work_or_saved_trips(self):
  import sqlite3,json
  from contextlib import closing
  with tempfile.TemporaryDirectory() as folder:
   store=TripStore(Path(folder)/'trips.db');trip=fixture_trip();initialize(trip)
   path=store.path.with_name(store.path.stem+'-research.sqlite3')
   with closing(sqlite3.connect(path)) as db:
    db.execute('CREATE TABLE lodging_jobs (id TEXT PRIMARY KEY, query_key TEXT, trip_id TEXT, token TEXT, state TEXT, payload TEXT, updated_at TEXT)')
    from src.vacation_planner.core.planning.LodgingResearch import query_key
    from src.vacation_planner.infrastructure.planning.TripStore import timestamp
    db.execute('INSERT INTO lodging_jobs VALUES (?,?,?,?,?,?,?)',('old',query_key(trip),trip['id'],'old-token','paused',json.dumps(trip),timestamp()))
    db.commit()
   jobs=LodgingJobStore(store);rows=jobs.list();self.assertEqual(rows[0]['id'],'old');self.assertEqual(jobs.load('old')['id'],trip['id'])
   with jobs.connect() as db:summary=db.execute('SELECT summary FROM lodging_jobs WHERE id=?',('old',)).fetchone()[0]
   self.assertNotEqual(summary,'{}');self.assertEqual(store.list(),[])
