import copy
import json
import tempfile
import threading
import time
import unittest
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch
from zoneinfo import ZoneInfo

from src.vacation_planner.core.planning.SearchRequest import SearchRequest
from src.vacation_planner.core.planning.SearchContext import SearchContext
from src.vacation_planner.core.planning.CostItem import CostItem
from src.vacation_planner.core.planning.CostService import CostService
from src.vacation_planner.core.planning.DiscoveryService import DiscoveryService
from src.vacation_planner.core.planning.RankingService import RankingService
from src.vacation_planner.infrastructure.planning.TripStore import TripStore
from src.vacation_planner.infrastructure.planning.DestinationCatalog import DestinationCatalog
from src.vacation_planner.infrastructure.planning.WikivoyageParser import WikivoyageParser, safe_url
from src.vacation_planner.infrastructure.planning.PublicHttpClient import PublicHttpClient
from src.vacation_planner.infrastructure.planning.OpenTravelProvider import OpenTravelProvider
from src.vacation_planner.entrypoints.gui.TripPresenter import TripPresenter, local_stamp

FIXTURES=Path(__file__).resolve().parents[1]/'fixtures'


def request(**kwargs):
    return SearchRequest(earliest='2090-07-01',latest='2090-07-31',**kwargs)


class FixtureProvider:
    def __init__(self,fail_route=False):
        self.fail_route=fail_route
    def origin(self,*args):
        return dict(name='Berlin',latitude=52.52,longitude=13.405,precision='Ortszentrum')
    def places(self,destination,context):
        result=WikivoyageParser().parse((FIXTURES/'bled-vcards.html').read_text(),destination,'2026-10-27T12:00:00+00:00')
        return dict(result,cache_note='TEST fixture',warnings=[])
    def route(self,*args):
        if self.fail_route:raise OSError('Route offline')
        return dict(legs=[dict(distance=500000,duration=18000),dict(distance=510000,duration=18100)],
                    source='https://example.org/fixture',retrieved_at='2026-10-27T12:00:00+00:00',precision='Ortszentrum')


def fixture_trip():
    catalog=DestinationCatalog()
    catalog.destinations=[catalog.resolve('Bled')]
    return DiscoveryService(catalog,FixtureProvider()).search(request(adults=5,rooms=3),SearchContext(),lambda *args:None)[0]


class SearchRequestTests(unittest.TestCase):
    def test_next_july_is_future(self):
        from src.vacation_planner.core.planning.SearchRequest import next_july
        with patch('src.vacation_planner.core.planning.SearchRequest.today',return_value=date(2026,10,27)):
            self.assertEqual(next_july(),('2027-07-01','2027-07-31'))

    def test_days_nights_and_flexible_dates(self):
        r=request(min_days=5,max_days=9)
        r.validate()
        self.assertLessEqual(len(r.dates()),3)
        for start,end in r.dates():
            self.assertTrue(r.earliest<=start<=end<=r.latest)
            self.assertTrue(4 <= (date.fromisoformat(end)-date.fromisoformat(start)).days <= 8)
        self.assertEqual((date.fromisoformat(request().dates()[0][1])-date.fromisoformat(request().dates()[0][0])).days,6)

    def test_too_short_window(self):
        r=request();r.latest='2090-07-05'
        with self.assertRaises(ValueError):r.validate()

    def test_vehicle_capacity(self):
        with self.assertRaises(ValueError):request(adults=6,cars=1,seats=5).validate()
        request(adults=6,cars=2,seats=3).validate()
        request(adults=6,cars=0,modes=['Zug']).validate()

    def test_rooms_occupancy(self):
        self.assertEqual(request(adults=5,rooms=3).room_occupancy(),[2,2,1])
        with self.assertRaises(ValueError):request(adults=2,rooms=3).validate()

    def test_weight_normalization_and_zero(self):
        self.assertEqual(sum(request().normalized_weights().values()),1)
        self.assertEqual(set(request(weights={}).normalized_weights().values()),{Decimal('.25')})

    def test_invalid_numbers(self):
        for number in ('NaN','Infinity','-3','0'):
            with self.subTest(number=number),self.assertRaises(ValueError):request(budget=number).validate()

    def test_country_region_exclusions(self):
        cat=DestinationCatalog()
        candidates=cat.candidates(request(countries=['AT'],regions=['Alpen'],excluded=['Innsbruck']))
        self.assertTrue(candidates)
        self.assertTrue(all(c['code']=='AT' and c['region']=='Alpen' and c['name']!='Innsbruck' for c in candidates))
        self.assertGreater(len(cat.destinations),50)
        self.assertGreater(len({c['country'] for c in cat.destinations}),20)


