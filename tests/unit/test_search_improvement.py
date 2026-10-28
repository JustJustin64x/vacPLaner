"""Deterministic geographic fixtures and contract regressions. No network access."""
import copy
import json
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from src.vacation_planner.core.planning.SearchRequest import SearchRequest
from src.vacation_planner.core.planning.SearchContext import SearchContext
from src.vacation_planner.core.planning.DiscoveryService import DiscoveryService
from src.vacation_planner.core.planning.PlaceResearch import PlaceResearch,deduplicate
from src.vacation_planner.infrastructure.planning.DestinationCatalog import DestinationCatalog,distance
from src.vacation_planner.infrastructure.planning.OpenTravelProvider import OpenTravelProvider
from src.vacation_planner.infrastructure.planning.TripStore import TripStore,timestamp
from src.vacation_planner.infrastructure.planning.WikivoyageParser import WikivoyageParser
from src.vacation_planner.entrypoints.gui.TripPresenter import TripPresenter
from src.vacation_planner.infrastructure.planning.TripPdfExporter import TripPdfExporter

FIX=Path(__file__).resolve().parents[1]/'fixtures/search_v2'


def request(**kwargs):
    return SearchRequest(earliest='2090-07-01',latest='2090-07-31',**kwargs)


def catalog(*names):
    cat=DestinationCatalog()
    if names:cat.destinations=[copy.deepcopy(cat.resolve(n)) for n in names]
    return cat


class GeographicProvider:
    """Explicit synthetic lodging IDs tied to each real catalog coordinate; not live evidence."""
    def __init__(self,empty=(),fails=(),amenities=None):
        self.empty=set(empty);self.fails=set(fails);self.visited=[];self.routes=[];self.amenities=amenities or {}
    def origin(self,*args):
        return dict(name='Berlin',latitude=52.52,longitude=13.405,precision='Test-Ortszentrum')
    def places(self,d,context):
        self.visited.append(d['name'])
        if d['name'] in self.fails:raise OSError('TEST source unavailable')
        if d['name'] in self.empty:return dict(lodgings=[],activities=[],cache_note='TEST',warnings=[])
        source=d['source'];items=[]
        for i in range(2):
            items.append(dict(id='TEST-'+d['name']+str(i),name='TEST Unterkunft '+d['name']+str(i),type='Hotel',
                latitude=d['latitude']+.001*i,longitude=d['longitude'],address='TEST '+d['name'],
                amenities=self.amenities,price=dict(low=None,status='unbekannt',label='Unterkunft'),
                source=source,url=source,link_kind='Testquelle',retrieved_at=timestamp(),
                data_status='TEST',booking_status='unbekannt'))
        activity=dict(id='TEST-Weg-'+d['name'],name='TEST Weg '+d['name'],type='hiking',topics=['Wandern'],
            latitude=d['latitude'],longitude=d['longitude'],source=source,url=source,link_kind='Testquelle',
            description='TEST nachgewiesener Wanderweg',price_status='unbekannt',duration='unbekannt',retrieved_at=timestamp())
        return dict(lodgings=items,activities=[activity],cache_note='TEST',warnings=[])
    def route(self,origin,d,context):
        self.routes.append(d['name'])
        return dict(legs=[dict(distance=200000,duration=10000)]*2,source='https://example.org/test',
                    retrieved_at=timestamp(),precision='TEST')


