from __future__ import annotations

from datetime import datetime, timedelta
import unicodedata
from urllib.parse import urlencode

from ...core.planning.TravelOffers import OfferResult, TravelOffer, amount


def normalized(value):
    return ''.join(c for c in unicodedata.normalize('NFKD',value.casefold()) if not unicodedata.combining(c)).strip()


class RegioJetOfferProvider:
    """Read-only public website search; endpoint/fields observed in RegioJet's own JS.

    Searches and route details are non-transactional GETs. No cart, ticket hold,
    login, private key, paid API or reservation call is used.
    """
    name='RegioJet';category='rail'
    BASE='https://brn-ybus-pubapi.sa.cz/restapi'
    HEADERS={'X-Currency':'EUR','X-Lang':'en','Accept':'application/1.2.0+json'}

    def __init__(self,http,store): self.http,self.store=http,store

    def locations(self,context):
        cached=self.store.cache_get('regiojet-locations-v1',7*86400)
        if cached:return cached[0]
        data,stamp=self.http.json(self.BASE+'/consts/locations',context,headers={**self.HEADERS,'Accept':'application/json'})
        if not isinstance(data,list):raise ValueError('Ungültige RegioJet-Ortsantwort')
        self.store.cache_set('regiojet-locations-v1',data,stamp);return data

    @staticmethod
    def city(locations,name):
        wanted=normalized(name.split(',')[0])
        for country in locations:
            for city in country.get('cities',[]):
                names=[city['name']]+city.get('aliases',[])
                if any(wanted==normalized(n) for n in names) and 'TRAIN_STATION' in city.get('stationsTypes',[]):return city
        return None

    def search(self,query,trip,context):
        params=query.to_dict();sources=[]
        if query.currency!='EUR' or query.travel_class!='2' or query.discount_cards:
            return OfferResult(self.name,self.category,'unsupported',params,message='Nur Erwachsene, EUR, zweite Klasse ohne Rabattkarten unterstützt.')
        locations=self.locations(context);origin=self.city(locations,query.origin);destination=self.city(locations,query.destination)
        if not origin or not destination:
            return OfferResult(self.name,self.category,'unsupported',params,message='RegioJet bietet für mindestens einen Ort keinen eindeutig zugeordneten Bahnhof. Keine Aussage über andere Bahnunternehmen.')
        directions=[]
        for start,end,day in ((origin,destination,query.start),(destination,origin,query.end)):
            context.check();search={'fromLocationId':start['id'],'fromLocationType':'CITY','toLocationId':end['id'],'toLocationType':'CITY','departureDate':day,'tariffs':['REGULAR']*query.adults}
            url=self.BASE+'/routes/search/simple?'+urlencode(search,doseq=True);sources.append(url)
            response,stamp=self.http.json(url,context,headers=self.HEADERS)
            if not isinstance(response,dict) or not isinstance(response.get('routes'),list):raise ValueError('RegioJet-Suchergebnis fehlt')
            candidates=[r for r in response['routes'] if r.get('bookable') and r.get('vehicleTypes')==['TRAIN'] and r.get('freeSeatsCount',0)>=query.adults
                        and datetime.fromisoformat(r['departureTime']).date().isoformat()==day]
            if not candidates:
                return OfferResult(self.name,self.category,'no_offers',params,message='Keine buchbare reine Zugverbindung für '+day+' zurückgegeben; Buchungshorizont nicht nachgewiesen.',sources=sources)
            # Summary fare is never accepted: inspect actual class, passenger echo and capacity.
            cheapest=sorted(candidates,key=lambda r:(r.get('priceFrom') is None,r.get('priceFrom') or 0))
            def hours(r):
                return (datetime.fromisoformat(r['arrivalTime'])-datetime.fromisoformat(r['departureTime'])).total_seconds()
            shortlist=[]
            for route in [cheapest[0],min(candidates,key=hours)]+cheapest[:2]:
                if route['id'] not in [r['id'] for r in shortlist]:shortlist.append(route)
            found=[]
            for route in shortlist[:3]:
                url=self.BASE+'/routes/'+str(route['id'])+'/simple?'+urlencode({'fromStationId':route['departureStationId'],'toStationId':route['arrivalStationId'],'tariffs':['REGULAR']*query.adults},doseq=True);sources.append(url)
                detail,stamp=self.http.json(url,context,headers={**self.HEADERS,'Accept':'application/json'})
                parsed=self.parse_detail(detail,query.adults,start['id'],end['id'],day)
                if parsed:found.append((parsed,stamp,url))
            if not found:return OfferResult(self.name,self.category,'no_offers',params,message='Keine zweite Klasse mit bestätigter Gruppenbelegung in den geprüften Verbindungen.',sources=sources)
            directions.append(found)
        combinations=[(out,back) for out in directions[0] for back in directions[1]]
        cheap=min(combinations,key=lambda pair:sum(amount(x[0]['price']) for x in pair))
        fast=min(combinations,key=lambda pair:(sum(x[0]['duration_hours'] for x in pair),sum(amount(x[0]['price']) for x in pair)))
        selected=[cheap]
        if tuple(x[0]['id'] for x in fast)!=tuple(x[0]['id'] for x in cheap):selected.append(fast)
        url='https://regiojet.com/?'+urlencode({'fromLocationId':origin['id'],'fromLocationType':'CITY','toLocationId':destination['id'],'toLocationType':'CITY','departureDate':query.start,'returnDepartureDate':query.end,'tariffs':['REGULAR']*query.adults},doseq=True)
        offers=[]
        for index,pair in enumerate(selected):
            legs=[d[0] for d in pair];total=sum((amount(x['price']) for x in legs),amount('0'))
            stamp=pair[-1][1];valid_until=(min(datetime.fromisoformat(x[1]) for x in pair)+timedelta(minutes=10)).isoformat(timespec='seconds')
            offer=TravelOffer(self.name,self.category,'rj:'+':'.join(str(x['id']) for x in legs)+':'+str(query.adults),url,stamp,params,str(total),'EUR','group_roundtrip',str(total),valid_until=valid_until,
                          included=['Hin- und Rückfahrt für alle angefragten Erwachsenen','Zweite Klasse, keine Rabattkarten','Sitzplatzreservierung laut Verbindungsabschnitten'],
                          unresolved=['Zubringer und Unterkunftstransfers nicht enthalten'],
                          details={'legs':legs,'travel_class':'2','tariffs':['REGULAR']*query.adults,'independent_tickets':True,'comparison_role':'günstig unter geprüften Verbindungen' if index==0 else 'schnell unter geprüften Verbindungen'},
                          evidence={'sources':sources,'price_field':'priceClasses.price','passenger_echo':'priceClasses.tariffs','capacity_field':'priceClasses.freeSeatsCount','currency_request':'X-Currency: EUR','normalization':'Summe zweier direkt abgefragter Gruppentarife; keine Personenmultiplikation'})
            offers.append(offer)
        return OfferResult(self.name,self.category,'found',params,offers,'Datierte Gruppentarife; getrennte Hin- und Rückfahrkarten. Begrenzte günstige/schnelle Auswahl; kein Marktminimum.',sources=sources)

    @staticmethod
    def parse_detail(detail,adults,from_id,to_id,day):
        if detail.get('vehicleTypes')!=['TRAIN'] or not detail.get('bookable'):return None
        if detail.get('departureCityId')!=from_id or detail.get('arrivalCityId')!=to_id:raise ValueError('RegioJet hat andere Orte übernommen')
        if datetime.fromisoformat(detail['departureTime']).date().isoformat()!=day:raise ValueError('RegioJet hat ein anderes Datum übernommen')
        classes=[c for c in detail.get('priceClasses',[]) if c.get('seatClassKey') in ('C0','TRAIN_STANDARD_PL','TRAIN_LOW_COST','TRAIN_2ND_CLASS') and c.get('bookable')
                 and c.get('tariffs')==['REGULAR']*adults and c.get('freeSeatsCount',0)>=adults and c.get('price') is not None]
        if not classes:return None
        fare=min(classes,key=lambda x:amount(x['price']))
        sections=detail.get('sections') or []
        if not sections or any(s.get('vehicleType')!='TRAIN' for s in sections):return None
        return {'id':detail['id'],'departure':detail['departureTime'],'arrival':detail['arrivalTime'],
                'from':detail.get('departureCityName','')+' '+detail.get('departureStationName',''),
                'to':detail.get('arrivalCityName','')+' '+detail.get('arrivalStationName',''),
                'from_station_id':detail['departureStationId'],'to_station_id':detail['arrivalStationId'],
                'price':str(amount(fare['price'])),'seat_class':fare['seatClassKey'],
                'conditions':fare.get('conditions',{}),'transfers':len(sections)-1,
                'duration_hours':(datetime.fromisoformat(detail['arrivalTime'])-datetime.fromisoformat(detail['departureTime'])).total_seconds()/3600,
                'sections':[{k:s.get(k) for k in ('departureTime','arrivalTime','departureCityName','arrivalCityName','departureStationName','arrivalStationName','fixedSeatReservation','line')} for s in sections]}