class CostTests(unittest.TestCase):
    def test_all_vehicles_round_trip_fuel(self):
        result=CostService.fuel(1000,request(adults=8,cars=2,consumption='8',petrol='2'),'', '', '2090-07-01','2090-07-07')
        self.assertEqual(result['low'],'288.00')
        self.assertEqual(result['high'],'384.00')

    def test_unknown_not_free_and_optional_excluded(self):
        items=[CostItem('Transport','100','100','aktuell abgerufen').to_dict(),CostItem('Unterkunft').to_dict(),
               CostItem('Essen','300','300','aktuell abgerufen',optional=True).to_dict()]
        s=CostService.summarize(items,'200')
        self.assertEqual(s['status'],'Teilsumme')
        self.assertEqual(s['low'],'100.00')
        self.assertIsNone(s['budget_ok'])
        self.assertIsNone(s['budget_delta'])
        self.assertEqual(s['missing'],['Unterkunft'])

    def test_full_estimate_budget_delta(self):
        items=[CostItem('Hotel','990','1100','geschätzt',method='documented fixture').to_dict()]
        s=CostService.summarize(items,'1000')
        self.assertEqual(s['status'],'Schätzspanne')
        self.assertFalse(s['budget_ok'])
        self.assertEqual(s['budget_delta'],'100.00')

    def test_stale_price_is_not_current_total(self):
        s=CostService.summarize([CostItem('Hotel','100','100','veraltet').to_dict()],'200')
        self.assertEqual(s['coverage'],0)
        self.assertIsNone(s['budget_ok'])

    def test_explicit_normalization_and_camping(self):
        self.assertEqual(CostService.normalize('80','Zimmer/Nacht',5,3,6,capacity=6),Decimal('1440'))
        self.assertEqual(CostService.normalize('20','Bett/Nacht',5,3,6,capacity=5),Decimal('600'))
        with self.assertRaises(ValueError):CostService.normalize('80','Zimmer/Nacht',5,3,6)
        with self.assertRaises(ValueError):CostService.normalize('20','Stellplatz/Nacht',5,3,6,capacity=6)

    def test_vignette_validity_inclusive(self):
        self.assertEqual(CostService.vignette_count(date(2090,7,1),date(2090,7,7),10),1)
        self.assertEqual(CostService.vignette_count(date(2090,7,1),date(2090,7,10),10),1)
        self.assertEqual(CostService.vignette_count(date(2090,7,1),date(2090,7,11),10),2)

    def test_bad_estimates_rejected(self):
        with self.assertRaises(ValueError):CostItem('x','1','2','geschätzt')
        with self.assertRaises(ValueError):CostItem('x','2','1','aktuell abgerufen')
        with self.assertRaises(ValueError):CostItem('x','0')


