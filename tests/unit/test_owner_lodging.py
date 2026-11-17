"""Owner overview discovery uses observed leaf IDs and independent identities."""
import copy,unittest
from urllib.parse import urlsplit
from src.vacation_planner.core.planning.TravelOffers import OfferQuery
from src.vacation_planner.core.planning.SearchContext import SearchContext
from src.vacation_planner.core.planning.OfferResearchService import OfferResearchService
from src.vacation_planner.infrastructure.planning.LodgingOfferProvider import LodgingOfferProvider
from src.vacation_planner.infrastructure.planning.LodgingSourcePolicy import LodgingSourcePolicy
from src.vacation_planner.infrastructure.planning.Beds24ResponsiveQuote import Beds24ResponsiveQuote
from src.vacation_planner.infrastructure.planning.Beds24RoomSelection import selections
from tests.unit.test_general_lodging import item
from tests.unit.test_responsive_lodging import inventory,fixture
from tests.unit.test_surprise_planning import fixture_trip
import tests.unit.test_source_research as wire

class OwnerWireTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):wire.ResearchTests.setUpClass()
 @classmethod
 def tearDownClass(cls):wire.ResearchTests.tearDownClass()
 def test_observed_owner_to_leaf_quote_through_real_local_http(self):self.run_case(False,False)
 def test_direct_owner_seed_resolves_identity_at_leaf_not_brand(self):self.run_case(True,False)
 def test_same_owner_brand_cannot_confirm_different_property(self):self.run_case(True,True)
 def run_case(self,direct,wrong):
  f=wire.ResearchTests('test_real_fixture_http_identity_provenance_and_no_trip_mutation');f.setUp()
  try:
   trip=fixture_trip();trip.pop('lodging_research',None);house=item();trip['lodgings']=[house];trip['selected_lodging']=0
   owner='https://beds24.com/booking2.php?ownerid=918273';leaf='https://beds24.com/booking2.php?propid=876543'
   if direct:house['url']=owner
   q=OfferQuery.from_trip(trip);h=inventory(q).replace('</form>','<select name="sr1-729"><option value="0">0</option><option value="1">1</option></select><select name="naa1-1-729"><option value="1">1</option></select></form>')
   policy=LodgingSourcePolicy(house['url'],house);policy.booking_link(owner);policy.booking_link(leaf)
   from datetime import date
   params=dict(propid='876543',checkin=q.start,numnight=str((date.fromisoformat(q.end)-date.fromisoformat(q.start)).days),numadult=str(q.adults),numchild='0',lang='de',multiroom='1')
   initial=policy.query(leaf,params);rooms,fields,multi=Beds24ResponsiveQuote.inventory(h,q);choice=selections(rooms,q.room_assignments,limit=2)[0]
   selected=policy.responsive_query(leaf,Beds24ResponsiveQuote.parameters(params,rooms,fields,multi,choice),fields,multi)
   for host in ('house1.example','beds24.com'):f.routes[host,'/robots.txt']=(404,'text/plain','',{})
   pages=[(owner,'<h1>Independent House 1</h1><a href="'+leaf+'">Object</a>'),
          (leaf,'<h1>Independent House '+('2' if wrong else '1')+'</h1>12345'),
          (initial,h+'12345'),(selected,fixture(q,{'718':(2,2),'729':(1,1)}))]
   if not direct:pages.append((house['url'],'<h1>Independent House 1</h1>12345<a href="'+owner+'">Book</a>'))
   for url,body in pages:
    p=urlsplit(url);f.routes[p.hostname,p.path+('?'+p.query if p.query else '')]=(200,'text/html',body,{})
   def factory(p):f.http.policy=p;return f.http
   ctx=SearchContext(budget=12);ctx.wait=lambda _:ctx.check()
   result=OfferResearchService([LodgingOfferProvider(f.store,http_factory=factory)]).research(trip,ctx,categories=['lodging'])
   entry=result['lodging_research']['entries'][0]
   if wrong:
    self.assertFalse(entry['offers']);self.assertFalse(entry['official_website']);self.assertIn('nicht durch Name',entry['reason']);self.assertEqual(entry['selection_responses'],0)
   else:
    self.assertEqual(entry['state'],'partial');o=entry['offers'][0]
    self.assertEqual(o['eur_amount'],'325.00');self.assertEqual(o['evidence']['discovery_variant'],'owner-property-list-v1')
    self.assertEqual(o['evidence']['owner_source']['observed_property_url'],leaf);self.assertTrue(entry['official_website'])
    self.assertEqual(entry['selection_responses'],1)
  finally:f.tearDown()

if __name__=='__main__':unittest.main()
