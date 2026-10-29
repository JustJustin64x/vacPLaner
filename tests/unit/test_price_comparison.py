import copy
from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
import unittest

from src.vacation_planner.core.planning.TravelComparison import comparison
from src.vacation_planner.core.planning.OfferResearchService import OfferResearchService
from src.vacation_planner.core.planning.SearchContext import SearchContext
from src.vacation_planner.core.planning.TravelOffers import expire_offers
from src.vacation_planner.infrastructure.planning.OfficialActivityPrices import OfficialActivityPrices
from src.vacation_planner.infrastructure.planning.PdfTripPresenter import PdfTripPresenter
from src.vacation_planner.infrastructure.planning.TripPdfExporter import TripPdfExporter
from src.vacation_planner.infrastructure.planning.TripStore import TripStore
from src.vacation_planner.entrypoints.gui.TripPresenter import TripPresenter
from tests.unit.test_surprise_planning import fixture_trip, request, FixtureProvider


class ComparisonTests(unittest.TestCase):
    def test_auto_only_snapshot_exports_all_modes_without_mutation(self):
        trip=fixture_trip();trip['transports']=trip['transports'][:1];before=copy.deepcopy(trip)
        model=PdfTripPresenter.present(trip)
        self.assertEqual([t['mode'] for t in model['transports']],['Auto','Zug','Flug'])
        self.assertEqual(trip,before)
        self.assertIn('Nicht geprüft',model['transports'][2]['status'])
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'comparison.pdf';TripPdfExporter().export_trips(path,[trip])
            from pypdf import PdfReader
            text='\n'.join(p.extract_text() for p in PdfReader(path).pages)
            for phrase in ('Auto','Zug','Flug','getrennte Szenarien','Pro Person','Hin- und Rückreise'):
                self.assertIn(phrase,text)

    def test_scenarios_do_not_add_alternatives_or_optional_activities(self):
        trip=fixture_trip();trip['lodgings'][0]['price']={'label':'Unterkunft','low':'200','high':'200','status':'aktuell abgerufen'}
        trip['lodgings'][0]['mandatory_costs']=[]
        for t,cost in zip(trip['transports'],('100','150','300')):
            t['costs']=[{'label':'Hin und zurück','low':cost,'high':cost,'status':'aktuell abgerufen'}]
        trip['activities']=[{'activity_price':{'eur_amount':'900'}}]
        rows=comparison(trip)
        self.assertEqual([r['scenario']['low'] for r in rows],['300.00','350.00','500.00'])
        trip['transports'][1]['costs'].append({'label':'Transfer','low':None,'status':'unbekannt'})
        self.assertIsNone(comparison(trip)[1]['scenario']['budget_ok'])

    def test_price_target_validation_and_old_request_defaults(self):
        self.assertEqual(request().price_targets,3)
        request(price_targets=0).validate()
        for value in (-1,13,True,'3'):
            with self.subTest(value=value),self.assertRaises(ValueError):request(price_targets=value).validate()

    def test_research_targets_ranked_shortlist_not_discovery_order(self):
        from src.vacation_planner.core.planning.DiscoveryService import DiscoveryService
        from src.vacation_planner.infrastructure.planning.DestinationCatalog import DestinationCatalog
        catalog=DestinationCatalog();catalog.destinations=[catalog.resolve(x) for x in ('Bled','Innsbruck','Brünn')]
        seen=[];researched=[]
        class Provider(FixtureProvider):
            def research_offers(self,trip,context,emit):
                seen.append(trip['destination']['name']);return trip
        class Discovery(DiscoveryService):
            def research(self,r,ctx,origin,destination,emit):
                researched.append(destination['name'])
                trip=fixture_trip();trip['id']=destination['name'];trip['destination']=destination;trip['score']=len(researched)*10
                self.diagnostics.data['counts']['matches']+=1
                return trip
        result=Discovery(catalog,Provider()).search(request(price_targets=2,shortlist=3),SearchContext(),lambda *a:None)
        self.assertEqual(seen,[t['destination']['name'] for t in result[:2]])
        self.assertEqual(seen,list(reversed(researched))[:2])


