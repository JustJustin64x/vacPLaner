import copy
from datetime import datetime,timedelta,timezone
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
from src.vacation_planner.core.planning.CandidateIdeas import IdeaReferences,geographic_allowed
from src.vacation_planner.core.planning.SearchRequest import SearchRequest
from src.vacation_planner.core.planning.SearchContext import SearchContext
from src.vacation_planner.core.planning.ResearchAssessment import assess_research
from src.vacation_planner.infrastructure.planning.CandidateDiscoveryService import CandidateDiscoveryService
from src.vacation_planner.infrastructure.planning.DestinationInventory import DestinationInventory
from src.vacation_planner.infrastructure.planning.DestinationCatalog import DestinationCatalog
from src.vacation_planner.infrastructure.planning.TripStore import TripStore
import tests.unit.test_source_research as research_fixture
from tests.unit.test_destination_inventory import place
from tests.unit.test_surprise_planning import fixture_trip


def query(**kwargs):return SearchRequest(earliest='2090-07-01',latest='2090-07-31',ai_discovery=True,**kwargs)


class IdeaModel:
    def __init__(self,ideas=None,error=None):self.ideas=ideas;self.error=error;self.messages=[]
    def chat(self,messages,schema=None,**kwargs):
        self.messages.append(messages)
        if self.error:raise self.error
        refs=json.loads(messages[-1]['content'])['references']
        ideas=self.ideas if self.ideas is not None else [dict(reference=p['reference'],name=p['name'],country=p['country'],region='') for p in refs[:2]]
        return dict(parsed=dict(ideas=ideas))


class CandidateTests(unittest.TestCase):
    def setUp(self):
        self.directory=tempfile.TemporaryDirectory();self.inventory=DestinationInventory(Path(self.directory.name)/'destinations.sqlite3')
        self.inventory.replace_country('AT',[place(1,name='Eindeutig',lat=47.0),dict(place(2,name='Gleich'),region='Tirol',regions=['Tirol']),
            dict(place(3,name='Gleich',lon=14.5),region='Salzburg',regions=['Salzburg']),
            dict(place(4,name='Weißsee'),aliases=['Weisssee'])],{},SearchContext())
        self.catalog=DestinationCatalog(self.inventory);self.origin=dict(latitude=52.52,longitude=13.405)
    def tearDown(self):self.directory.cleanup()
    def service(self,ideas=None,error=None):return CandidateDiscoveryService(self.catalog,client=IdeaModel(ideas,error))
    def run_ideas(self,ideas,request=None):
        report={};s=self.service(ideas);result=s.suggest(self.catalog.candidates(request or query()),[],[],request or query(),self.origin,SearchContext(seconds=10),lambda *x:None,report)
        return result,report['ai_discovery']
    def test_full_country_identity_not_small_legacy_list_and_homonyms(self):
        result,report=self.run_ideas([dict(reference='',name='Eindeutig',country='AT',region='')])
        self.assertEqual(len(result),1);self.assertEqual(result[0]['id'],'geonames:1')
        self.assertEqual(result[0]['latitude'],47.0)
        result,report=self.run_ideas([dict(reference='',name='Gleich',country='AT',region='')]);self.assertFalse(result)
        result,report=self.run_ideas([dict(reference='',name='Gleich',country='AT',region='Salzburg')]);self.assertEqual(result[0]['id'],'geonames:3')
    def test_alias_normalisation_and_no_like_limit(self):
        rows=self.inventory.exact_named_places('Weisssee','AT','',SearchContext());self.assertEqual(len(rows),1)
        rows=self.inventory.exact_named_places('Weiss','AT','',SearchContext());self.assertFalse(rows)
        self.assertFalse(self.inventory.exact_named_places('Eindeutig','DE','',SearchContext()))
    def test_fabricated_country_region_and_region_object_rejected(self):
        for name,country,region in [('Erfundenerort','AT',''),('Eindeutig','DE',''),('Eindeutig','AT','Unbekannt')]:
            result,report=self.run_ideas([dict(reference='',name=name,country=country,region=region)])
            self.assertFalse(result);self.assertEqual(report['rejected'],1)
    def test_call_references_exact_and_never_cross_calls(self):
        d=self.catalog.resolve('Eindeutig, AT');a=IdeaReferences([d]);b=IdeaReferences([d]);key=next(iter(a.mapping))
        row=dict(reference=key,name=d['name'],country='AT',region='')
        self.assertEqual(a.resolve(row)['id'],d['id'])
        with self.assertRaises(ValueError):b.resolve(row)
        with self.assertRaises(ValueError):a.resolve(dict(row,name='Anders'))
        self.assertNotIn(d['id'],json.dumps(a.schema(['AT'])))
    def test_hard_geography_radius_type_and_exclusions_preserved(self):
        d=self.catalog.resolve('Eindeutig, AT')
        for args in (dict(countries=['DE']),dict(excluded=['Eindeutig']),dict(regions=['Salzburg']),dict(target_type='Stadt'),dict(max_distance_km='10')):
            self.assertFalse(geographic_allowed(self.catalog,d,query(**args),self.origin),args)
        self.assertFalse(geographic_allowed(self.catalog,dict(d,kind='region'),query(),self.origin))
        self.assertFalse(geographic_allowed(self.catalog,dict(d,latitude=float('nan')),query(),self.origin))
    def test_duplicate_known_candidate_is_not_returned(self):
        d=self.catalog.resolve('Eindeutig, AT');report={};s=self.service([dict(reference='',name='Eindeutig',country='AT',region='')])
        rows=s.suggest(self.catalog.candidates(query()),[d],[],query(),self.origin,SearchContext(),lambda *x:None,report)
        self.assertFalse(rows);self.assertEqual(report['ai_discovery']['rejected'],1)
    def test_model_unavailable_or_invalid_keeps_baseline_and_no_private_context(self):
        q=query(origin='Privater Start',address='PRIVATE ADRESSE',budget='5432',adults=5)
        s=self.service(error=OSError('offline'));report={}
        rows=s.suggest(self.catalog.candidates(q),[],[],q,self.origin,SearchContext(),lambda *x:None,report)
        self.assertFalse(rows);self.assertEqual(report['ai_discovery']['status'],'model_unavailable_or_invalid')
        data=json.dumps(s.client.messages,ensure_ascii=False)
        for value in ('PRIVATE ADRESSE','Privater Start','5432','adults','earliest'):self.assertNotIn(value,data)
    def test_cancel_and_rest_budget_prevent_model_and_lookup(self):
        c=SearchContext(budget=0);s=self.service();report={}
        self.assertFalse(s.suggest([],[],[],query(),self.origin,c,lambda *x:None,report));self.assertFalse(s.client.messages)
        c=SearchContext();c.cancel.set()
        with self.assertRaises(InterruptedError):self.inventory.exact_named_places('Eindeutig','AT','',c)
    def test_opt_in_boolean_is_strict(self):
        self.assertFalse(SearchRequest().ai_discovery)
        with self.assertRaises(ValueError):SearchRequest(earliest='2090-07-01',latest='2090-07-31',ai_discovery='ja').validate()
