"""Responsive source contract, synthetic identities; real prices are not fixtures."""
import copy
import json
import unittest
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from urllib.parse import parse_qs,urlsplit
from tests.unit.test_general_lodging import item
from src.vacation_planner.infrastructure.planning.Beds24ResponsiveQuote import Beds24ResponsiveQuote as Responsive
from src.vacation_planner.infrastructure.planning.Beds24OfferAdapter import Beds24OfferAdapter
from src.vacation_planner.infrastructure.planning.LodgingSourcePolicy import LodgingSourcePolicy
from src.vacation_planner.infrastructure.planning.LodgingWebsite import operator_links,availability_form,extract_links,matches_identity
from src.vacation_planner.infrastructure.planning.TripStore import timestamp,TripStore
from src.vacation_planner.core.planning.TravelOffers import OfferQuery
from src.vacation_planner.core.planning.SearchContext import SearchContext
from src.vacation_planner.core.planning.OfferResearchService import OfferResearchService
from src.vacation_planner.infrastructure.planning.LodgingOfferProvider import LodgingOfferProvider
from src.vacation_planner.infrastructure.planning.LodgingDirectory import LodgingDirectory
from tests.unit.test_surprise_planning import fixture_trip
import tests.unit.test_source_research as wire_fixture


def fixture(q,choice,fee=25):
    rows='';total=fee
    for index,(rid,(qty,adults)) in enumerate(choice.items(),1):
        total+=100*qty
        rows+=f'''<input name="na1-{rid}-{index}" value="{adults}"><input name="nc1-{rid}-{index}" value="0">
        <input name="sr1-{rid}-{index}" value="{qty}"><input id="x{index}roomprice" value="100">
        <div class="at_roomnametext">Room {rid}</div>{'<span class="occupancyadult"></span>'*adults}
        <span id="x{index}drprice">{100*qty},00</span><span class="bookingpagecurrency2">€</span>'''
    if fee:rows+=f'<div id="zupsellrow9"><span class="b24-upsellname">Cleaning</span><span id="x9dispprice">{fee},00</span></div><input id="x9oblig" value="{fee}">'
    nights=(__import__('datetime').date.fromisoformat(q.end)-__import__('datetime').date.fromisoformat(q.start)).days
    return f'''<h1>Independent House 1</h1><form id="formbook" method="post"><input name="propid" value="876543"><input name="page" value="book">
    <input name="firstnight" value="{q.start}"><input name="checkout" value="{q.end}"><input name="numnight" value="{nights}">
    <div class="b24-bookingdetails"><div class="panel-body">{rows}<span id="totaldispprice">{total},00</span></div></div>
    <input name="subtotalprice" value="{total},00"><input name="guestname"><input name="bookbook" value="Pay"></form>'''


def inventory(q):
    start=__import__('datetime').date.fromisoformat(q.start);end=__import__('datetime').date.fromisoformat(q.end)
    return f'''<h1>Independent House 1</h1><script>var checkindefault = new Date({start.year},{start.month-1},{start.day},0,0,0);
    var checkoutdefault = new Date({end.year},{end.month-1},{end.day},0,0,0);</script>
    <form id="formlook" method="GET"><input name="page" value="book3"><button name="bookmult">Select</button>
    <select name="sr1-718"><option value="0">0</option><option value="1">1</option><option value="2">2</option></select>
    <select name="naa1-1-718"><option value="1">1</option><option value="2">2</option></select>
    <select name="naa2-1-718"><option value="1">1</option><option value="2">2</option></select></form>'''


