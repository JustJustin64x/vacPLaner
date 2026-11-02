import copy
import unittest
from unittest.mock import patch
from src.vacation_planner.core.planning.SearchContext import SearchContext
from src.vacation_planner.core.planning.SearchRequest import SearchRequest
from src.vacation_planner.infrastructure.planning.CandidateDiscoveryService import CandidateDiscoveryService
from src.vacation_planner.infrastructure.planning.DestinationCatalog import DestinationCatalog
import tests.unit.test_source_research as fixture

MODULE='src.vacation_planner.infrastructure.planning.CandidateDiscoveryService.ResearchHttp'


class PreparationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):fixture.ResearchTests.setUpClass()
    @classmethod
    def tearDownClass(cls):fixture.ResearchTests.tearDownClass()
    def setUp(self):
        self.fixture=fixture.ResearchTests('test_real_fixture_http_identity_provenance_and_no_trip_mutation');self.fixture.setUp()
        self.destination=fixture.trip()['destination'];self.service=CandidateDiscoveryService(DestinationCatalog(),self.fixture.store)
        self.request=SearchRequest(interests={'Kultur':5},ai_discovery=True)
    def tearDown(self):self.fixture.tearDown()
    def prepare(self,context=None,report=None):
        report=report if report is not None else dict(source_targets=0,source_http_calls=0)
        with patch(MODULE,return_value=self.fixture.http):
            d,source=self.service.prepare(self.destination,self.request,context or SearchContext(),lambda *a:None,report)
        return d,source,report
    def test_verified_fixture_page_reused_by_normal_adapter_within_parent_budget(self):
        context=SearchContext(budget=6);before=copy.deepcopy(self.destination)
        d,source,report=self.prepare(context)
        self.assertEqual(len(source['evidence']),3);self.assertEqual(context.calls,5);self.assertEqual(report['source_http_calls'],5)
        self.assertEqual(self.destination,before)
        self.assertTrue(self.fixture.store.cache_get('places-v4:'+d['wikivoyage_source'],7*86400))
        # Only one additional source target even when another candidate exists.
        d,source,report=self.prepare(context,report);self.assertIsNone(source);self.assertEqual(context.calls,5)
    def test_extracted_cache_does_not_trigger_new_unguarded_page_fetch(self):
        d,source,_=self.prepare();self.assertTrue(source['evidence'])
        with self.fixture.store.connect() as db:db.execute("DELETE FROM cache WHERE key LIKE 'places-v4:%'")
        self.fixture.http.memory.clear();context=SearchContext()
        d,source,_=self.prepare(context);self.assertTrue(source['evidence']);self.assertNotIn('wikivoyage_source',d);self.assertEqual(context.calls,0)
    def test_source_failure_or_quota_keeps_original_identity(self):
        for context in (SearchContext(budget=0),SearchContext(budget=1)):
            d,source,_=self.prepare(context);self.assertEqual(d,self.destination)
            self.assertLessEqual(context.calls,context.budget)
            if source:self.assertFalse(source['evidence'])
    def test_cancel_propagates_and_never_changes_destination(self):
        c=SearchContext();c.cancel.set()
        with self.assertRaises(InterruptedError):self.prepare(c)
