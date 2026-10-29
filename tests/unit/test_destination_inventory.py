import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from src.vacation_planner.core.planning.SearchContext import SearchContext
from src.vacation_planner.core.planning.DestinationFeatures import feature_profile, feature_topics
from src.vacation_planner.core.planning.CandidateSelection import select_candidates
from src.vacation_planner.core.planning.RankingService import RankingService
from src.vacation_planner.infrastructure.planning.DestinationInventory import DestinationInventory
from src.vacation_planner.infrastructure.planning.DestinationImportService import DestinationImportService
from src.vacation_planner.infrastructure.planning.DestinationCatalog import DestinationCatalog
from src.vacation_planner.infrastructure.planning.OpenTravelProvider import OpenTravelProvider
from src.vacation_planner.infrastructure.planning.TripStore import TripStore
from tests.unit.test_surprise_planning import request, fixture_trip


def archive(rows):
    stream=io.BytesIO()
    with zipfile.ZipFile(stream,'w') as z:z.writestr('AT.txt','\n'.join(rows)+'\n')
    stream.seek(0);return stream


def row(gid,name='Testdorf',lat=47,lon=11,feature_class='P',feature_code='PPL',population=0):
    return '\t'.join(map(str,[gid,name,name,'Alias '+name,lat,lon,feature_class,feature_code,'AT','','07','1','','',population,'','700','Europe/Vienna','2026-10-29']))


def place(gid=1,**kwargs):return next(DestinationImportService.parse_country(archive([row(gid,**kwargs)]),'AT',{'AT.07':'Tyrol'}))


def feature(gid,tags,lat=47,lon=11):
    return {'type':'node','id':gid,'lat':lat,'lon':lon,'tags':{'name':'TEST '+str(gid),**tags}}