class ParserAndSearchTests(unittest.TestCase):
    def test_real_listings_no_prices_or_events_inferred(self):
        parsed=FixtureProvider().places(DestinationCatalog().resolve('Bled'),SearchContext())
        self.assertGreaterEqual(len(parsed['lodgings']),2)
        names=[l['name'] for l in parsed['lodgings']]
        self.assertIn('Grand Hotel Toplice',names)
        self.assertTrue(all(l['price']['low'] is None for l in parsed['lodgings']))
        self.assertFalse(any(a['type'] in ('event','festival') for a in parsed['activities']))
        self.assertTrue(any('Baden' in a['topics'] for a in parsed['activities']))
        self.assertEqual(next(l for l in parsed['lodgings'] if l['name']=='Camping Bled')['type'],'Camping')

    def test_dedupe_same_identity_not_different_places(self):
        card='<div class="vcard" data-name="Hotel" data-group="sleep" data-type="hotel" data-wikidata="{id}"></div>'
        result=WikivoyageParser().parse(card.format(id='Q1')*2+card.format(id='Q2'),DestinationCatalog().resolve('Bled'),'')
        self.assertEqual(len(result['lodgings']),2)

    def test_unsafe_provider_links_rejected(self):
        self.assertEqual(safe_url('javascript:alert(1)'), '')
        self.assertEqual(safe_url('file:///etc/passwd'), '')
        self.assertEqual(safe_url('https://example.org'), 'https://example.org')

    def test_end_to_end_real_identity_fixture_group_scope(self):
        trip=fixture_trip()
        self.assertGreaterEqual(len(trip['lodgings']),2)
        self.assertEqual(trip['nights'],6)
        self.assertEqual(trip['lodgings'][0]['requested_occupancy'],[2,2,1])
        self.assertEqual(len(trip['transports']),3)
        self.assertIsNone(trip['cost_summary']['budget_ok'])
        self.assertIn('group_adults=5',trip['lodgings'][0]['search_url'])
        self.assertIn('no_rooms=3',trip['lodgings'][0]['search_url'])

    def test_transport_swap_does_not_reward_unknown_price(self):
        trip=fixture_trip();auto=trip['score']
        trip['selected_transport']=1;RankingService.recompute(trip)
        self.assertLessEqual(trip['score'],auto)
        self.assertEqual(trip['cost_summary']['coverage'],0)
        self.assertIsNone(trip['cost_summary']['budget_ok'])
        self.assertNotIn('Benzin',str(trip['costs']))

    def test_lodging_swap_recalculates_costs(self):
        trip=fixture_trip()
        trip['lodgings'][1]['price']=CostItem('Fixture accommodation','700','700','aktuell abgerufen').to_dict()
        before=Decimal(trip['cost_summary']['low'])
        trip['selected_lodging']=1;RankingService.recompute(trip)
        self.assertEqual(Decimal(trip['cost_summary']['low']),before+700)
        self.assertIn(trip['lodgings'][1]['name'],str(TripPresenter.sections(trip)))

    def test_provider_outage_leaves_honest_results(self):
        cat=DestinationCatalog();cat.destinations=[cat.resolve('Bled')]
        out=DiscoveryService(cat,FixtureProvider(True)).search(request(),SearchContext(),lambda *args:None)
        self.assertEqual(len(out),1)
        self.assertEqual(out[0]['cost_summary']['coverage'],0)

    def test_unknown_mandatory_amenities_exclude(self):
        cat=DestinationCatalog();cat.destinations=[cat.resolve('Bled')]
        out=DiscoveryService(cat,FixtureProvider()).search(request(required=['Pool']),SearchContext(),lambda *args:None)
        self.assertEqual(out,[])

    def test_max_time_is_hard_filter(self):
        cat=DestinationCatalog();cat.destinations=[cat.resolve('Bled')]
        out=DiscoveryService(cat,FixtureProvider()).search(request(max_hours='2'),SearchContext(),lambda *args:None)
        self.assertEqual(out,[])

    def test_actual_osrm_fixture_two_legs(self):
        route=json.loads((FIXTURES/'live_route.json').read_text())
        self.assertEqual(route['code'],'Ok')
        self.assertEqual(len(route['routes'][0]['legs']),2)
        self.assertGreater(route['routes'][0]['distance'],1000000)


