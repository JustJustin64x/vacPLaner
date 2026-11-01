"""Regression tests for geography, evidence and resumable spatial imports."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from src.vacation_planner.infrastructure.planning.EuropeScope import contains,EXCLUDED
from src.vacation_planner.infrastructure.planning.DestinationImportService import DestinationImportService,COUNTRIES,parse_poly
from src.vacation_planner.infrastructure.planning.DestinationInventory import DestinationInventory
from src.vacation_planner.infrastructure.planning.OsmRegionalExtract import extract_features
from src.vacation_planner.core.planning.DestinationFeatures import feature_profile,feature_topics,spatial_distance,evidence_score
from src.vacation_planner.core.planning.CandidateSelection import same_holiday_region
from src.vacation_planner.core.planning.SearchContext import SearchContext
from tests.unit.test_destination_inventory import place,feature
from tests.unit import test_destination_inventory as fixtures
from tests.unit.test_surprise_planning import request


class EuropeSearchTests(unittest.TestCase):
    def test_explicit_non_eu_and_difficult_countries(self):
        for c in ('NO','CH','GB','BA','BY','UA','RU','TR','KZ','XK','GG','SJ'):self.assertIn(c,COUNTRIES)
        self.assertEqual(set(EXCLUDED),{'AM','AZ','GE','GL'})

    def test_transcontinental_scope(self):
        for c,lat,lon in [('RU',55.75,37.62),('KZ',51.0,51.0),('TR',41.02,28.95)]:self.assertTrue(contains(c,lat,lon),(c,lat,lon))
        for c,lat,lon in [('RU',43.1,131.9),('RU',45.0,39.0),('KZ',43.2,76.9),('TR',39.9,32.9),('TR',41.02,29.2)]:self.assertFalse(contains(c,lat,lon),(c,lat,lon))

    def test_overseas_and_documented_island_exceptions(self):
        for c,lat,lon in [('FR',4,-53),('ES',28.3,-16.5),('ES',35.3,-2.9),('NL',12,-68),('DK',64,-45)]:self.assertFalse(contains(c,lat,lon))
        for c,lat,lon in [('FR',42.1,9.2),('PT',32.7,-16.9),('PT',37.8,-25.5),('CY',35,33),('SJ',78.2,15.6)]:self.assertTrue(contains(c,lat,lon))

    def test_green_space_and_water_are_not_quietness_or_bathing(self):
        self.assertNotIn('Ruhe',feature_topics({'leisure':'park'}))
        self.assertNotIn('Baden',feature_topics({'natural':'water'}))
        self.assertNotIn('Baden',feature_topics({'natural':'beach','swimming':'no'}))

    def test_missing_empty_partial_and_failed_are_distinct(self):
        with tempfile.TemporaryDirectory() as folder:
            inventory=DestinationInventory(Path(folder)/'data.db');p=place()
            unknown=feature_profile([],p,[])
            empty=feature_profile([],p,[dict(name='TEST',categories=['Baden'],radius_complete=True)])
            partial=feature_profile([],p,[dict(name='TEST',categories=['Baden'],radius_complete=False)])
            self.assertEqual(unknown['category_status']['Baden'],'not_investigated')
            self.assertEqual(empty['category_status']['Baden'],'observed_no_matches')
            self.assertEqual(partial['category_status']['Baden'],'partial')
            inventory.record_attempt('TEST',[46,10,48,12],'https://example.org','failed','TEST offline',['Baden'])
            inventory._attempt_cache=inventory.attempts()
            with inventory.connect() as db:r=inventory.profile_place(p,[],db)
            self.assertEqual(r['feature_profile']['category_status']['Baden'],'source_unreachable')
            self.assertFalse(r['feature_profile']['strengths'])

    def test_relation_untagged_nested_members_and_missing_members(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'test.osm'
            path.write_text('''<osm version="0.6"><node id="1" lat="47" lon="11"/><node id="2" lat="47.01" lon="11.01"/>
            <way id="3"><nd ref="1"/><nd ref="2"/></way>
            <relation id="4"><member type="way" ref="3" role="outer"/></relation>
            <relation id="5"><member type="relation" ref="4" role=""/><tag k="type" v="route"/><tag k="route" v="hiking"/></relation>
            <relation id="6"><member type="way" ref="3" role=""/><member type="way" ref="99" role=""/><tag k="type" v="route"/><tag k="route" v="hiking"/></relation></osm>''')
            rows=extract_features(path,[46,10,48,12],SearchContext())
            byid={r['id']:r for r in rows}
            self.assertTrue(byid[5]['geometry']['complete'])
            self.assertFalse(byid[6]['geometry']['complete'])
            self.assertEqual(byid[5]['geometry']['points'][0],(47,11))

    def test_sampled_geometry_distance_is_not_center_or_access_claim(self):
        f=dict(latitude=50,longitude=11,geometry=dict(points=[[47,11],[50,11]],complete=False))
        self.assertEqual(spatial_distance(place(),f),0)
        f.update(id='osm:relation:1',name='TEST',tags={'type':'route','route':'hiking'},source='https://example.org',retrieved_at='2026-10-30')
        profile=feature_profile([f],place(),[dict(name='TEST')]);proof=profile['evidence']['Wandern'][0]
        self.assertIn('ungeprüft',proof['access_status']);self.assertFalse(proof['geometry_complete'])
        self.assertLessEqual(profile['strengths']['Wandern'],.4)

    def test_polygon_holes_and_bbox_are_not_country_proof(self):
        rings=parse_poly('TEST\n1\n10 46\n12 46\n12 48\n10 48\n10 46\nEND\n!2\n10.9 46.9\n11.1 46.9\n11.1 47.1\n10.9 47.1\nEND\nEND')
        c=dict(bounds=[45,9,49,13],source_polygons=rings)
        self.assertFalse(DestinationInventory.covered(c,47,11));self.assertFalse(DestinationInventory.covered(c,48.5,12.5))
        self.assertTrue(DestinationInventory.covered(c,46.5,10.5))

    def test_combination_cannot_be_filled_by_single_abundant_category(self):
        r=request(interests={'Baden':5,'Wandern':5})
        a=dict(feature_profile=dict(strengths={'Baden':1}))
        b=dict(feature_profile=dict(strengths={'Baden':.6,'Wandern':.6}))
        self.assertLess(evidence_score(a,r),evidence_score(b,r))

    def test_bar_cluster_excludes_widely_scattered_bars(self):
        factory=fixtures.EvidenceSelectionTests();bars=[factory.f(i,{'amenity':'bar'},lat=47+offset,lon=11) for i,offset in enumerate([-.016,-.005,.006,.017])]
        profile=feature_profile(bars,place(),[dict(name='TEST')])
        self.assertLess(profile['strengths']['Barhopping'],.65)
        compact=feature_profile([factory.f(i,{'amenity':'bar'}) for i in range(50)],place(),[dict(name='TEST')])
        self.assertEqual(compact['strengths']['Barhopping'],.65)

    def test_shared_region_across_border_groups_but_different_remote_regions_do_not(self):
        a=place();b=place(2,lat=47.15);a['code']='AT';b['code']='DE'
        proof=[dict(id='osm:relation:'+str(i)) for i in range(3)]
        for p in (a,b):p['feature_profile']=dict(evidence={'Wandern':proof})
        self.assertTrue(same_holiday_region(a,b))
        b['latitude']=49;self.assertFalse(same_holiday_region(a,b))

    def test_identity_survives_source_country_correction(self):
        with tempfile.TemporaryDirectory() as folder:
            i=DestinationInventory(Path(folder)/'data.db');p=place()
            i.replace_country('AT',[p],{},SearchContext());p=copy.deepcopy(p);p['code']='DE'
            i.replace_country('DE',[p],{},SearchContext())
            with i.connect() as db:
                self.assertEqual(db.execute('SELECT id,country FROM places').fetchall(),[('geonames:1','DE')])
                self.assertEqual(db.execute('SELECT count(*) FROM place_geo').fetchone()[0],1)

    def test_cancelled_feature_refresh_preserves_completed_region(self):
        with tempfile.TemporaryDirectory() as folder:
            i=DestinationInventory(Path(folder)/'data.db');b=[46,10,48,12]
            i.replace_features('TEST',b,[feature(1,{'amenity':'bar'})],SearchContext(),'TEST')
            before=i.coverage();ctx=SearchContext();ctx.cancel.set()
            with self.assertRaises(InterruptedError):i.replace_features('TEST',b,[feature(2,{'amenity':'pub'})],ctx,'TEST')
            self.assertEqual(i.coverage(),before);self.assertEqual(i.nearby(47,11,2,'features')[0]['id'],'osm:node:1')

    def test_failed_live_source_records_failure_and_preserves_features(self):
        class Offline:
            def json(self,*args):raise OSError('TEST offline')
        with tempfile.TemporaryDirectory() as folder:
            i=DestinationInventory(Path(folder)/'data.db')
            with self.assertRaises(OSError):DestinationImportService(i,Offline()).update_region('TEST',(46.9,10.9,47.1,11.1),SearchContext())
            self.assertEqual(i.attempts()[0]['status'],'failed');self.assertEqual(i.coverage(),[])


class AccessResearchTests(unittest.TestCase):
    def test_bundled_foot_check_keeps_point_and_entrance_distinct_and_reuses_cache(self):
        from src.vacation_planner.infrastructure.planning.OpenTravelProvider import OpenTravelProvider
        from src.vacation_planner.infrastructure.planning.TripStore import TripStore
        class Http:
            calls=0
            def json(self,url,context):
                self.calls+=1;context.consume()
                return dict(code='Ok',routes=[dict(legs=[dict(distance=600,duration=480) for _ in range(4)])],waypoints=[dict(distance=20) for _ in range(5)]),'2026-10-30T10:00:00+00:00'
        with tempfile.TemporaryDirectory() as folder:
            http=Http();p=OpenTravelProvider(TripStore(Path(folder)/'trips.db'),http)
            trip=dict(destination=place(),activities=[dict(id='osm:node:'+str(i),name='TEST',latitude=47,longitude=11,distance_km=.4) for i in (1,2)],notes=[])
            p.verify_activity_access(trip,SearchContext());p.verify_activity_access(trip,SearchContext())
            self.assertEqual(http.calls,1)
            proof=trip['activities'][0]['access_research'];self.assertEqual(proof['kilometers'],.6)
            self.assertIn('ungeprüft',proof['note']);self.assertEqual(proof['endpoint_offset_meters'],20)

    def test_relation_representative_is_not_routed_as_a_trailhead(self):
        from src.vacation_planner.infrastructure.planning.OpenTravelProvider import OpenTravelProvider
        from src.vacation_planner.infrastructure.planning.TripStore import TripStore
        class Http:
            def json(self,*args):raise AssertionError('Kein Zugang bekannt')
        with tempfile.TemporaryDirectory() as folder:
            p=OpenTravelProvider(TripStore(Path(folder)/'trips.db'),Http())
            trip=dict(destination=place(),activities=[dict(id='osm:relation:1',distance_km=.1)],notes=[])
            p.verify_activity_access(trip,SearchContext());self.assertNotIn('access_research',trip['activities'][0])
            self.assertIn('offen',trip['notes'][0])


class CombinationReachabilityTests(unittest.TestCase):
    def test_culture_and_nightlife_need_joint_area_beyond_individual_radius(self):
        profile=dict(strengths={'Kultur':1,'Feiern':1},counts={'Kultur':5,'Feiern':3},evidence={
            'Kultur':[dict(id='museum',latitude=47.02,longitude=11,distance_km=2.2,cultural_anchor=True)],
            'Feiern':[dict(id='club',latitude=46.98,longitude=11,distance_km=2.2)]})
        destination=dict(feature_profile=profile);req=request(interests={'Kultur':5,'Feiern':5})
        self.assertEqual(evidence_score(destination,req),.45)
        profile['evidence']['Feiern'][0]['latitude']=47.019
        self.assertEqual(evidence_score(destination,req),1)

    def test_disabled_surroundings_removes_far_away_interest_evidence(self):
        f=fixtures.EvidenceSelectionTests().f(1,{'leisure':'swimming_area'},47.05)
        p=place();p['feature_profile']=feature_profile([f],p,[dict(name='TEST')])
        self.assertGreater(evidence_score(p,request(interests={'Baden':5},surroundings=True)),0)
        self.assertEqual(evidence_score(p,request(interests={'Baden':5},surroundings=False)),0)


class GoverningEvidenceTests(unittest.TestCase):
    def test_named_museum_is_not_hidden_by_nearer_artworks_and_anchor_survives_merge(self):
        factory=fixtures.EvidenceSelectionTests()
        features=[factory.f(i,{'tourism':'artwork'},47+i*.0001) for i in range(8)]
        museum=factory.f(99,{'tourism':'museum','name':'TEST Museum'},47.01);features.append(museum)
        profile=feature_profile(features,place(),[dict(name='TEST')])
        proof=next(p for p in profile['evidence']['Kultur'] if p['id']==museum['id'])
        self.assertTrue(proof['cultural_anchor']);self.assertEqual(profile['evidence']['Kultur'][0]['id'],museum['id'])
        museum['latitude']=47
        profile=feature_profile([museum],place(),[dict(name='TEST')])
        self.assertTrue(profile['evidence']['Kultur'][0]['cultural_anchor'])

    def test_private_museum_cannot_validate_a_strong_public_culture_score(self):
        factory=fixtures.EvidenceSelectionTests()
        features=[factory.f(i,{'tourism':'artwork'}) for i in range(8)]
        private=factory.f(99,{'tourism':'museum','access':'private'});features.append(private)
        profile=feature_profile(features,place(),[dict(name='TEST')])
        self.assertLessEqual(profile['strengths']['Kultur'],.35)
        self.assertNotIn(private['id'],[p['id'] for p in profile['evidence']['Kultur']])

    def test_private_swimming_facility_does_not_upgrade_public_beach_proofs(self):
        factory=fixtures.EvidenceSelectionTests()
        features=[factory.f(i,{'natural':'beach'}) for i in range(3)]+[factory.f(99,{'leisure':'swimming_area','access':'private'})]
        profile=feature_profile(features,place(),[dict(name='TEST')])
        self.assertEqual(profile['strengths']['Baden'],.6)


class CachedCoverageAttemptTests(unittest.TestCase):
    def test_new_source_failure_is_visible_with_existing_compiled_catalog(self):
        with tempfile.TemporaryDirectory() as folder:
            i=DestinationInventory(Path(folder)/'data.db')
            i.replace_country('AT',[place()],{},SearchContext())
            first=i.candidates();self.assertEqual(first[0]['feature_profile']['category_status']['Baden'],'not_investigated')
            i.record_attempt('TEST',[46,10,48,12],'https://example.org','failed','TEST offline',['Baden','Ruhe'])
            second=i.candidates()
            self.assertEqual(second[0]['feature_profile']['category_status']['Baden'],'source_unreachable')
            self.assertEqual(second[0]['feature_profile']['category_status']['Ruhe'],'not_investigated')
            self.assertIn('TEST offline',second[0]['feature_profile']['source_errors'])


class GuideEvidenceSupplementTests(unittest.TestCase):
    def test_researched_guide_evidence_supplements_unknown_osm_with_sources(self):
        from src.vacation_planner.core.planning.RankingService import RankingService
        p=place();p['feature_profile']=feature_profile([],p,[])
        activity=dict(id='guide:1',name='TEST Museum',topics=['Kultur'],latitude=47,longitude=11,distance_km=.5,source='https://example.org/museum',retrieved_at='2026-10-30T10:00:00+00:00')
        r=request(interests={'Kultur':5})
        self.assertEqual(RankingService.interest_match(p,r),0)
        self.assertGreater(RankingService.interest_match(p,r,[activity]),0)
        proof=RankingService.interest_evidence(p,[activity],r)['Kultur']
        self.assertEqual(proof['sources'],[activity['source']]);self.assertEqual(proof['status'],'evidence_present')
        self.assertLessEqual(RankingService.interest_match(p,r,[activity]),.4)
        self.assertEqual(p['feature_profile']['counts'],{})

    def test_unlocated_guide_entries_and_green_space_do_not_invent_suitability(self):
        from src.vacation_planner.core.planning.RankingService import RankingService
        p=place();p['feature_profile']=feature_profile([],p,[])
        activity=dict(id='guide:1',name='TEST Park',topics=['Natur','Ruhe'],latitude=47,longitude=11,distance_km=.5,source='https://example.org/park')
        self.assertEqual(RankingService.interest_match(p,request(interests={'Ruhe':5}),[activity]),0)
        activity.pop('latitude')
        self.assertEqual(RankingService.interest_match(p,request(interests={'Natur':5}),[activity]),0)


class UnknownSourceResearchTests(unittest.TestCase):
    def test_known_guide_can_guide_unknown_research_without_suitability_bonus(self):
        from src.vacation_planner.core.planning.CandidateSelection import select_candidates
        from src.vacation_planner.core.planning.RankingService import RankingService
        unknown=place();unknown['feature_profile']=feature_profile([],unknown,[])
        guide=copy.deepcopy(unknown);guide.update(id='guide',source='https://example.org/guide',wikivoyage_source='https://example.org/guide',latitude=48)
        req=request(interests={'Wandern':5})
        chosen,counts=select_candidates([unknown,guide],req,dict(latitude=46,longitude=11),SearchContext())
        self.assertEqual(chosen[0]['id'],'guide');self.assertEqual(RankingService.interest_match(guide,req),0)
        self.assertEqual(counts['source_guided_unknown_research'],1)
        unknown['feature_profile']['strengths']['Wandern']=1
        chosen,_=select_candidates([unknown,guide],req,dict(latitude=46,longitude=11),SearchContext())
        self.assertEqual(chosen[0]['id'],unknown['id'])


class GuideProfileCacheTests(unittest.TestCase):
    def test_warm_catalog_reuses_profiles_and_source_revision_invalidates_them(self):
        from src.vacation_planner.infrastructure.planning.DestinationCatalog import DestinationCatalog
        with tempfile.TemporaryDirectory() as folder:
            i=DestinationInventory(Path(folder)/'data.db')
            i.replace_country('AT',[place()],{},SearchContext())
            with patch.object(i,'profile_place',wraps=i.profile_place) as compute:
                DestinationCatalog(i);first=compute.call_count
                DestinationCatalog(i);self.assertEqual(compute.call_count,first)
                i.replace_features('TEST',[46.9,10.9,47.1,11.1],[],SearchContext(),'TEST source')
                DestinationCatalog(i);self.assertGreater(compute.call_count,first)


class CancelledCountryAttemptTests(unittest.TestCase):
    def test_service_records_cancelled_country_and_keeps_completed_dataset(self):
        with tempfile.TemporaryDirectory() as folder:
            i=DestinationInventory(Path(folder)/'data.db');i.replace_country('AT',[place()],{},SearchContext());before=i.coverage()
            downloads=Path(folder)/'destination-downloads';downloads.mkdir();(downloads/'admin1CodesASCII.txt').write_text('AT.07\tTyrol\n')
            (downloads/'AT.zip').write_bytes(fixtures.archive([fixtures.row(1)]).getvalue())
            with patch.object(i,'replace_country',side_effect=InterruptedError('TEST cancelled')):
                with self.assertRaises(InterruptedError):DestinationImportService(i).import_countries(['AT'],SearchContext())
            self.assertEqual(i.attempts()[0]['status'],'cancelled');self.assertEqual(i.coverage(),before)