class InventoryTests(unittest.TestCase):
    def setUp(self):
        self.folder=tempfile.TemporaryDirectory();self.root=Path(self.folder.name)
        self.inventory=DestinationInventory(self.root/'destinations.sqlite3')
    def tearDown(self):self.folder.cleanup()
    def imported(self,rows=None):
        self.inventory.replace_country('AT',rows or [place()],{'name':'Österreich'},SearchContext())

    def test_country_parser_includes_zero_population_villages_and_separates_regions(self):
        stream=archive([row(1),row(2,'See',feature_class='H',feature_code='LK'),row(3,'Ruine',feature_code='PPLQ'),row(4,'Station',feature_class='S',feature_code='RSTN')])
        parsed=list(DestinationImportService.parse_country(stream,'AT'))
        self.assertEqual([p['kind'] for p in parsed],['settlement','region'])
        self.assertEqual(parsed[0]['population'],0);self.assertIn('Alias Testdorf',parsed[0]['aliases'])
        self.imported(parsed);self.assertEqual(len(self.inventory.candidates()),1)

    def test_repeat_import_updates_without_duplicates_or_trip_changes(self):
        store=TripStore(self.root/'trips.sqlite3');trip=fixture_trip();key=store.save('Bestehend',trip)
        before=store.load(key)
        self.imported();self.imported([place(name='Aktualisiert')])
        self.assertEqual([p['name'] for p in self.inventory.candidates()],['Aktualisiert'])
        with self.inventory.connect() as db:self.assertEqual(db.execute('SELECT count(*) FROM place_geo').fetchone()[0],1)
        self.assertEqual(store.load(key),before)

    def test_cancel_and_malformed_update_roll_back_complete_country(self):
        self.imported();before=self.inventory.coverage()
        def cancelled():
            yield place(2)
            raise InterruptedError('TEST Abbruch')
        with self.assertRaises(InterruptedError):self.imported(cancelled())
        self.assertEqual(self.inventory.coverage(),before)
        self.assertEqual(self.inventory.candidates()[0]['id'],'geonames:1')
        with self.assertRaises(ValueError):
            self.imported(DestinationImportService.parse_country(archive([row(3),'broken']),'AT'))
        self.assertEqual(self.inventory.candidates()[0]['id'],'geonames:1')

    def test_spatial_lookup_and_non_imported_country_message(self):
        self.imported([place(1),place(2,name='Fern',lat=49)])
        self.assertEqual(len(self.inventory.nearby(47,11,5)),1)
        cat=DestinationCatalog(self.inventory)
        # A country with some editorial records still has explicitly limited coverage.
        with self.assertRaisesRegex(ValueError,'noch nicht importiert'):cat.candidates(request(countries=['Albanien']))

    def test_feature_refresh_invalidates_cache_within_same_second(self):
        self.imported();bounds=[46.9,10.9,47.1,11.1]
        self.inventory.replace_features('TEST',bounds,[feature(1,{'amenity':'bar'})],SearchContext(),'https://example.org/test')
        first=self.inventory.candidates();self.assertEqual(first[0]['feature_profile']['counts']['Barhopping'],1)
        self.inventory.replace_features('TEST',bounds,[feature(2,{'tourism':'museum'})],SearchContext(),'https://example.org/test')
        second=self.inventory.candidates();self.assertNotIn('Barhopping',second[0]['feature_profile']['counts'])
        self.assertEqual(second[0]['feature_profile']['counts']['Kultur'],1)

    def test_overlap_and_repeat_region_import_do_not_duplicate_or_erase_other_region(self):
        b=[46.9,10.9,47.1,11.1];f=feature(1,{'amenity':'bar'})
        for name in ('A','B','B'):self.inventory.replace_features(name,b,[f],SearchContext(),'https://example.org/test')
        self.assertEqual(len(self.inventory.nearby(47,11,5,'features')),1)
        self.inventory.replace_features('A',b,[],SearchContext(),'https://example.org/test')
        self.assertEqual(len(self.inventory.nearby(47,11,5,'features')),1)

    def test_name_alone_never_merges_geographic_identities(self):
        self.imported([place(1,name='Gleich'),place(2,name='Gleich',lat=49)])
        self.assertEqual(len(self.inventory.candidates()),2)

    def test_osm_and_geonames_identity_merge_needs_position_or_explicit_id(self):
        self.imported([place(1,name='Gleich'),place(2,name='Gleich',lat=49)])
        f=feature(9,{'name':'Gleich','place':'village'},lat=47.0001)
        self.inventory.replace_features('TEST',[46.9,10.9,47.1,11.1],[f],SearchContext(),'https://example.org/test')
        candidates=self.inventory.candidates()
        self.assertEqual(len(candidates),2);self.assertEqual(candidates[0]['source_identities'],['osm:node:9'])
        self.assertNotIn('source_identities',candidates[1])

    def test_normal_provider_uses_imported_features_without_geonames_scraping(self):
        self.imported();f=feature(9,{'tourism':'hotel','name':'TEST Hotel'})
        self.inventory.replace_features('TEST',[46.9,10.9,47.1,11.1],[f],SearchContext(),'https://example.org/test')
        class NoHttp:
            def get(self,*a):raise AssertionError('Keine GeoNames-HTML-Abfrage')
        provider=OpenTravelProvider(TripStore(self.root/'trips.sqlite3'),NoHttp())
        data=provider.places(provider.catalog.resolve('Testdorf'),SearchContext())
        self.assertEqual(data['lodgings'][0]['name'],'TEST Hotel');self.assertIsNone(data['lodgings'][0]['price']['low'])

    def test_habitat_protection_zone_is_context_not_a_visitor_activity(self):
        self.imported()
        self.inventory.replace_features('TEST',[46.9,10.9,47.1,11.1],[feature(9,{'boundary':'protected_area','name':'TEST Wildruhezone'})],SearchContext(),'https://example.org/test')
        provider=OpenTravelProvider(TripStore(self.root/'trips.sqlite3'))
        destination=provider.catalog.resolve('Testdorf')
        self.assertIn('Natur',destination['feature_profile']['counts'])
        self.assertEqual(provider.places(destination,SearchContext())['activities'],[])

    def test_unknown_poi_country_never_satisfies_hard_country_requirement(self):
        from src.vacation_planner.core.planning.DiscoveryService import DiscoveryService
        self.imported()
        self.inventory.replace_features('TEST',[46.9,10.9,47.1,11.1],[feature(9,{'tourism':'hotel','name':'TEST A'}),feature(10,{'tourism':'hotel','name':'TEST B'},47.002)],SearchContext(),'https://example.org/test')
        provider=OpenTravelProvider(TripStore(self.root/'trips.sqlite3'))
        provider.origin=lambda *a:{'name':'Berlin','latitude':52.5,'longitude':13.4,'precision':'TEST'}
        provider.catalog.destinations=[provider.catalog.resolve('Testdorf')]
        req=request(countries=['AT'],modes=['Zug'],show_ideas=True,regional_queries=0,price_targets=0,surroundings=False)
        trips=DiscoveryService(provider.catalog,provider).search(req,SearchContext(),lambda *a:None)
        self.assertEqual(trips[0]['filter_status'],'offen')
        self.assertIn('Länderzuordnung',str(trips[0]['open_criteria']))

    def test_wikidata_failure_is_optional_and_never_loses_geo_data(self):
        self.imported()
        class Offline:
            def json(self,*a):raise OSError('TEST offline')
        with self.assertRaises(OSError):DestinationImportService(self.inventory,Offline()).enrich_wikidata(['Q1'],SearchContext())
        self.assertEqual(len(self.inventory.candidates()),1)

    def test_failed_regional_source_has_backoff_and_preserves_local_candidates(self):
        self.imported()
        class Offline:
            calls=0
            def json(self,*a):self.calls+=1;raise OSError('TEST Quelle ausgefallen')
        http=Offline();provider=OpenTravelProvider(TripStore(self.root/'trips.sqlite3'),http)
        candidates=provider.catalog.candidates(request(countries=['AT']))
        origin={'latitude':46,'longitude':11};req=request(countries=['AT'],interests={'Wandern':5})
        for _ in range(2):
            result=provider.enrich_candidates(candidates,req,origin,SearchContext(),lambda *a:None)
            self.assertEqual(result,candidates)
        self.assertEqual(http.calls,1)

    def test_pbf_filter_keeps_route_geometry_and_admission_is_not_inferred(self):
        from src.vacation_planner.infrastructure.planning.OsmRegionalExtract import extract_features
        path=self.root/'TEST.osm'
        path.write_text('''<osm version="0.6" generator="TEST">
        <node id="1" lat="47.00" lon="11.00"><tag k="name" v="TEST Strand"/><tag k="natural" v="beach"/></node>
        <node id="2" lat="47.01" lon="11.01"/>
        <way id="3"><nd ref="1"/><nd ref="2"/><tag k="highway" v="path"/></way>
        <relation id="4"><member type="way" ref="3" role=""/><tag k="name" v="TEST Wanderroute"/><tag k="type" v="route"/><tag k="route" v="hiking"/></relation></osm>''')
        rows=extract_features(path,[46.9,10.9,47.1,11.1],SearchContext())
        self.assertEqual({x['id'] for x in rows},{1,4})
        self.assertEqual(rows[-1]['type'],'relation')
        self.assertNotIn('price',rows[0]['tags'])
        context=SearchContext();context.cancel.set()
        with self.assertRaises(InterruptedError):extract_features(path,[46.9,10.9,47.1,11.1],context)

    def test_wikidata_exact_geonames_reference_attaches_identity_and_relations(self):
        self.imported()
        self.inventory.save_entities({'Q123':{'claims':{'P1566':[{'mainsnak':{'datavalue':{'value':'1'}}}],'P31':[{'mainsnak':{'datavalue':{'value':{'id':'Q532'}}}}]},'sitelinks':{'dewikivoyage':{'title':'TEST Dorf'}}}})
        self.inventory.replace_features('TEST',[46.9,10.9,47.1,11.1],[feature(8,{'place':'village','name':'Andere Sprache','wikidata':'Q123'})],SearchContext(),'https://example.org/test')
        candidate=self.inventory.candidates()[0]
        self.assertEqual(candidate['wikidata_id'],'Q123');self.assertIn('P31',candidate['wikidata_relationships'])
        self.assertEqual(candidate['wikivoyage_source'],'https://de.wikivoyage.org/wiki/TEST_Dorf')


