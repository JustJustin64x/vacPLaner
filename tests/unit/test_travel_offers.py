import copy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import tempfile
import unittest

from src.vacation_planner.core.planning.TravelOffers import OfferQuery, OfferResult, TravelOffer, amount, expire_offers
from src.vacation_planner.core.planning.OfferResearchService import OfferResearchService
from src.vacation_planner.core.planning.RankingService import RankingService
from src.vacation_planner.core.planning.SearchContext import SearchContext
from src.vacation_planner.infrastructure.planning.RegioJetOfferProvider import RegioJetOfferProvider
from src.vacation_planner.infrastructure.planning.SmoobuOfferProvider import SmoobuOfferProvider
from src.vacation_planner.infrastructure.planning.TripStore import TripStore
from src.vacation_planner.infrastructure.planning.PdfTripPresenter import PdfTripPresenter
from src.vacation_planner.infrastructure.planning.TripPdfExporter import TripPdfExporter
from src.vacation_planner.entrypoints.gui.TripPresenter import TripPresenter
from tests.unit.test_surprise_planning import fixture_trip

FIX=Path(__file__).resolve().parents[1]/'fixtures/offers'


def stamp():return datetime.now(timezone.utc).isoformat(timespec='seconds')


class RealResponseParserTests(unittest.TestCase):
    def setUp(self):
        self.query=OfferQuery('Berlin','Innsbruck','2026-11-23','2026-11-25',2,1)
        self.hotel=json.loads((FIX/'smoobu-2026-11-23.json').read_text())
        self.rail=json.loads((FIX/'regiojet-prague-brno-2026-11-12.json').read_text())

    def hotels(self,response=None,query=None):
        return SmoobuOfferProvider.parse_response(response or self.hotel,query or self.query,SmoobuOfferProvider.SOURCES[0],stamp(),'https://booking.smoobu.com/perfect-lodgings/checkAvailability')

    def test_real_hotel_totals_and_cleaning_not_multiplied_by_nights(self):
        offers=self.hotels();self.assertGreaterEqual(len(offers),2)
        self.assertEqual(offers[0].original_amount,'234.00')
        self.assertEqual(offers[0].price_basis,'group_stay')
        self.assertEqual(sum(amount(x['amount']) for x in offers[0].evidence['components']),amount('234'))
        self.assertIn('Cleaning fee: 70.00 EUR',offers[0].included)

    def test_hotel_checks_echo_of_dates_adults_and_units(self):
        for changed in (OfferQuery('Berlin','Innsbruck','2026-11-24','2026-11-26',2,1),OfferQuery('Berlin','Innsbruck','2026-11-23','2026-11-25',1,1)):
            with self.subTest(query=changed),self.assertRaises(ValueError):self.hotels(query=changed)
        invalid=copy.deepcopy(self.hotel);invalid['data']['apartments'][0]['bookUrl']=invalid['data']['apartments'][0]['bookUrl'].replace('apartmentId=','apartmentId=999')
        with self.assertRaises(ValueError):self.hotels(invalid)

    def test_unrelated_properties_and_unconfirmed_capacity_are_rejected(self):
        response=copy.deepcopy(self.hotel)
        for item in response['data']['apartments']:item['id']=999
        self.assertEqual(self.hotels(response),[])
        self.assertEqual(self.hotels(query=OfferQuery('Berlin','Innsbruck','2026-11-23','2026-11-25',40,1)),[])

    def test_components_and_currency_must_agree(self):
        for change in ('amount','currency'):
            d=copy.deepcopy(self.hotel);identifier=str(d['data']['apartments'][0]['id'])
            if change=='amount':d['data']['availabilityResponse']['prices'][identifier]['price']+=10
            else:
                for e in d['data']['availabilityResponse']['prices'][identifier]['priceElements']:e['currencyCode']='USD'
            if change=='amount':
                with self.assertRaises(ValueError):self.hotels(d)
            else:self.assertNotIn(identifier,[x.details['property']['id'].split(':')[1] for x in self.hotels(d)])

    def test_real_rail_fare_is_group_price_not_times_passengers(self):
        fare=RegioJetOfferProvider.parse_detail(self.rail,2,10202003,10202002,'2026-11-12')
        self.assertEqual(fare['price'],'16.80');self.assertEqual(fare['duration_hours'],2.65)
        self.assertEqual(fare['transfers'],0)
        self.assertIsNone(RegioJetOfferProvider.parse_detail(self.rail,5,10202003,10202002,'2026-11-12'))

    def test_rail_rejects_changed_parameters_first_class_and_no_capacity(self):
        with self.assertRaises(ValueError):RegioJetOfferProvider.parse_detail(self.rail,2,10202003,10202002,'2026-11-13')
        d=copy.deepcopy(self.rail);d['priceClasses']=[x for x in d['priceClasses'] if x['seatClassKey']=='C2']
        self.assertIsNone(RegioJetOfferProvider.parse_detail(d,2,10202003,10202002,'2026-11-12'))
        d=copy.deepcopy(self.rail)
        for c in d['priceClasses']:c['freeSeatsCount']=1
        self.assertIsNone(RegioJetOfferProvider.parse_detail(d,2,10202003,10202002,'2026-11-12'))

    def test_decimal_currency_and_occupancy_contract(self):
        self.assertEqual(amount('1.234,56'),amount('1234.56'))
        self.assertEqual(OfferQuery('A','B','2026-11-01','2026-11-02',5,3).occupancy,(2,2,1))
        for a in ('NaN','-1','Infinity'):
            with self.assertRaises(ValueError):amount(a)
        with self.assertRaises(ValueError):TravelOffer('P','flight','1','https://example.org',stamp(),{},'123','USD','group_roundtrip','123')

    def test_query_keys_separate_all_price_parameters(self):
        queries=[self.query,OfferQuery('Berlin','Innsbruck','2026-11-23','2026-11-25',3,1),OfferQuery('Berlin','Innsbruck','2026-11-23','2026-11-25',2,2)]
        self.assertEqual(len({q.cache_key('P','lodging') for q in queries}),3)
        self.assertNotEqual(self.query.cache_key('P','lodging'),self.query.cache_key('P','rail'))


