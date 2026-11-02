"""Additional ideas use the actual ordinary lodging/transport pipeline."""
import copy
import unittest
from dataclasses import replace
from src.vacation_planner.core.planning.DiscoveryService import DiscoveryService
from src.vacation_planner.core.planning.SearchContext import SearchContext
from src.vacation_planner.core.planning.SearchRequest import SearchRequest
from tests.unit.test_search_improvement import GeographicProvider,catalog
from tests.unit.test_candidate_discovery import IdeaModel
from src.vacation_planner.infrastructure.planning.CandidateDiscoveryService import CandidateDiscoveryService


class ExtensionProvider(GeographicProvider):
    def __init__(self,cat,**kwargs):
        super().__init__(**kwargs);self.cat=cat;self.prepared=[];self.service_calls=0
    def candidate_discovery(self,cat):
        self.service_calls+=1
        model=IdeaModel([dict(reference='',name='Braunlage',country='DE',region='')])
        service=CandidateDiscoveryService(cat,client=model)
        def prepare(d,*args):self.prepared.append(d['name']);return d,None
        service.prepare=prepare
        return service


class IntegrationTests(unittest.TestCase):
    def run_search(self,**kwargs):
        cat=catalog('Hinterzarten','Braunlage');provider=ExtensionProvider(cat,**kwargs.pop('provider',{}))
        q=SearchRequest(earliest='2090-07-01',latest='2090-07-31',ai_discovery=True,surroundings=False,
            candidate_pool=10,shortlist=3,regional_queries=0,price_targets=0,**kwargs)
        # Fix only the deterministic candidate order, never the travel verdict.
        from unittest.mock import patch
        service=DiscoveryService(cat,provider);events=[]
        with patch('src.vacation_planner.core.planning.CandidateSelection.select_candidates',return_value=([cat.destinations[0]],dict(geographic_considered=2,with_interest_evidence=0,features_unknown=2))):
            results=service.search(q,SearchContext(),lambda k,v:events.append((k,v)))
        return results,provider,service.diagnostics.data,events
    def test_additional_candidate_uses_ordinary_pipeline_and_is_visible(self):
        results,p,d,events=self.run_search()
        self.assertEqual(len(results),2);self.assertEqual(p.prepared,['Braunlage'])
        self.assertEqual(d['ai_discovery']['returned_matches'],1)
        self.assertTrue(all(t['filter_status']=='passend' for t in results))
        self.assertTrue(results[0]['cost_summary']['missing'])
        self.assertEqual([v['destination']['name'] for k,v in events if k=='result'][0],'Hinterzarten')
    def test_unknown_required_amenity_stays_open_and_can_be_hidden(self):
        results,p,d,_=self.run_search(required=['Pool'],show_ideas=True)
        extra=[t for t in results if t.get('discovery_origin')]
        self.assertEqual(len(extra),1);self.assertEqual(extra[0]['filter_status'],'offen');self.assertFalse(p.routes)
        results,_,d,_=self.run_search(required=['Pool'],show_ideas=False)
        self.assertFalse(results);self.assertEqual(d['ai_discovery']['returned_matches'],0)
    def test_violated_required_amenity_or_travel_time_never_passes(self):
        results,_,d,_=self.run_search(required=['Pool'],show_ideas=True,provider=dict(amenities={'Pool':False}))
        self.assertFalse(results)
        results,_,d,_=self.run_search(max_hours='1',modes=['Auto'],show_ideas=True)
        self.assertFalse(results)
    def test_unknown_train_duration_remains_open(self):
        results,_,d,_=self.run_search(modes=['Zug'],max_hours='8',show_ideas=True)
        self.assertEqual(d['ai_discovery']['returned_ideas'],1)
        self.assertTrue(all(t['filter_status']=='offen' and 'Reisezeit unbekannt' in t['open_criteria'] for t in results))
    def test_core_rechecks_geography_even_if_extension_returns_bad_candidate(self):
        from unittest.mock import patch
        original=CandidateDiscoveryService.suggest
        for changes in (dict(code='XX'),dict(code='RU',latitude=60,longitude=100),dict(kind='region'),dict(latitude=52.52,longitude=13.405)):
            def corrupt(service,*args,**kwargs):
                rows=original(service,*args,**kwargs)
                for d in rows:d.update(changes)
                return rows
            with patch.object(CandidateDiscoveryService,'suggest',corrupt):
                results,p,d,_=self.run_search()
            self.assertEqual(len(results),1);self.assertFalse(p.prepared)
            self.assertEqual(d['ai_discovery']['returned_matches'],0)
    def test_optional_failure_preserves_already_emitted_regular_result(self):
        from unittest.mock import patch
        for failure in (OSError('offline'),RuntimeError('unexpected extension error')):
            with patch.object(CandidateDiscoveryService,'suggest',side_effect=failure):
                results,p,d,events=self.run_search()
            self.assertEqual(len(results),1);self.assertEqual(d['ai_discovery']['status'],'extension_failed')
            self.assertTrue(any(k=='result' for k,v in events));self.assertTrue(d['errors'])
    def test_opt_out_never_constructs_model_service(self):
        # Exercise the same public path separately to avoid duplicate kwargs.
        cat=catalog('Hinterzarten');p=ExtensionProvider(cat)
        DiscoveryService(cat,p).search(SearchRequest(earliest='2090-07-01',latest='2090-07-31',surroundings=False,price_targets=0),SearchContext(),lambda *a:None)
        self.assertEqual(p.service_calls,0)
    def test_unsupported_provider_preserves_normal_results(self):
        service=DiscoveryService(catalog('Hinterzarten'),GeographicProvider())
        result=service.search(SearchRequest(earliest='2090-07-01',latest='2090-07-31',ai_discovery=True,surroundings=False,price_targets=0),SearchContext(),lambda *a:None)
        self.assertEqual(len(result),1);self.assertEqual(service.diagnostics.data['ai_discovery']['status'],'provider_not_supported')
