"""Explicit group requests and source-scoped per-unit selections."""
import unittest
from datetime import date
from src.vacation_planner.core.planning.RoomParty import RoomParty,room_parties,ages_from_text
from src.vacation_planner.core.planning.TravelOffers import OfferQuery
from src.vacation_planner.core.planning.ChildAgeRange import ChildAgeRange
from src.vacation_planner.infrastructure.planning.Beds24RoomSelection import selections,Beds24RoomSelection
from src.vacation_planner.infrastructure.planning.Beds24QuoteEvidence import room_facts,child_age_contract
from src.vacation_planner.infrastructure.planning.Beds24ResponsiveQuote import Beds24ResponsiveQuote as Responsive
from tests.unit.test_responsive_lodging import inventory,fixture
from tests.unit.test_general_lodging import item
from src.vacation_planner.infrastructure.planning.TripStore import timestamp

class PartyTests(unittest.TestCase):
    def test_explicit_allocation_preserves_people_not_only_total(self):
        self.assertEqual([p.adults for p in room_parties(4,[],2)], [2,2])
        rows=[dict(adults=3,children_ages=[]),dict(adults=1,children_ages=[0,17])]
        self.assertEqual([p.persons for p in room_parties(4,[17,0],2,rows)],[3,3])
        for bad in [[],[0,16],[0,17,17]]:
            with self.assertRaises(ValueError):room_parties(4,bad,2,rows)
    def test_invalid_ages_not_coerced_or_dropped(self):
        for ages in [[True],[18],[-1],['5']]:
            with self.assertRaises(ValueError):room_parties(2,ages,1)
        self.assertEqual(ages_from_text('0, 17'),[0,17])
    def test_old_adult_query_contract_and_new_family_roundtrip(self):
        q=OfferQuery('A','B','2090-05-10','2090-05-14',4,2)
        self.assertNotIn('children_ages',q.to_dict());self.assertNotIn('room_assignments',q.to_dict())
        q=OfferQuery('A','B',q.start,q.end,2,2,children_ages=(4,8))
        self.assertEqual(q.persons,4);self.assertEqual(OfferQuery(**q.to_dict()).to_dict(),q.to_dict())
    def test_mixed_occupancy_in_same_type_uses_actual_per_unit_ranges(self):
        room=dict(rid='718',offer='1',quantities=[0,1,2,3],unit_options={i:dict(adults=[1,2],children=[0]) for i in (1,2,3)})
        result=selections([room,dict(room,offer='2')],tuple(RoomParty(n) for n in (2,2,1)))
        self.assertEqual(len(result),2)
        self.assertTrue(all(len(c)==1 and c[0].quantity==3 for c in result))
        room['unit_options'][3]['adults']=[2]
        self.assertEqual(selections([room],tuple(RoomParty(n) for n in (2,2,1))),[])
    def test_age_category_requires_published_selector_label_and_boundary(self):
        q=OfferQuery('A','B','2090-05-10','2090-05-14',2,1,children_ages=(9,))
        html='<form id="formlook"><label for="kids">Children under 10</label><select id="kids" name="numchild"></select></form>'
        self.assertEqual(child_age_contract(html,q)['maximum'],9)
        for label in ['Kinder','Children under 9','Children under 18 or ask us']:
            with self.assertRaises(ValueError):child_age_contract(html.replace('Children under 10',label),q)
        self.assertIsNone(ChildAgeRange.parse('Children under 10 optional'))
    def test_tariff_conditions_negations_and_time_are_not_guarantees(self):
        facts,_=room_facts('kein eigenes Bad','Frühstück nicht enthalten; nicht erstattungsfähig','2090-05-10')
        self.assertEqual(facts,{'Eigenes Bad':False,'Frühstück':False,'Kostenlose Stornierung':False})
        facts,_=room_facts('Private bathroom and shared bathroom','Frühstück inklusive, ohne Frühstück','2090-05-10')
        self.assertNotIn('Eigenes Bad',facts);self.assertNotIn('Frühstück',facts)
        facts,_=room_facts('','Kostenlose Stornierung bis 7 Tage vor Anreise','2090-05-10',date(2090,5,2))
        self.assertTrue(facts['Kostenlose Stornierung'])
        facts,_=room_facts('','Kostenlose Stornierung bis 7 Tage vor Anreise','2090-05-10',date(2090,5,3))
        self.assertNotIn('Kostenlose Stornierung',facts)
        facts,_=room_facts('','Kostenlose Stornierung optional gegen Aufpreis','2090-05-10')
        self.assertNotIn('Kostenlose Stornierung',facts)
    def test_same_room_type_split_quote_matches_each_actual_party(self):
        q=OfferQuery('A','B','2090-05-10','2090-05-14',3,2)
        html=fixture(q,{'718':(1,2),'729':(1,1)}).replace('729','718')
        choice=(Beds24RoomSelection('718','1',(RoomParty(2),RoomParty(1))),)
        offer=Responsive.parse(html,q,item(),choice,timestamp(),'https://beds24.com/',{'propid':'876543'})
        self.assertEqual(offer.eur_amount,'225.00')
        self.assertEqual([r['adults_per_unit'] for r in offer.details['selected_rooms']],[2,1])
    def test_children_quote_needs_source_age_contract_and_visible_icons(self):
        q=OfferQuery('A','B','2090-05-10','2090-05-14',2,1,children_ages=(5,))
        html=fixture(q,{'718':(1,2)}).replace('nc1-718-1" value="0"','nc1-718-1" value="1"').replace('<span id="x1drprice">','<span class="occupancychild"></span><span id="x1drprice">')
        choice=(Beds24RoomSelection('718','1',q.room_assignments),)
        with self.assertRaises(ValueError):Responsive.parse(html,q,item(),choice,timestamp(),'https://beds24.com/',{'propid':'876543'})
        source=dict(rid='718',offer='1',age_contract=ChildAgeRange.parse('Children under 10').to_dict(),room_evidence=dict(facts={},proof={}))
        offer=Responsive.parse(html,q,item(),choice,timestamp(),'https://beds24.com/',{'propid':'876543'},[source])
        self.assertEqual(offer.details['capacity'],3)
        with self.assertRaises(ValueError):Responsive.parse(html.replace('occupancychild','other'),q,item(),choice,timestamp(),'https://beds24.com/',{'propid':'876543'},[source])

