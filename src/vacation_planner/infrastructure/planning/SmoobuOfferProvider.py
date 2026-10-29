from __future__ import annotations

from datetime import date, datetime, timedelta
from urllib.parse import parse_qs, urlencode, urljoin, urlsplit

from ...core.planning.TravelOffers import OfferResult, TravelOffer, amount
from .RegioJetOfferProvider import normalized


class SmoobuOfferProvider:
    """Public read-only guest search, observed in the accommodation's own widget.

    This is not the paid Smoobu host API. Only checkAvailability GETs are used.
    Returned bookUrl parameters and property IDs must match the checked request.
    Inventory from unrelated towns, even when returned by the server, is rejected.
    """
    name='Smoobu · direkte Unterkunft';category='lodging'
    # IDs come from the official apartment provider's embedded public booking widget.
    SOURCES=[{'destination':'Innsbruck','owner':'Apartments Innsbruck / Perfect Lodgings',
              'source':'https://www.apartments-innsbruck.com/en/buchen/',
              'widget':'https://booking.smoobu.com/perfect-lodgings', 'user_id':71379,
              'property_ids':(577977,577989,577980,577974,577986,577983,1659658),
              'identity_prefix':'Innstrasse 40','address':'Innstraße 40, Innsbruck, Österreich'}]

    def __init__(self,http):self.http=http

    def search(self,query,trip,context):
        params=query.to_dict()
        if query.currency!='EUR':return OfferResult(self.name,self.category,'unsupported',params,message='Dieser geprüfte Zugang übernimmt ausschließlich direkt belegte EUR-Angebote.')
        source=next((s for s in self.SOURCES if normalized(s['destination'])==normalized(query.destination)),None)
        if not source:return OfferResult(self.name,self.category,'unsupported',params,message='Für diesen Ort ist noch keine geprüfte direkte Buchungsstrecke integriert.')
        if 'Ferienwohnung' not in query.accommodation_types:
            return OfferResult(self.name,self.category,'unsupported',params,message='Dieser Direktanbieter liefert Ferienwohnungen; angefragte Unterkunftsarten werden beachtet.')
        if query.rooms!=1:
            return OfferResult(self.name,self.category,'unsupported',params,message='Die geprüfte Buchungsstrecke bestätigt jeweils eine Ferienwohnung. Ein Preis für mehrere Zimmer wird nicht daraus hochgerechnet.')
        request={'theme':'booking-tool','arrivalDate':date.fromisoformat(query.start).strftime('%d.%m.%y'),
                 'departureDate':date.fromisoformat(query.end).strftime('%d.%m.%y'),
                 'userId':source['user_id'],'guests':query.adults,'adults':query.adults,'children':0}
        url=source['widget']+'/checkAvailability?'+urlencode(request)
        response,stamp=self.http.json(url,context)
        offers=self.parse_response(response,query,source,stamp,url)
        return OfferResult(self.name,self.category,'found' if offers else 'no_offers',params,offers,
                           f'{len(offers)} passend zugeordnete Ferienwohnungen mit datiertem Aufenthaltspreis.' if offers else 'Keine passenden verfügbaren Wohnungen in der geprüften Antwort; kein Nachweis eines Buchungshorizonts.',sources=[source['source'],url])

    @staticmethod
    def parse_response(response,query,source,stamp,url):
        if not isinstance(response,dict) or response.get('success') is not True:raise ValueError('Smoobu hat die Verfügbarkeitsprüfung nicht erfolgreich beantwortet')
        data=response.get('data') or {};apartments=data.get('apartments');availability=data.get('availabilityResponse') or {}
        if not isinstance(apartments,list) or not isinstance(availability.get('availableApartments'),list):raise ValueError('Verfügbarkeitsdaten fehlen')
        offers=[];nights=(date.fromisoformat(query.end)-date.fromisoformat(query.start)).days
        for item in apartments:
            identity=item.get('id')
            if identity not in source['property_ids'] or identity not in availability['availableApartments']:continue
            if not normalized(item.get('name','')).startswith(normalized(source['identity_prefix'])):raise ValueError('Unterkunftsname oder Adresse passen nicht zur geprüften Identität')
            if item.get('persons',0)<query.adults or item.get('numberOfNights')!=nights:continue
            book_url=urljoin(source['widget'],item.get('bookUrl',''));parsed=urlsplit(book_url)
            expected=urlsplit(source['widget'])
            if parsed.scheme!='https' or parsed.netloc!=expected.netloc or parsed.path!=expected.path:raise ValueError('Unerwarteter Unterkunftslink')
            echo=parse_qs(parsed.query)
            wanted={'apartmentId':str(identity),'arrivalDate':date.fromisoformat(query.start).strftime('%d/%m/%Y'),
                    'departureDate':date.fromisoformat(query.end).strftime('%d/%m/%Y'),'adults':str(query.adults),'children':'0'}
            if any(echo.get(k)!=[v] for k,v in wanted.items()):raise ValueError('Buchungsstrecke hat abweichende Reiseparameter übernommen')
            pricing=(availability.get('prices') or {}).get(str(identity)) or {}
            elements=pricing.get('priceElements') or []
            if not elements or any(e.get('currencyCode')!='EUR' for e in elements):continue
            total=amount(pricing['price'])
            if total!=amount(item['amount']) or total!=sum((amount(e['amount'],allow_negative=True) for e in elements),amount(0)):
                raise ValueError('Gesamtpreis und Preisbestandteile widersprechen sich')
            included=[e.get('name',e.get('type','Preisbestandteil'))+': '+str(amount(e['amount'],allow_negative=True))+' EUR' for e in elements]
            price_property={'id':'smoobu:'+str(identity),'name':item['name'],'address':source['address'],'type':'Ferienwohnung',
                            'source':source['source'],'url':book_url,'capacity':item['persons'],
                            'amenities':{'Küche':True} if any(a.get('name')=='Küche' for a in item.get('amenities',[])) else {}}
            offers.append(TravelOffer(source['owner'], 'lodging', 'smoobu:'+str(identity)+':'+query.start+':'+query.end+':'+str(query.adults),
                                      book_url,stamp,query.to_dict(),str(total),'EUR','group_stay',str(total),
                                      valid_until=(datetime.fromisoformat(stamp)+timedelta(minutes=10)).isoformat(timespec='seconds'),
                                      included=included,details={'property':price_property,'units':1,'nights':nights,'capacity':item['persons'],
                                      'board':'Nicht als enthalten ausgewiesen','cancellation':'In der Angebotsantwort nicht ausgewiesen; vor Buchung prüfen',
                                      'payment':'In der Angebotsantwort nicht ausgewiesen; vor Buchung prüfen'},
                                      evidence={'sources':[source['source'],url],'price_field':'availabilityResponse.prices.price',
                                      'components':elements,'parameter_echo':wanted,'availability_field':'availabilityResponse.availableApartments',
                                      'normalization':'Direkter Gesamtbetrag für eine Ferienwohnung, alle angefragten Erwachsenen und gesamten Aufenthalt; inklusive ausgewiesener Pflichtbestandteile'}))
        return sorted(offers,key=lambda x:amount(x.eur_amount))