class EvidenceSelectionTests(unittest.TestCase):
    def destination(self,identity,lat,features):
        p=place(identity,name='TEST '+str(identity),lat=lat)
        p['feature_profile']=feature_profile(features,p,[{'name':'TEST Gebiet'}]);return p
    def f(self,i,tags,lat=47,lon=11):
        f=feature(i,tags,lat,lon)
        return dict(id='osm:node:'+str(i),name='TEST '+str(i),latitude=lat,longitude=lon,tags=f['tags'],source='https://www.openstreetmap.org/node/'+str(i),retrieved_at='2026-10-29T10:00:00+00:00')

    def test_interest_synonyms_are_normalized_without_ai_or_double_weights(self):
        r=request(interests={'Nightlife':5,'Feiern':3,'Bar Hopping':4});r.validate()
        self.assertEqual(r.interests,{'Feiern':5,'Barhopping':4})

    def test_city_interest_uses_known_place_type_without_general_population_bonus(self):
        city=place(population=150000);village=place(2,population=0)
        city['feature_profile']=feature_profile([],city,[]);village['feature_profile']=feature_profile([],village,[])
        self.assertGreater(RankingService.interest_match(city,request(interests={'Städte':5})),RankingService.interest_match(village,request(interests={'Städte':5})))
        self.assertEqual(RankingService.interest_match(city,request(interests={'Wandern':5})),RankingService.interest_match(village,request(interests={'Wandern':5})))

    def test_water_path_and_single_bar_do_not_prove_bathing_hiking_nightlife(self):
        for tags in ({'natural':'water'},{'highway':'path'},{'amenity':'bar'}):
            topics=feature_topics(tags)
            self.assertNotIn('Baden',topics);self.assertNotIn('Wandern',topics);self.assertNotIn('Feiern',topics)
        profile=feature_profile([self.f(1,{'amenity':'bar'})],place(),[{'name':'TEST'}])
        self.assertEqual(profile['strengths']['Barhopping'],.15)
        self.assertFalse(feature_topics({'amenity':'nightclub','access':'private'}))

    def test_distinct_interests_favor_matching_small_place_over_unmatched_city(self):
        nature=[self.f(i,{'route':'hiking','type':'route'}) for i in range(4)]+[self.f(10,{'leisure':'nature_reserve'})]
        culture=[self.f(i,{'tourism':'museum'},47.5) for i in range(5)]+[self.f(i+10,{'amenity':'nightclub'},47.5) for i in range(3)]
        village=self.destination(1,47,nature);city=self.destination(2,47.5,culture);city['type']='Großstadt'
        hiking=request(interests={'Wandern':5,'Ruhe':3});night=request(interests={'Kultur':5,'Feiern':5})
        self.assertGreater(RankingService.interest_match(village,hiking),RankingService.interest_match(city,hiking))
        self.assertGreater(RankingService.interest_match(city,night),RankingService.interest_match(village,night))

    def test_barhopping_needs_multiple_nearby_bars_and_coverage_is_explicit(self):
        base=place();bars=[self.f(i,{'amenity':'pub'}) for i in range(4)]+[self.f(10,{'amenity':'pub'},47.2)]
        p=feature_profile(bars,base,[{'name':'TEST'}]);self.assertEqual(p['counts']['Barhopping'],4)
        self.assertEqual(p['strengths']['Barhopping'],1)
        self.assertEqual(feature_profile([],base,[])['coverage'],'unknown')
        self.assertEqual(feature_profile([],base,[{'name':'TEST'}])['coverage'],'regional')

    def test_changing_interests_rescores_same_cached_features_and_stays_deterministic(self):
        village=self.destination(1,47,[self.f(i,{'route':'hiking','type':'route'}) for i in range(4)])
        bars=self.destination(2,47.5,[self.f(i,{'amenity':'pub'},47.5) for i in range(4)])
        origin={'latitude':46,'longitude':11};pool=[village,bars];before=copy.deepcopy(pool)
        def select(interests):return select_candidates(pool,request(interests=interests,weights={'Interessen':100}),origin,SearchContext())[0]
        self.assertEqual(select({'Wandern':5})[0]['id'],village['id']);self.assertEqual(select({'Barhopping':5})[0]['id'],bars['id'])
        self.assertEqual(select({'Wandern':5}),select({'Wandern':5}));self.assertEqual(pool,before)

    def test_candidate_limit_applies_after_all_geographic_rows_are_scored(self):
        pool=[self.destination(i,47+i*.01,[]) for i in range(100)]
        pool[-1]['feature_profile']['strengths']={'Wandern':1}
        selected,counts=select_candidates(pool,request(candidate_pool=20,interests={'Wandern':5},weights={'Interessen':100}),{'latitude':46,'longitude':11},SearchContext())
        self.assertEqual(counts['geographic_considered'],100);self.assertEqual(len(selected),20);self.assertEqual(selected[0]['id'],pool[-1]['id'])

    def test_dense_city_does_not_exclude_other_fitting_regions_before_diversity(self):
        pool=[self.destination(i,47+i*.0001,[]) for i in range(250)]
        for d in pool:d['feature_profile']['strengths']={'Wandern':1}
        remote=self.destination(900,48,[]);remote['feature_profile']['strengths']={'Wandern':1};pool.append(remote)
        selected,_=select_candidates(pool,request(candidate_pool=20,interests={'Wandern':5},weights={'Interessen':100}),{'latitude':46,'longitude':11},SearchContext())
        self.assertIn(remote['id'],[d['id'] for d in selected[:3]])

    def test_diversity_does_not_promote_weak_fit_ahead_of_matching_candidates(self):
        matching=[self.destination(i,47+i*.01,[]) for i in range(3)]
        for d in matching:d['feature_profile']['strengths']={'Wandern':1}
        weak=self.destination(900,48,[])
        selected,_=select_candidates(matching+[weak],request(interests={'Wandern':5}),{'latitude':46,'longitude':11},SearchContext())
        self.assertNotIn(weak['id'],[d['id'] for d in selected[:3]])

    def test_rtree_regions_link_to_stay_not_region_as_destination(self):
        with tempfile.TemporaryDirectory() as folder:
            inventory=DestinationInventory(Path(folder)/'db.sqlite3')
            region=place(2,name='TEST See',feature_class='H',feature_code='LK')
            inventory.replace_country('AT',[place(),region],{},SearchContext())
            inventory.replace_features('TEST',[46.9,10.9,47.1,11.1],[],SearchContext(),'https://example.org/test')
            rows=inventory.candidates();self.assertEqual(len(rows),1)
            self.assertEqual(rows[0]['tourist_regions'][0]['id'],'geonames:2')


if __name__=='__main__':unittest.main()