class SourceSafetyTests(unittest.TestCase):
    def test_qualifications_outside_short_clause_cannot_confirm_hard_fact(self):
        facts,_=room_facts('Private bathroom. Not in every room.','Free cancellation until 7 days before arrival. Except weekends.','2090-05-10')
        self.assertNotIn('Eigenes Bad',facts);self.assertNotIn('Kostenlose Stornierung',facts)
    def test_missing_third_room_and_cancel_are_open_not_availability(self):
        room=dict(rid='random',offer='1',quantities=[0,1,2],unit_options={i:dict(adults=[1,2],children=[0]) for i in (1,2)})
        self.assertEqual(selections([room],tuple(RoomParty(n) for n in (2,2,1))),[])
        def cancel():raise InterruptedError('cancelled')
        with self.assertRaises(InterruptedError):selections([room],(RoomParty(2),),check=cancel)
    def test_adult_only_provider_is_not_called_for_family(self):
        from src.vacation_planner.core.planning.OfferResearchService import OfferResearchService
        from src.vacation_planner.core.planning.SearchContext import SearchContext
        from tests.unit.test_surprise_planning import fixture_trip
        trip=fixture_trip();trip['request']['children_ages']=[6]
        class AdultsOnly:
            name='No age contract';category='lodging'
            def search(self,*args):raise AssertionError('Must not send adult-only query')
        result=OfferResearchService([AdultsOnly()]).research(trip,SearchContext(),categories=['lodging'])
        self.assertEqual(result['offer_searches']['lodging']['status'],'unsupported')
    def test_pdf_group_and_divisor_include_children_without_inventing_tariffs(self):
        from src.vacation_planner.infrastructure.planning.PdfTripPresenter import PdfTripPresenter
        from tests.unit.test_surprise_planning import fixture_trip
        trip=fixture_trip();trip['request']['adults']=2;trip['request']['children_ages']=[5,8]
        trip['cost_summary'].update(coverage=1,low='400',high='400',missing=[])
        model=PdfTripPresenter.present(trip)
        self.assertIn('2 Kinder',model['group_label']);self.assertIn('100',model['cost']['per_person'])
    def test_unknown_age_evidence_cannot_pass_price_quality(self):
        from src.vacation_planner.core.planning.OfferQuality import assess
        q=OfferQuery('A','B','2090-05-10','2090-05-14',2,1,children_ages=(6,))
        adult=OfferQuery('A','B',q.start,q.end,2,1)
        offer=Responsive.parse(fixture(adult,{'718':(1,2)}),adult,item(),{'718':(1,2)},timestamp(),'https://beds24.com/',{'propid':'876543'}).to_dict()
        offer['parameters']=q.to_dict();offer['details']['capacity']=3
        quality=assess(offer,q,{})
        self.assertFalse(quality['price_eligible']);self.assertEqual(quality['status'],'mismatch')

if __name__=='__main__':unittest.main()
