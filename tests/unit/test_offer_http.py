"""Local HTTP fixtures exercise the real safe transport gates, not production bypasses."""
import json
import unittest
from unittest.mock import patch
from src.vacation_planner.infrastructure.planning.ResearchHttp import ResearchHttp
from src.vacation_planner.core.planning.SearchContext import SearchContext
from src.vacation_planner.infrastructure.planning.RegioJetOfferProvider import RegioJetOfferProvider
import tests.unit.test_source_research as fixture

URL='https://brn-ybus-pubapi.sa.cz/restapi/consts/locations'


class OfferHttpTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):fixture.ResearchTests.setUpClass()
 @classmethod
 def tearDownClass(cls):fixture.ResearchTests.tearDownClass()
 def setUp(self):
  self.f=fixture.ResearchTests('test_real_fixture_http_identity_provenance_and_no_trip_mutation');self.f.setUp()
  self.f.routes['brn-ybus-pubapi.sa.cz','/robots.txt']=(404,'text/plain','',{})
  self.f.routes['brn-ybus-pubapi.sa.cz','/restapi/consts/locations']=(200,'application/json','[]',{})
 def tearDown(self):self.f.tearDown()
 def test_readonly_price_paths_and_queries_only(self):
  good=[URL,'https://booking.smoobu.com/perfect-lodgings/checkAvailability?theme=booking-tool&arrivalDate=23.11.26&departureDate=25.11.26&userId=71379&guests=2&adults=2&children=0',
   'https://brn-ybus-pubapi.sa.cz/restapi/routes/search/simple?fromLocationId=123&fromLocationType=CITY&toLocationId=456&toLocationType=CITY&departureDate=2026-11-12&tariffs=REGULAR',
   'https://brn-ybus-pubapi.sa.cz/restapi/routes/123/simple?fromStationId=1&toStationId=2&tariffs=REGULAR']
  for url in good:self.assertEqual(ResearchHttp.validate_url(url),url)
  for url in (URL+'?token=secret',URL.replace('/consts/locations','/tickets/book'),good[1].replace('userId=71379','userId=1'),good[2]+'&callback=http://127.0.0.1',good[3].replace('tariffs=REGULAR','tariffs=PRIVATE'),URL.replace('https:','http:'),URL.replace('brn-ybus-pubapi.sa.cz','127.0.0.1')):
   with self.subTest(url=url),self.assertRaises(ValueError):ResearchHttp.validate_url(url)
 def test_unknown_headers_never_transmitted(self):
  for headers in ({'Authorization':'secret'},{'X-Currency':'USD'},{'Cookie':'session'},{'X-Lang':'en\nInjection'}):
   with self.assertRaises(ValueError):self.f.http.fetch(URL,SearchContext(),headers=headers)
  self.assertFalse(self.f.http.audit)
 def test_public_api_headers_reach_bound_wire_and_cache_is_separate(self):
  wire=self.f.http._wire;seen=[]
  def capture(url,ip,context,maximum,headers=None):
   seen.append(headers);return wire(url,ip,context,maximum)
  with patch.object(self.f.http,'_wire',side_effect=capture):
   data,stamp=self.f.http.json(URL,SearchContext(),headers=RegioJetOfferProvider.HEADERS)
  self.assertEqual(data,[]);self.assertEqual(seen[-1],RegioJetOfferProvider.HEADERS);self.assertIsNone(seen[0])
 def test_robots_html_response_blocks_before_offer_query(self):
  self.f.routes['brn-ybus-pubapi.sa.cz','/robots.txt']=(200,'text/html','<html>not rules</html>',{})
  with self.assertRaises(ValueError):self.f.http.fetch(URL,SearchContext())
  self.assertEqual(len(self.f.http.audit),1)
 def test_price_redirect_to_internal_or_unknown_path_blocked(self):
  self.f.routes['brn-ybus-pubapi.sa.cz','/restapi/consts/locations']=(302,'text/html','',dict(Location='https://127.0.0.1/private'))
  with self.assertRaises(ValueError):self.f.http.fetch(URL,SearchContext())
 def test_shared_budget_and_cached_response_keep_original_stamp(self):
  c=SearchContext(budget=2);first=self.f.http.fetch(URL,c);second=self.f.http.fetch(URL,c)
  self.assertEqual(c.calls,2);self.assertEqual(first['retrieved_at'],second['retrieved_at']);self.assertTrue(second['cache_used'])
 def test_blocked_api_not_retried(self):
  self.f.routes['brn-ybus-pubapi.sa.cz','/restapi/consts/locations']=(429,'application/json','{}',{})
  c=SearchContext()
  with self.assertRaises(OSError):self.f.http.fetch(URL,c)
  before=c.calls
  with self.assertRaises(OSError):self.f.http.fetch(URL,c)
  self.assertEqual(before,c.calls)
 def test_ambiguous_station_city_does_not_use_first_match(self):
  data=[dict(cities=[dict(id=1,name='Testort',stationsTypes=['TRAIN_STATION']),dict(id=2,name='Testort',stationsTypes=['TRAIN_STATION'])])]
  self.assertIsNone(RegioJetOfferProvider.city(data,'Testort'))