class LifecycleTests(unittest.TestCase):
    def test_persistence_after_reopen_modify_duplicate_delete(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'test.sqlite3'
            store=TripStore(path);trip=fixture_trip()
            identifier=store.save('Juli äöü',trip)
            store=TripStore(path)
            loaded=store.load(identifier)
            self.assertEqual(loaded['request']['adults'],5)
            self.assertEqual(loaded['researched_at'],trip['researched_at'])
            loaded['selected_transport']=1
            store.save('Änderung',loaded,identifier)
            duplicate=store.duplicate(identifier,'Kopie')
            store.delete(identifier)
            self.assertEqual(len(store.list()),1)
            self.assertEqual(store.load(duplicate)['selected_transport'],1)
            with self.assertRaises(KeyError):store.load(identifier)

    def test_cache_is_separate_from_saved_trips(self):
        with tempfile.TemporaryDirectory() as directory:
            store=TripStore(Path(directory)/'test.sqlite3')
            store.cache_set('x',{'data':1},'2000-01-01T00:00:00+00:00')
            self.assertIsNone(store.cache_get('x',60))
            self.assertEqual(store.cache_get('x')[0],{'data':1})
            self.assertEqual(store.list(),[])

    def test_budget_and_cancel(self):
        context=SearchContext(budget=1)
        context.consume()
        with self.assertRaises(InterruptedError):context.consume()
        context=SearchContext();context.cancel.set()
        with self.assertRaises(InterruptedError):context.check()
        context=SearchContext(seconds=-1)
        with self.assertRaises(InterruptedError):context.check()

    def test_wait_can_be_cancelled(self):
        context=SearchContext()
        timer=threading.Timer(.03,context.cancel.set);timer.start()
        started=time.monotonic()
        with self.assertRaises(InterruptedError):context.wait(10)
        self.assertLess(time.monotonic()-started,.5)
        timer.join()

    def test_blocked_host_never_retried(self):
        context=SearchContext();context.disabled.add('example.org')
        with patch('subprocess.Popen') as process:
            with self.assertRaises(OSError):PublicHttpClient().get('https://example.org/a',context)
            process.assert_not_called()
        self.assertEqual(context.calls,0)

    def test_timezone_midnight_and_dst(self):
        self.assertIn('02.07.2027 00:30',local_stamp('2027-07-01T22:30:00+00:00'))
        self.assertIn('CEST',local_stamp('2027-10-31T00:30:00+00:00'))
        self.assertIn('CET',local_stamp('2027-10-31T01:30:00+00:00'))


class ActivityEvidenceTests(unittest.TestCase):
    def test_free_requires_explicit_unconditional_evidence(self):
        html=''.join(f'<div id="a{i}" class="vcard" data-name="Ort {i}" data-group="see" data-type="museum"><span class="voy-listing-price">{price}</span></div>' for i,price in enumerate(['Preis: Eintritt frei','Preis: Kinder kostenlos','Preis: 10 Euro','']))
        activities=WikivoyageParser().parse(html,DestinationCatalog().resolve('Bled'),'2026-10-27T12:00:00+00:00')['activities']
        self.assertIn('Kostenlos',activities[0]['topics'])
        self.assertTrue(all('Kostenlos' not in a['topics'] for a in activities[1:]))
        self.assertIn('aktuell nicht bestätigt',activities[0]['price_status'])

class ProviderFallbackTests(unittest.TestCase):
    def test_offline_source_snapshot_is_real_and_marked_old(self):
        class Offline:
            def get(self,*args):raise OSError('offline')
        with tempfile.TemporaryDirectory() as directory:
            provider=OpenTravelProvider(TripStore(Path(directory)/'store.sqlite3'),Offline())
            result=provider.places(provider.catalog.resolve('Bled'),SearchContext())
            self.assertGreaterEqual(len(result['lodgings']),2)
            self.assertIn('möglicherweise veraltet',result['cache_note'])
            self.assertIn('offline',result['warnings'])
            self.assertTrue(all(l['price']['status']=='unbekannt' for l in result['lodgings']))

    def test_origin_catalog_never_transmits_private_address(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(PublicHttpClient,'json',side_effect=AssertionError('network not allowed')):
                provider=OpenTravelProvider(TripStore(Path(directory)/'store.sqlite3'))
                origin=provider.origin('Berlin','Private Straße 123',SearchContext())
                self.assertIn('Adresse nicht geocodiert',origin['precision'])

    def test_requests_cancel_kills_running_curl(self):
        from unittest.mock import MagicMock
        import subprocess
        context=SearchContext()
        process=MagicMock()
        process.communicate.side_effect=[subprocess.TimeoutExpired('curl',.1),(b'',b'')]
        process.poll.return_value=None
        def check():
            if process.communicate.call_count:
                raise InterruptedError('cancelled')
        context.check=check
        with patch('subprocess.Popen',return_value=process):
            with self.assertRaises(InterruptedError):PublicHttpClient().get('https://cancellation.example.test',context)
        process.kill.assert_called_once()

class ClassificationTests(unittest.TestCase):
    def test_park_is_not_a_verified_hiking_opportunity(self):
        html='<div class="vcard" data-name="Hundepark" data-group="nature" data-type="park"></div>'
        activity=WikivoyageParser().parse(html,DestinationCatalog().resolve('Bled'),'')['activities'][0]
        self.assertIn('Natur',activity['topics'])
        self.assertNotIn('Wandern',activity['topics'])


if __name__=='__main__':
    unittest.main()