class ResponsiveTests(unittest.TestCase):
    def setUp(self):
        self.q=OfferQuery('Berlin','Town','2090-05-10','2090-05-14',4,2);self.choice={'718':(2,2)}
        self.html=fixture(self.q,self.choice);self.ids={'propid':'876543'}
    def parse(self,h=None):return Responsive.parse(h or self.html,self.q,item(),self.choice,timestamp(),'https://beds24.com/booking2.php?propid=876543',self.ids)
    def test_group_stay_and_surcharge_are_independently_reconciled(self):
        o=self.parse();self.assertEqual(o.eur_amount,'225.00');self.assertEqual(o.details['units'],2)
        self.assertFalse(o.evidence['fees_complete']);self.assertTrue(o.unresolved)
        self.assertEqual(o.details['included_surcharges'][0]['amount'],'25.00')
    def test_two_distinct_types_and_uneven_occupancy(self):
        q=OfferQuery('Berlin','Town',self.q.start,self.q.end,3,2);choice={'718':(1,2),'729':(1,1)}
        o=Responsive.parse(fixture(q,choice),q,item(),choice,timestamp(),'https://beds24.com/',self.ids)
        self.assertEqual(o.eur_amount,'225.00');self.assertEqual(len(o.details['selected_rooms']),2)
    def test_wrong_dates_property_name_quantity_and_children_rejected(self):
        for before,after in [('2090-05-10','2090-05-11'),('876543','876544'),('Independent House 1','Independent House 2'),('value="2"','value="1"'),('nc1-718-1" value="0"','nc1-718-1" value="1"')]:
            with self.subTest(before=before),self.assertRaises(ValueError):self.parse(self.html.replace(before,after))
    def test_sold_zero_missing_price_or_visible_occupancy_rejected(self):
        for h in [self.html.replace('id="x1roomprice" value="100"','id="x1roomprice" value="0"'),self.html.replace('id="x1drprice"','id="not-price"'),self.html.replace('class="occupancyadult"','class="not-adult"')]:
            with self.assertRaises(ValueError):self.parse(h)
    def test_mandatory_fee_total_currency_and_night_price_mismatch_rejected(self):
        for h in [self.html.replace('id="x9oblig" value="25"','id="x9oblig" value="0"'),self.html.replace('225,00','200,00'),self.html.replace('€','USD'),self.html.replace('200,00','100,00')]:
            with self.assertRaises(ValueError):self.parse(h)
    def test_duplicate_parameter_extra_room_and_missing_full_group_rejected(self):
        for h in [self.html.replace('<input name="propid"', '<input name="propid" value="876543"><input name="propid"'),self.html.replace('sr1-718-1','sr1-999-1'),self.html.replace('sr1-718-1" value="2"','sr1-718-1" value="1"')]:
            with self.assertRaises(ValueError):self.parse(h)
    def test_source_selector_contract_and_safe_selection_only(self):
        rooms,fields,multi=Responsive.inventory(inventory(self.q),self.q)
        choice=Beds24OfferAdapter.combinations(rooms,self.q.occupancy)[0]
        self.assertEqual(choice,self.choice)
        p=LodgingSourcePolicy('https://beds24.com/booking2.php?propid=876543',item())
        params=dict(propid='876543',checkin=self.q.start,numnight='4',numadult='4',numchild='0',multiroom='1',lang='de')
        selected=Responsive.parameters(params,rooms,fields,multi,choice)
        url=p.responsive_query(p.seed,selected,fields,multi);self.assertIn('bookmult=',url)
        for bad in [dict(selected,page='book'),dict(selected,guestname='x'),dict(selected,propid='999')]:
            with self.assertRaises(ValueError):p.responsive_query(p.seed,bad,fields,multi)
        with self.assertRaises(ValueError):p.validate_url(url+'&bookbook=Pay')
    def test_wrong_source_date_and_no_multiroom_does_not_claim_sold_out(self):
        with self.assertRaises(ValueError):Responsive.inventory(inventory(self.q).replace('2090,4,10','2090,4,11'),self.q)
        with self.assertRaisesRegex(ValueError,'keine Mehrzimmerauswahl'):Responsive.inventory(inventory(self.q).replace('name="bookmult"','name="other"'),self.q)
    def test_operator_grant_requires_actual_backend_anchor_and_public_transport(self):
        p=LodgingSourcePolicy('https://beds24.com/booking2.php?propid=876543',item())
        html='<a href="https://operator.example/">Official</a><script>fetch("https://evil.example/")</script>'
        self.assertEqual(operator_links(html,p.seed),['https://operator.example/'])
        p.operator_link('https://operator.example/',html,p.seed)
        with self.assertRaises(ValueError):p.operator_link('https://evil.example/',html,p.seed)
        with self.assertRaises(ValueError):p.operator_link('https://127.0.0.1/', '<a href="https://127.0.0.1/">x</a>',p.seed)
        p=LodgingSourcePolicy('https://house.example/',item())
        with self.assertRaises(ValueError):p.operator_link('https://operator.example/',html,p.seed)

    def test_observed_public_search_fields_only_and_room_hints_survive(self):
        form='<form class="acantic-beds24-search-form" method="get">'+''.join('<input name="'+n+'">' for n in ('checkin','checkout','numadult','numchild'))+'</form>'
        p=LodgingSourcePolicy(item()['url'],item());self.assertTrue(availability_form(form))
        url=p.availability_query(p.seed,form,self.q);params=parse_qs(urlsplit(url).query)
        self.assertEqual(params,{'checkin':[self.q.start],'checkout':[self.q.end],'numadult':['2'],'numchild':['0']})
        for h in [form.replace('method="get"','method="post"'),form.replace('</form>','<input name="guestemail"></form>'),form.replace('method="get"','action="https://evil.example/"')]:
            with self.assertRaises(ValueError):p.availability_query(p.seed,h,self.q)
        with self.assertRaises(ValueError):p.availability_query('https://evil.example/',form,self.q)
        links=extract_links('<input data-reservation-url="https://beds24.com/booking2.php?propid=876543&amp;roomid=718&amp;br3-718=Book">',p.seed)
        self.assertEqual(links['booking'],['https://beds24.com/booking2.php?propid=876543&roomid=718'])

    def test_calendars_prune_on_request_and_missing_dates_but_do_not_confirm_price(self):
        q=OfferQuery('Berlin','Town','2090-05-10','2090-05-11',2,1)
        html=inventory(q).replace('<button name="bookmult">Select</button>','<input name="br3-718" value="Book">')
        html=html.replace('</form>','</form><script>$("#ajaxroomoffer3-718").data("avail", {"20900510":"1"});</script>')
        rooms,_,_=Responsive.inventory(html,q);self.assertEqual(rooms[0]['rid'],'718')
        for code in ('0','2'):
            with self.assertRaises(ValueError):Responsive.inventory(html.replace('"20900510":"1"','"20900510":"'+code+'"'),q)
        with self.assertRaises(ValueError):self.parse(self.html.replace('name="page" value="book"','name="page" value="enquire"'))

    def test_http_hint_uses_same_https_host_without_plaintext_fallback(self):
        p=LodgingSourcePolicy('http://house1.example/',item());self.assertEqual(p.seed,'https://house1.example/')
        with self.assertRaises(ValueError):p.validate_url('http://house1.example/')
        with self.assertRaises(ValueError):LodgingSourcePolicy('http://user:secret@house1.example/',item())

    def test_brand_alias_still_requires_independent_location_or_phone(self):
        house=dict(item(),name='H73-Inn Hostel',identity_tags={'phone':'+49 123 456789'})
        self.assertTrue(matches_identity(house,'<h1>H73-Inn Hotel Garni</h1><p>+49 123 456789</p>'))
        self.assertFalse(matches_identity(house,'<h1>H73-Inn Hotel Garni</h1><p>+49 999 999999</p>'))
        links=extract_links('<a href="/contact/">Kontakt</a><a href="http://beds24.com/booking.php?propid=876543">Book</a>',house['url'])
        self.assertEqual(links['identity_pages'],['https://house1.example/contact/'])
        self.assertEqual(links['booking'],['https://beds24.com/booking.php?propid=876543'])

    def test_cancelled_adapter_is_not_swallowed_as_source_error_or_retried(self):
        trip=fixture_trip();trip.pop('lodging_research',None);trip['lodgings']=[item()]
        html='<h1>Independent House 1</h1>12345<a href="https://beds24.com/booking2.php?propid=876543">Book</a><a href="https://beds24.com/booking2.php?propid=876544">Book</a>'
        class Pages:
            def fetch(self,url,*a,**kw):return dict(body=html.encode(),retrieved_at=timestamp(),original_url=url,final_url=url)
        ctx=SearchContext(budget=12)
        def cancelled(*a,**kw):ctx.cancel.set();raise InterruptedError('Cancelled')
        with tempfile.TemporaryDirectory() as t,patch.object(Beds24OfferAdapter,'search',side_effect=cancelled) as search:
            p=LodgingOfferProvider(TripStore(Path(t)/'test.db'),http_factory=lambda _:Pages())
            p.search(OfferQuery.from_trip(trip),trip,ctx)
            e=trip['lodging_research']['entries'][0]
            self.assertEqual(e['state'],'cancelled');self.assertEqual(search.call_count,1)
            self.assertFalse(e.get('rejected_responses'))


class ResponsiveHttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):wire_fixture.ResearchTests.setUpClass()
    @classmethod
    def tearDownClass(cls):wire_fixture.ResearchTests.tearDownClass()
    def test_real_local_http_through_provider_costs_and_explicit_snapshot(self):self.full_http(False)
    def test_real_local_public_search_form_through_quote_and_snapshot(self):self.full_http(True)
    def test_bounded_cold_directory_wire_cache_and_error_are_separate(self):
        f=wire_fixture.ResearchTests('test_real_fixture_http_identity_provenance_and_no_trip_mutation');f.setUp()
        try:
            body=json.dumps({'elements':[{'type':'node','id':876,'lat':46.36,'lon':14.11,'tags':{'name':'Fresh House','tourism':'hotel','website':'https://fresh.example/'}},
                {'type':'node','id':877,'lat':47.36,'lon':14.11,'tags':{'name':'Far House','tourism':'hotel'}}]})
            def factory(store,policy):
                f.http.policy=policy
                for url in policy.urls:
                    p=urlsplit(url);f.routes[p.hostname,p.path+('?' + p.query if p.query else '')]=(404,'text/plain','',{}) if p.path=='/robots.txt' else (200,'application/json',body,{})
                return f.http
            ctx=SearchContext(budget=8);ctx.wait=lambda _:ctx.check()
            request=SimpleNamespace(lodging_radius_km='3',surroundings=True);destination={'latitude':46.36,'longitude':14.11}
            with patch('src.vacation_planner.infrastructure.planning.LodgingDirectory.ResearchHttp',side_effect=factory):
                provider=LodgingDirectory(f.store);first=provider.collect(destination,request,ctx);cached=provider.collect(destination,request,ctx)
                self.assertEqual([x['name'] for x in first['lodgings']],['Fresh House']);self.assertEqual(ctx.calls,2)
                self.assertEqual(first['coverage']['retrieved_at'],cached['coverage']['retrieved_at']);self.assertTrue(cached['cache_used'])
                f.http.memory.clear()
                body=json.dumps({'elements':[],'remark':'runtime timeout'})
                failed=provider.collect({'latitude':46.37,'longitude':14.11},request,ctx)
                self.assertEqual(failed['coverage']['status'],'source_error');self.assertEqual(first['lodgings'][0]['name'],'Fresh House')
        finally:f.tearDown()

    def full_http(self,public_form):
        f=wire_fixture.ResearchTests('test_real_fixture_http_identity_provenance_and_no_trip_mutation');f.setUp()
        try:
            trip=fixture_trip();trip.pop('lodging_research',None);trip['lodgings']=[item()];trip['selected_lodging']=0
            q=OfferQuery.from_trip(trip);base='https://beds24.com/booking2.php?propid=876543'
            h=inventory(q).replace('</form>','''<select name="sr1-729"><option value="0">0</option><option value="1">1</option></select>
                <select name="naa1-1-729"><option value="1">1</option></select></form>''')
            policy=LodgingSourcePolicy(item()['url'],item());policy.booking_link(base)
            from datetime import date
            params=dict(propid='876543',checkin=q.start,numnight=str((date.fromisoformat(q.end)-date.fromisoformat(q.start)).days),numadult=str(q.adults),numchild='0',lang='de',multiroom='1')
            initial=policy.query(base,params);rooms,fields,multi=Responsive.inventory(h,q)
            choice=Beds24OfferAdapter.combinations(rooms,q.occupancy)[0]
            selected=policy.responsive_query(base,Responsive.parameters(params,rooms,fields,multi,choice),fields,multi)
            f.routes['house1.example','/robots.txt']=(404,'text/plain','',{})
            f.routes['beds24.com','/robots.txt']=(404,'text/plain','',{})
            f.routes['house1.example','/']=(200,'text/html','<h1>Independent House 1</h1>12345 <a href="'+base+'">Book</a>',{})
            if public_form:
                f.routes['house1.example','/']=(200,'text/html','<h1>Independent House 1</h1>12345 <a href="/availability/">Book</a>',{})
                form='<form class="acantic-beds24-search-form" method="get">'+''.join('<input name="'+n+'">' for n in ('checkin','checkout','numadult','numchild'))+'</form>'
                source=policy.site_link('https://house1.example/availability/')
                search=policy.availability_query(source,form,q);path=urlsplit(search)
                f.routes['house1.example','/availability/']=(200,'text/html',form,{})
                f.routes['house1.example',path.path+'?'+path.query]=(200,'text/html','<input data-reservation-url="'+base+'">',{})
            for url,body in [(initial,h),(selected,fixture(q,choice))]:
                p=urlsplit(url);f.routes[p.hostname,p.path+'?'+p.query]=(200,'text/html',body,{})
            def factory(policy):f.http.policy=policy;return f.http
            ctx=SearchContext(budget=8);ctx.wait=lambda seconds:ctx.check()
            before=copy.deepcopy(trip)
            result=OfferResearchService([LodgingOfferProvider(f.store,http_factory=factory)]).research(trip,ctx,categories=['lodging'])
            entry=result['lodging_research']['entries'][0]
            self.assertEqual(entry['state'],'partial');self.assertEqual(entry['variant'],Responsive.variant)
            self.assertEqual(entry['offers'][0]['eur_amount'],'325.00');self.assertEqual(ctx.calls,7 if public_form else 5)
            self.assertEqual(entry['selection_responses'],1)
            self.assertEqual(trip,before);self.assertTrue(any(c['low'] is None for c in result['lodgings'][0]['mandatory_costs']))
            saved=f.store.save('Responsive fixture',result);loaded=f.store.load(saved)
            self.assertEqual(loaded['lodging_research']['entries'][0]['offers'][0]['eur_amount'],'325.00')
        finally:f.tearDown()


if __name__=='__main__':unittest.main()