class SearchImprovementTests(unittest.TestCase):
    def run_search(self,req=None,cat=None,provider=None,context=None):
        service=DiscoveryService(cat or catalog('Hinterzarten','Braunlage','Waren (Müritz)'),provider or GeographicProvider())
        events=[]
        result=service.search(req or request(surroundings=False),context or SearchContext(),lambda k,v:events.append((k,v)))
        return result,service.diagnostics.data,events

    def test_interests_are_preferences_single_mixed_zero(self):
        for interests in ({'Wandern':5},{'Wandern':5,'Baden':5,'Feiern':5},{}):
            with self.subTest(interests=interests):
                out,diag,_=self.run_search(request(interests=interests,surroundings=False))
                self.assertEqual(len(out),3)
                self.assertEqual(diag['counts']['matches'],3)
                self.assertTrue(all(t['activities'] for t in out))
        from src.vacation_planner.core.planning.RankingService import RankingService
        d=catalog('Hinterzarten').destinations[0];r=request(interests={'Wandern':5})
        self.assertGreater(RankingService.interest_match(d,r,[{'topics':['Wandern']}]),RankingService.interest_match(d,r))
        self.assertEqual(RankingService.interest_match(d,r,[{'topics':['Wandern']}]),RankingService.interest_match(d,r,[{'topics':['Wandern']}]*20))
        with self.assertRaises(ValueError):request(interests={'Wandern':6}).validate()
        for invalid in (dict(budget=''),dict(budget=None),dict(interests=None),dict(earliest=None),dict(adults=None),dict(regions=None)):
            with self.subTest(invalid=invalid),self.assertRaises(ValueError):
                r=request();[setattr(r,k,v) for k,v in invalid.items()];r.validate()
        req=request(budget='2000,50',petrol='1,80',max_hours='8,5');req.validate()
        self.assertEqual(req.petrol,'1.80')
        self.assertEqual(req.max_hours,'8.5')

    def test_regions_aliases_and_unknown_diagnostic(self):
        cat=DestinationCatalog()
        for region in ('Schwarzwald','BLACK FOREST'):
            out=cat.candidates(request(regions=[region]))
            self.assertTrue(out);self.assertTrue(all('Schwarzwald' in d['regions'] for d in out))
        self.assertEqual({d['code'] for d in cat.candidates(request(countries=['Oesterreich']))},{'AT'})
        events=[];svc=DiscoveryService(cat,GeographicProvider())
        with self.assertRaisesRegex(ValueError,'Gebiet nicht erkannt'):
            svc.search(request(regions=['Schwarzwaldd']),SearchContext(),lambda k,v:events.append((k,v)))
        self.assertIn('Schwarzwald',svc.diagnostics.data['summary'])
        self.assertEqual(svc.diagnostics.data['counts']['examined'],0)

    def test_adaptive_finds_after_first_nine_without_raising_http_budget(self):
        cat=DestinationCatalog();cat.destinations=cat.destinations[65:80]
        class Late(GeographicProvider):
            def places(self,d,c):
                if len(self.visited)<9:self.empty.add(d['name'])
                return super().places(d,c)
        provider=Late()
        out,diag,_=self.run_search(request(surroundings=False,show_ideas=False,shortlist=3,request_budget=4),cat,provider)
        self.assertEqual(len(out),3)
        self.assertEqual(diag['counts']['examined'],12)
        self.assertEqual(diag['http_calls'],0) # local fixture/cache reads are not HTTP
        self.assertTrue(all(len(t['lodgings'])==2 for t in out))

    def test_surroundings_one_plus_one_with_distances_and_opt_out(self):
        cat=catalog('Hinterzarten','Titisee-Neustadt')
        base,near=cat.destinations
        class One(GeographicProvider):
            def places(self,d,c):
                r=super().places(d,c);r['lodgings']=r['lodgings'][:1];r['activities']=[];return r
        provider=One()
        data=PlaceResearch(cat,provider).collect(base,request(),SearchContext(),lambda *a:None)
        self.assertEqual(len(data['lodgings']),2)
        self.assertEqual(data['lodgings'][1]['source_place'],near['name'])
        self.assertAlmostEqual(data['lodgings'][1]['distance_km'],distance(base,near),places=1)
        self.assertTrue(data['lodgings'][1]['vicinity'])
        data=PlaceResearch(cat,One()).collect(base,request(surroundings=False),SearchContext(),lambda *a:None)
        self.assertEqual(len(data['lodgings']),1)

    def test_country_region_exclusions_and_radii_apply_to_pois(self):
        cat=catalog('Hřensko','Bad Schandau')
        base=cat.destinations[0]
        class Border(GeographicProvider):
            def places(self,d,c):
                r=super().places(d,c)
                # Foreign coordinate even on the base article must not leak through.
                foreign=super().places(cat.destinations[1],c)['lodgings'][0]
                r['lodgings'].append(foreign)
                return r
        for req in (request(countries=['CZ']),request(excluded=['Deutschland']),request(regions=['Böhmische Schweiz'])):
            p=Border();data=PlaceResearch(cat,p).collect(base,req,SearchContext(),lambda *a:None)
            self.assertTrue(data['lodgings'])
            self.assertTrue(all('Bad Schandau' not in l['name'] for l in data['lodgings']))
        data=PlaceResearch(cat,GeographicProvider()).collect(base,request(lodging_radius_km='1',activity_radius_km='1'),SearchContext(),lambda *a:None)
        self.assertTrue(all(l['distance_km']<=1 for l in data['lodgings']))

    def test_identity_dedup_and_similar_names_remain(self):
        d=catalog('Hinterzarten').destinations[0]
        rows=GeographicProvider().places(d,SearchContext())['lodgings']
        duplicate=copy.deepcopy(rows[0]);duplicate['source']='https://example.org/another-page'
        different=copy.deepcopy(rows[0]);different.update(id='other',latitude=rows[0]['latitude']+.1)
        self.assertEqual(len(deduplicate([*rows,duplicate,different])),3)

    def test_unknown_pool_is_not_a_match_and_no_routing_wasted(self):
        provider=GeographicProvider()
        out,diag,_=self.run_search(request(required=['Pool'],show_ideas=True,surroundings=False),provider=provider)
        self.assertEqual(diag['counts']['matches'],0)
        self.assertTrue(all(t['filter_status']=='offen' for t in out))
        self.assertIn('Pflichtausstattung unbelegt: Pool',diag['summary'])
        self.assertEqual(provider.routes,[])
        hidden,_,_=self.run_search(request(required=['Pool'],show_ideas=False,surroundings=False))
        self.assertEqual(hidden,[])
        violated,diag,_=self.run_search(request(required=['Pool'],show_ideas=True,surroundings=False),provider=GeographicProvider(amenities={'Pool':False}))
        self.assertEqual(violated,[])
        self.assertIn('nachweislich verletzt',diag['summary'])

    def test_train_duration_unknown_never_claims_eight_hours(self):
        out,diag,_=self.run_search(request(modes=['Zug'],max_hours='8',show_ideas=True,surroundings=False))
        self.assertEqual(diag['counts']['matches'],0)
        self.assertIn('Reisezeit unbekannt',diag['summary'])
        self.assertTrue(all(t['transports'][0]['hours_high'] is None for t in out))
        self.assertTrue(all(t['filter_status']=='offen' for t in out))

    def test_provider_error_isolated_and_trace_is_redacted(self):
        class Broken(GeographicProvider):
            def places(self,d,c):
                if d['name']=='Hinterzarten':raise RuntimeError('Problem an Geheime Straße 1')
                return super().places(d,c)
        out,diag,_=self.run_search(request(address='Geheime Straße 1',surroundings=False),provider=Broken())
        self.assertEqual(len(out),2)
        self.assertEqual(diag['counts']['matches'],2)
        self.assertNotIn('Geheime Straße 1',json.dumps(diag))
        self.assertIn('Traceback',diag['errors'][0]['traceback'])
        self.assertEqual(sum(diag['primary_reasons'].values()),diag['counts']['examined'])

    def test_control_aborts_propagate_through_provider_and_routing(self):
        class Stop(GeographicProvider):
            def route(self,*args):raise InterruptedError('Abfragebudget erreicht')
        service=DiscoveryService(catalog('Hinterzarten'),Stop())
        with self.assertRaises(InterruptedError):service.search(request(surroundings=False),SearchContext(),lambda *a:None)
        self.assertIn('Abfragebudget',service.diagnostics.data['stop_reason'])
        cancelled=SearchContext(cancel=threading.Event());cancelled.cancel.set()
        for context in (SearchContext(seconds=-1),cancelled):
            with self.assertRaises(InterruptedError):self.run_search(context=context)
        class StopHttp:
            def get(self,*a):raise InterruptedError('Zeitlimit erreicht')
        with tempfile.TemporaryDirectory() as folder:
            provider=OpenTravelProvider(TripStore(Path(folder)/'db.sqlite3'),StopHttp())
            with self.assertRaises(InterruptedError):provider.places(catalog('Bled').destinations[0],SearchContext())

    def test_http_quota_preserves_emitted_results_and_stops(self):
        class Metered(GeographicProvider):
            def places(self,d,c):c.consume();return super().places(d,c)
            def route(self,o,d,c):c.consume();return super().route(o,d,c)
        service=DiscoveryService(catalog('Hinterzarten','Braunlage','Waren (Müritz)'),Metered())
        events=[];context=SearchContext(budget=4)
        with self.assertRaises(InterruptedError):
            service.search(request(surroundings=False),context,lambda k,v:events.append((k,v)))
        self.assertEqual(len([v for k,v in events if k=='result']),2)
        self.assertEqual(context.calls,4)
        self.assertIn('Abfragebudget',service.diagnostics.data['summary'])

    def test_malformed_card_does_not_destroy_valid_entries(self):
        html='<div class="vcard" data-name="Kaputt" data-group="sleep" data-type="hotel" data-url="https://[broken"><span data-lat="NaN" data-lon="0"></span></div>'
        html+='<div class="vcard" data-name="Gültig" data-group="sleep" data-type="hotel" data-url="https://example.org"></div>'
        data=WikivoyageParser().parse(html,catalog('Hinterzarten').destinations[0],timestamp())
        self.assertEqual(len(data['lodgings']),2)
        self.assertIsNone(data['lodgings'][0]['latitude'])
        self.assertEqual(data['lodgings'][1]['name'],'Gültig')

    def test_actual_multitype_cards_and_conservative_inferences(self):
        cat=catalog('Bad Schandau','Trogir','Hřensko');parser=WikivoyageParser()
        names=['Bad_Schandau.html','Trogir.html','H%C5%99ensko.html']
        for d,name in zip(cat.destinations,names):
            data=parser.parse((FIX/name).read_text(),d,'2026-10-28T10:00:00+00:00')
            self.assertGreaterEqual(len(data['lodgings']),1)
            self.assertTrue(all(x['source'].startswith(d['source']) for x in data['lodgings']))
        data=parser.parse((FIX/'Bad_Schandau.html').read_text(),cat.destinations[0],timestamp())
        self.assertTrue(any(l['type']=='Hotel' and 'garni' in l['name'].lower() for l in data['lodgings']))
        self.assertTrue(any('Wandern' in a['topics'] for a in data['activities']))
        html='<div class="vcard" data-name="Testsee" data-group="nature" data-type="lake"></div><div class="vcard" data-name="Testgipfel" data-group="nature" data-type="mountain"></div>'
        acts=parser.parse(html,cat.destinations[0],timestamp())['activities']
        self.assertNotIn('Baden',acts[0]['topics']);self.assertNotIn('Wandern',acts[1]['topics'])

    def test_cache_version_and_historical_snapshot_not_relabelled_fresh(self):
        class CountingHttp:
            def __init__(self):self.calls=0
            def get(self,url,c):
                self.calls+=1;c.consume()
                return (FIX/'H%C5%99ensko.html').read_text(),timestamp()
        with tempfile.TemporaryDirectory() as folder:
            store=TripStore(Path(folder)/'db.sqlite3');http=CountingHttp();provider=OpenTravelProvider(store,http)
            d=catalog('Hřensko').destinations[0]
            store.cache_set('places-v3:'+d['source'],dict(lodgings=[],activities=[]),timestamp())
            c=SearchContext();first=provider.places(d,c);second=provider.places(d,c)
            self.assertEqual(http.calls,1);self.assertEqual(c.calls,1)
            self.assertEqual(first['lodgings'][0]['retrieved_at'],second['lodgings'][0]['retrieved_at'])
            self.assertIn('Cache',second['cache_note'])

    def test_diversity_and_nature_do_not_default_to_capitals(self):
        cat=DestinationCatalog();provider=GeographicProvider()
        out,_,_=self.run_search(request(interests={'Wandern':5,'Baden':5,'Feiern':5},surroundings=False),cat,provider)
        self.assertGreaterEqual(sum(t['destination']['type']!='Großstadt' for t in out),3)
        self.assertGreaterEqual(len({t['destination']['area_id'] for t in out}),4)
        self.assertGreaterEqual(len({t['destination']['type'] for t in out}),2)

    def test_origin_alias_exclusion_and_stable_dates(self):
        cat=DestinationCatalog();cat.resolve('Berlin')['aliases']=['Berlin DE']
        self.assertNotIn('Berlin',[d['name'] for d in cat.candidates(request(origin='Berlin DE'))])
        out,_,_=self.run_search(request(surroundings=False))
        self.assertEqual(len({t['start'] for t in out}),1)
        self.assertTrue(all(len(t['date_options'])==3 for t in out))

    def test_new_fields_and_old_saved_trip_pdf_compatible(self):
        out,_,_=self.run_search(request(required=['Pool'],show_ideas=True,surroundings=False))
        with tempfile.TemporaryDirectory() as folder:
            store=TripStore(Path(folder)/'trips.sqlite3');identifier=store.save('Neue Idee',out[0])
            loaded=store.load(identifier)
            self.assertEqual(loaded['filter_status'],'offen')
            self.assertEqual(loaded['destination']['regions'],out[0]['destination']['regions'])
            for key in ('filter_status','open_criteria','interest_evidence','evidence_confidence','date_options'):loaded.pop(key,None)
            for key in ('surroundings','show_ideas','target_type','lodging_radius_km','activity_radius_km'):loaded['request'].pop(key,None)
            TripPdfExporter().export(Path(folder)/'old.pdf',TripPresenter.sections(loaded))
            self.assertGreater((Path(folder)/'old.pdf').stat().st_size,5000)

    def test_catalog_unique_sources_and_traceable_nonurban_coverage(self):
        cat=DestinationCatalog();rows=cat.destinations
        self.assertGreaterEqual(len(rows),250)
        self.assertGreaterEqual(len({d['code'] for d in rows}),20)
        self.assertGreaterEqual(sum(d['type']!='Großstadt' for d in rows)/len(rows),.6)
        self.assertEqual(len({d['id'] for d in rows}),len(rows))
        for d in rows:
            self.assertTrue(d['source_checked_at']);self.assertTrue(d['source'].startswith('https://de.wikivoyage.org/wiki/'))
            self.assertTrue(d['regions']);self.assertTrue(d['base_name'])

if __name__=='__main__':unittest.main()
