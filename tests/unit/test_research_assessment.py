import copy
from datetime import datetime,timedelta,timezone
import json
import unittest
from src.vacation_planner.core.planning.ResearchAssessment import assess_research
from src.vacation_planner.core.planning.RankingService import RankingService
from src.vacation_planner.core.planning.SearchRequest import SearchRequest
from src.vacation_planner.core.planning.DestinationFeatures import feature_profile
from src.vacation_planner.infrastructure.local_ai.ExplanationService import ExplanationService
import tests.unit.test_source_research as fixture


class AssessmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):fixture.ResearchTests.setUpClass()
    @classmethod
    def tearDownClass(cls):fixture.ResearchTests.tearDownClass()
    def setUp(self):
        self.fixture=fixture.ResearchTests('test_real_fixture_http_identity_provenance_and_no_trip_mutation');self.fixture.setUp()
        self.trip=self.fixture.enrich();self.trip['activities']=[]
        self.trip['destination']['feature_profile']=feature_profile([],self.trip['destination'],[])
        self.request=SearchRequest(**dict(self.trip['request'],interests={'Kultur':5},ai_discovery=True))
        self.trip['request']=self.request.to_dict();self.trip['interest_evidence']={};self.trip['interest_match']=0
        RankingService.recompute(self.trip)
        self.before=copy.deepcopy(self.trip);self.now=datetime.now(timezone.utc)
    def tearDown(self):self.fixture.tearDown()
    def assess(self):return assess_research(self.trip,self.request,self.now)
    def test_only_controlled_culture_contribution_and_budget_preserved(self):
        self.assess();a=self.trip['research_assessment']
        self.assertEqual(len(a['accepted']),1);self.assertEqual(len(a['rejected']),2)
        self.assertAlmostEqual(a['signal'],.1);self.assertAlmostEqual(a['delta'],.05)
        self.assertGreater(self.trip['score'],self.before['score'])
        self.assertEqual(self.trip['cost_summary'],self.before['cost_summary'])
        self.assertIn('keine Öffnungs',self.trip['interest_evidence']['Kultur']['explanation'])
    def test_repeated_assessment_cannot_accumulate_bonus(self):
        self.assess();once=copy.deepcopy(self.trip);self.assess();self.assertEqual(self.trip,once)
    def test_distance_and_interest_combination_bound_contribution(self):
        self.request.interests={'Kultur':1,'Baden':5,'Wandern':5}
        self.assess();self.assertLessEqual(self.trip['research_assessment']['delta'],.1/11)
        self.trip=copy.deepcopy(self.before);e=self.trip['source_research']['evidence'][0]
        e['subject']['coordinates']['latitude']+=.1;p=json.loads(e['quote']);p['latitude']=e['subject']['coordinates']['latitude'];e['quote']=json.dumps(p)
        self.assess();self.assertFalse(self.trip['research_assessment']['accepted'])
    def test_opt_out_and_unselected_interest_have_no_new_effect(self):
        self.request.ai_discovery=False;self.assess();self.assertEqual(self.trip,self.before)
        self.request.ai_discovery=True;self.request.interests={'Baden':5,'Ruhe':5}
        self.assess();self.assertEqual(self.trip['research_assessment']['delta'],0)
    def test_shared_identity_across_sources_never_counts_twice(self):
        original=self.trip['source_research']['evidence'][0]
        other=copy.deepcopy(original);other['id']='second-source';other['source_url']+='-other'
        self.trip['source_research']['evidence'].append(other);self.assess()
        self.assertEqual(len(self.trip['research_assessment']['accepted']),1)
    def test_existing_osm_qid_or_same_name_point_blocks_duplicate(self):
        original=self.trip['source_research']['evidence'][0]
        for known in (dict(id='osm:node:123',wikidata_id=original['subject']['id'],name='Anderer Name',**original['subject']['coordinates']),
                      dict(id='osm:node:456',name=original['subject']['name'],**original['subject']['coordinates'])):
            self.trip=copy.deepcopy(self.before);self.trip['activities']=[dict(known,topics=['Kultur'],source='https://www.openstreetmap.org/node/123')]
            self.assess();self.assertFalse(self.trip['research_assessment']['accepted']);self.assertEqual(self.trip['research_assessment']['delta'],0)
    def test_smaller_explicit_radius_is_enforced_without_surroundings(self):
        self.request.surroundings=False;self.request.activity_radius_km='0.01'
        e=self.trip['source_research']['evidence'][0];e['subject']['coordinates']['latitude']+=.005
        p=json.loads(e['quote']);p['latitude']=e['subject']['coordinates']['latitude'];e['quote']=json.dumps(p)
        self.assess();self.assertFalse(self.trip['research_assessment']['accepted'])
        self.assertIn('Kulturumkreis',self.trip['research_assessment']['rejected'][0]['reason'])
    def test_text_length_and_model_selection_do_not_affect_value(self):
        first=self.assess()['research_assessment']['after'];self.trip=copy.deepcopy(self.before)
        e=self.trip['source_research']['evidence'][0];p=json.loads(e['quote']);p['description']='a'*10000;e['quote']=json.dumps(p);e['model_selected']=False
        self.assertEqual(self.assess()['research_assessment']['after'],first)
    def test_saturation_and_max_increase_even_with_many_distinct_objects(self):
        base=self.trip['source_research']['evidence'][0];self.trip['source_research']['evidence']=[]
        for n in range(30):
            e=copy.deepcopy(base);e['id']='proof'+str(n);e['subject']['id']='Q'+str(10000+n);e['subject']['name']='Museum '+str(n)
            e['subject']['coordinates']['latitude']+=n*.00001
            p=json.loads(e['quote']);p['name']=e['subject']['name'];p['latitude']=e['subject']['coordinates']['latitude'];e['quote']=json.dumps(p)
            self.trip['source_research']['evidence'].append(e)
        a=self.assess()['research_assessment'];self.assertEqual(len(a['accepted']),3);self.assertEqual(a['signal'],.25);self.assertLessEqual(a['delta'],.05)
    def test_conflict_and_permanent_closure_block_subject(self):
        for field,value in [('conflict','abweichend'),('quote','Dauerhaft geschlossen')]:
            self.trip=copy.deepcopy(self.before);e=self.trip['source_research']['evidence'][1];e[field]=value
            self.assess();self.assertFalse(self.trip['research_assessment']['accepted'])
    def test_old_future_unknown_or_other_target_not_upgraded(self):
        for change in (dict(retrieved_at=(self.now-timedelta(days=31)).isoformat()),dict(retrieved_at=(self.now+timedelta(hours=1)).isoformat()),dict(retrieved_at=None),dict(target_id='another-place')):
            self.trip=copy.deepcopy(self.before);self.trip['source_research']['evidence'][0].update(change)
            self.assess();self.assertFalse(self.trip['research_assessment']['accepted'])
    def test_lake_path_bar_unknown_opening_and_nan_do_not_become_culture(self):
        for kind in ('lake','hiking_trail','bar'):
            self.trip=copy.deepcopy(self.before);e=self.trip['source_research']['evidence'][0];p=json.loads(e['quote']);p['type']=[kind];e['quote']=json.dumps(p)
            self.assess();self.assertFalse(self.trip['research_assessment']['accepted'])
        self.trip=copy.deepcopy(self.before);e=self.trip['source_research']['evidence'][0];e['subject']['coordinates']['latitude']=float('nan')
        self.assess();self.assertFalse(self.trip['research_assessment']['accepted'])
    def test_zero_interest_weight_and_unknown_price_no_price_bonus(self):
        self.request.weights={'Preis':100,'Interessen':0,'Reisezeit':0,'Komfort':0};self.trip['request']=self.request.to_dict();RankingService.recompute(self.trip);before=self.trip['score']
        self.assess();self.assertEqual(self.trip['score'],before)
        self.assertTrue(self.trip['cost_summary']['missing'])
    def test_confidence_and_cache_state_visible_in_working_copy_only(self):
        key=ExplanationService.key(self.trip);saved=self.fixture.store.save('Alt',self.trip)
        self.assess();self.assertNotEqual(key,ExplanationService.key(self.trip));self.assertNotIn('research_assessment',self.fixture.store.load(saved))
        fresh=self.fixture.store.save('Neu',self.trip);self.assertEqual(self.fixture.store.load(fresh)['research_assessment'],self.trip['research_assessment'])