class OfferIntegrationTests(unittest.TestCase):
    def hotel_trip_and_provider(self):
        trip=fixture_trip();trip['destination']['name']='Innsbruck';trip.update(start='2026-11-23',end='2026-11-25',nights=2)
        trip['request'].update(adults=2,rooms=1)
        body=json.loads((FIX/'smoobu-2026-11-23.json').read_text())
        class Http:
            def json(self,url,context):context.consume();return body,stamp()
        return trip,SmoobuOfferProvider(Http())

    def test_prices_survive_recompute_store_gui_and_pdf_model(self):
        trip,provider=self.hotel_trip_and_provider();before=copy.deepcopy(trip)
        updated=OfferResearchService([provider]).research(trip,SearchContext())
        self.assertEqual(trip,before);self.assertEqual(updated['selected_lodging'],trip['selected_lodging'])
        priced=[i for i,l in enumerate(updated['lodgings']) if l.get('offer_id')];self.assertGreaterEqual(len(priced),2)
        updated['selected_lodging']=priced[0];RankingService.recompute(updated)
        self.assertEqual(updated['lodgings'][priced[0]]['price']['low'],'234.00')
        with tempfile.TemporaryDirectory() as folder:
            store=TripStore(Path(folder)/'db.sqlite3');key=store.save('Prüfreise',updated);reopened=store.load(key)
            self.assertIn('234,00 €',str(TripPresenter.sections(reopened)))
            model=PdfTripPresenter.present(reopened)
            self.assertEqual(model['lodging']['price'],'234,00 €')
            self.assertIn('bestätigt',model['lodging']['occupancy'])
            path=Path(folder)/'preise.pdf';TripPdfExporter().export_trips(path,[reopened])
            from pypdf import PdfReader
            pdf_text='\n'.join(page.extract_text() for page in PdfReader(path).pages)
            self.assertIn('234,00 €',pdf_text);self.assertIn('Cleaning fee: 70.00 EUR',pdf_text)

    def test_errors_no_offers_and_abort_do_not_delete_other_category(self):
        trip,hotel=self.hotel_trip_and_provider()
        class Failed:
            category='rail';name='Fehlerquelle'
            def search(self,*args):raise OSError('HTTP 403')
        r=OfferResearchService([hotel,Failed()]).research(trip,SearchContext())
        self.assertEqual(r['offer_searches']['lodging']['status'],'found');self.assertEqual(r['offer_searches']['rail']['status'],'blocked')
        class Cancelled(Failed):
            def search(self,*args):raise InterruptedError('abgebrochen')
        r=OfferResearchService([hotel,Cancelled()]).research(trip,SearchContext())
        self.assertEqual(r['offer_searches']['rail']['status'],'cancelled');self.assertTrue(r['offer_searches']['lodging']['offers'])

    def test_expired_price_is_not_budget_eligible_and_does_not_refresh_network(self):
        trip,provider=self.hotel_trip_and_provider();r=OfferResearchService([provider]).research(trip,SearchContext())
        r['selected_lodging']=next(i for i,x in enumerate(r['lodgings']) if x.get('offer_id'))
        expire_offers(r,datetime.now(timezone.utc)+timedelta(hours=1));RankingService.recompute(r)
        self.assertEqual(r['lodgings'][r['selected_lodging']]['price']['status'],'veraltet')
        self.assertEqual(r['offer_searches']['lodging']['status'],'stale');self.assertIsNone(r['cost_summary']['budget_ok'])

    def test_multi_room_never_multiplies_a_single_apartment_price(self):
        trip,provider=self.hotel_trip_and_provider();trip['request'].update(adults=5,rooms=3)
        r=OfferResearchService([provider]).research(trip,SearchContext())
        self.assertEqual(r['offer_searches']['lodging']['status'],'unsupported')
        self.assertFalse(any(x.get('offer_id') for x in r['lodgings']))

    def test_flexible_dates_keep_categories_together_and_do_not_change_selection(self):
        trip,_=self.hotel_trip_and_provider();trip['date_options']=[('2026-11-23','2026-11-25'),('2026-11-26','2026-11-28')]
        calls=[]
        class Recorder:
            def __init__(self,category):self.category=category;self.name=category
            def search(self,query,trip,context):
                calls.append((self.category,query.start,query.end));return OfferResult(self.name,self.category,'no_offers',query.to_dict())
        r=OfferResearchService([Recorder('lodging'),Recorder('rail')]).research_samples(trip,SearchContext())
        self.assertEqual((r['start'],r['end'],r['selected_lodging']),(trip['start'],trip['end'],trip['selected_lodging']))
        self.assertEqual([(a,b) for _,a,b in calls],[('2026-11-23','2026-11-25')]*2+[('2026-11-26','2026-11-28')]*2)
        self.assertEqual(len(r['offer_date_samples']),2)

    def test_roundtrip_contract_prevents_double_counting(self):
        trip=fixture_trip();trip['selected_transport']=2
        query=OfferQuery.from_trip(trip)
        offer=TravelOffer('Unit-test only','flight','test-roundtrip','https://example.org/roundtrip',stamp(),query.to_dict(),'500','EUR','group_roundtrip','500',
                          details={'legs':[{'duration_hours':2},{'duration_hours':3}]})
        class Provider:
            category='flight';name='Unit-test only'
            def search(self,*args):return OfferResult(self.name,self.category,'found',query.to_dict(),[offer])
        r=OfferResearchService([Provider()]).research(trip,SearchContext())
        self.assertEqual(r['transports'][2]['costs'][0]['low'],'500.00')
        self.assertEqual(r['cost_summary']['low'],'500.00')

    def test_previous_offer_expires_even_after_failed_refresh(self):
        trip,provider=self.hotel_trip_and_provider();r=OfferResearchService([provider]).research(trip,SearchContext())
        r['selected_lodging']=next(i for i,x in enumerate(r['lodgings']) if x.get('offer_id'))
        class Failed:
            category='lodging';name='offline'
            def search(self,*args):raise OSError('offline')
        r=OfferResearchService([Failed()]).research(r,SearchContext());expire_offers(r,datetime.now(timezone.utc)+timedelta(hours=1))
        self.assertEqual(r['lodgings'][r['selected_lodging']]['price']['status'],'veraltet')

    def test_changed_connection_is_an_alternative_and_does_not_replace_selection(self):
        trip=fixture_trip();trip['selected_transport']=1;query=OfferQuery.from_trip(trip)
        class Provider:
            category='rail';name='Unit-test only'
            def __init__(self,identifier):self.identifier=identifier
            def search(self,*args):
                offer=TravelOffer(self.name,'rail',self.identifier,'https://example.org/offer',stamp(),query.to_dict(),'50','EUR','group_roundtrip','50')
                return OfferResult(self.name,'rail','found',query.to_dict(),[offer])
        first=OfferResearchService([Provider('original')]).research(trip,SearchContext())
        second=OfferResearchService([Provider('new-connection')]).research(first,SearchContext())
        self.assertEqual(second['selected_transport'],1)
        self.assertEqual(second['transports'][1]['offer_id'],'original')
        self.assertEqual(second['transports'][1]['costs'][0]['status'],'veraltet')
        self.assertEqual(second['transports'][-1]['offer_id'],'new-connection')


if __name__=='__main__':unittest.main()