class ActivityTests(unittest.TestCase):
    def provider(self,body):
        class Http:
            def get(self,url,context):
                context.consume();return body,datetime.now(timezone.utc).isoformat(timespec='seconds')
        return OfficialActivityPrices(Http())

    def test_tariff_parser_uses_named_standard_price_not_first_number(self):
        body='<ul><li>Spende: 999 Euro</li><li><strong>Standardeintritt</strong>: 6,00 Euro</li><li>Ermäßigt: 3,00 Euro</li></ul>'
        self.assertEqual(OfficialActivityPrices.parse(body,'innsbruck')[0],'6.00')
        with self.assertRaises(ValueError):OfficialActivityPrices.parse('<p>ab 6 Euro</p>','innsbruck')
        self.assertEqual(OfficialActivityPrices.parse('<p>General admission free.</p>','london')[0],'0.00')
        with self.assertRaises(ValueError):OfficialActivityPrices.parse('<p>Admission information unavailable</p>','london')
        self.assertEqual(OfficialActivityPrices.parse('<h2>Tickets</h2><p>Der Eintritt ist kostenfrei.</p>','berlin')[0],'0.00')
        with self.assertRaises(ValueError):OfficialActivityPrices.parse('<h2>Schulkinder</h2><p>Der Eintritt ist kostenfrei.</p>','berlin')

    def test_tariff_not_dated_availability_and_not_part_of_main_budget(self):
        trip=fixture_trip();trip['destination']['name']='Innsbruck';before=trip['cost_summary']['low']
        updated=OfferResearchService([self.provider('<li><strong>Standardeintritt</strong>: 6,00 Euro</li>')]).research(trip,SearchContext())
        offer=updated['activities'][0]['activity_price']
        self.assertEqual(offer['eur_amount'],'30.00');self.assertFalse(offer['details']['date_confirmed'])
        self.assertEqual(updated['cost_summary']['low'],before)
        self.assertIn('keine datierte Eintrittskarte',str(TripPresenter.sections(updated)))
        with tempfile.TemporaryDirectory() as folder:
            store=TripStore(Path(folder)/'store.sqlite3');key=store.save('Tarif-Test',updated)
            reopened=store.load(key)
            self.assertEqual(reopened['activities'][0]['activity_price'],offer)
        expire_offers(updated,datetime.now(timezone.utc)+timedelta(days=2))
        self.assertEqual(updated['activities'][0]['activity_price']['price_status'],'veraltet')
        self.assertIn('veraltet',PdfTripPresenter.present(updated)['activities'][0]['price'])

    def test_skip_one_source_continues_independent_category(self):
        trip=fixture_trip();trip['destination']['name']='London'
        context=SearchContext();context.skipped_categories={'lodging'}
        class Skipped:
            name='Skip test';category='lodging'
            def search(self,*args):raise AssertionError('Übersprungene Quelle aufgerufen')
        result=OfferResearchService([Skipped(),self.provider('<p>General admission free.</p>')]).research(trip,context)
        self.assertEqual(result['offer_searches']['activities']['status'],'found')
        self.assertEqual(result['activities'][0]['activity_price']['eur_amount'],'0.00')

    def test_research_respects_selected_interests(self):
        trip=fixture_trip();trip['destination']['name']='Innsbruck';trip['request']['interests']={'Wandern':5}
        before=copy.deepcopy(trip['activities'])
        result=OfferResearchService([self.provider('<li><strong>Standardeintritt</strong>: 6,00 Euro</li>')]).research(trip,SearchContext())
        self.assertEqual(result['offer_searches']['activities']['status'],'unsupported')
        self.assertEqual(result['activities'],before)


if __name__=='__main__':unittest.main()
