from __future__ import annotations

import copy
from datetime import datetime

from .CostItem import CostItem
from .RankingService import RankingService
from .TravelOffers import OfferQuery, OfferResult, STATUS_LABELS, expire_offers


class OfferResearchService:
    """Independent providers; commit each successful category to an isolated snapshot."""
    def __init__(self,providers):self.providers=list(providers)

    def research_samples(self,trip,context,emit=lambda *args:None,categories=None):
        result=copy.deepcopy(trip);samples=[]
        for start,end in list(dict.fromkeys(tuple(x) for x in trip.get('date_options',[(trip['start'],trip['end'])])))[:3]:
            try:context.check()
            except InterruptedError:break
            candidate=copy.deepcopy(trip)
            candidate.update(start=start,end=end,nights=(datetime.fromisoformat(end)-datetime.fromisoformat(start)).days,offer_searches={})
            candidate.pop('offer_date_samples',None)
            # A different date may not inherit any earlier dated offer's price.
            for lodging in candidate.get('lodgings',[]):
                if lodging.pop('offer_id',None) or (start,end)!=(trip['start'],trip['end']):
                    lodging.pop('offer',None);lodging['price']=CostItem('Unterkunft für Gruppe und Aufenthalt').to_dict();lodging.pop('mandatory_costs',None)
            for option in candidate.get('transports',[]):
                if option.pop('offer_id',None) or ((start,end)!=(trip['start'],trip['end']) and option['mode'] in ('Zug','Flug')):
                    option.pop('offer',None);option['costs']=[CostItem(option['mode']+' für gesamte Gruppe hin und zurück').to_dict()];option['hours_low']=option['hours_high']=None
            def sample_emit(kind,value):
                if kind!='offer_partial':emit(kind,value)
            checked=self.research(candidate,context,sample_emit,categories)
            samples.append({'start':start,'end':end,'offer_searches':checked.get('offer_searches',{}),'cost_summary':checked['cost_summary']})
            if any(r['status']=='cancelled' for r in checked.get('offer_searches',{}).values()):break
        result['offer_date_samples']=samples
        return result

    def research(self,trip,context,emit=lambda *args:None,categories=None):
        result=copy.deepcopy(trip);query=OfferQuery.from_trip(result)
        searches=result.setdefault('offer_searches',{})
        for provider in self.providers:
            category=provider.category
            if categories and category not in categories:continue
            if category in getattr(context,'skipped_categories',set()) or (not categories and category in result.get('skipped_offer_categories',[])):
                emit('phase',provider.name+': auf Nutzerwunsch übersprungen');continue
            emit('phase',f'Preisprüfung {query.destination}: {provider.name} · {query.start} bis {query.end} · {query.adults} Erwachsene')
            previous=searches.get(category)
            try:
                context.check()
                response=provider.search(query,result,context).to_dict()
                if response['parameters']!=query.to_dict():raise ValueError('Anbieterantwort gehört zu anderen Reiseparametern')
                for offer in response['offers']:
                    if offer['parameters']!=query.to_dict():raise ValueError('Angebot gehört zu anderen Reiseparametern')
            except InterruptedError as exc:
                response=OfferResult(provider.name,category,'cancelled',query.to_dict(),message=str(exc)).to_dict()
                self._remember_previous(response,previous);searches[category]=response
                emit('warning',provider.name+': '+str(exc));break
            except (OSError,ValueError,KeyError,TypeError) as exc:
                blocked=any(code in str(exc) for code in ('HTTP 401','HTTP 403','HTTP 406','HTTP 429'))
                response=OfferResult(provider.name,category,'blocked' if blocked else 'error',query.to_dict(),message=str(exc)).to_dict()
            self._remember_previous(response,previous)
            searches[category]=response
            for offer in response['offers']:
                if offer.get('eur_amount') is None or offer.get('price_status')!='aktuell abgerufen':continue
                if category=='rail':self._apply_transport(result,offer,'Zug')
                elif category=='flight':self._apply_transport(result,offer,'Flug')
                elif category=='lodging':self._apply_lodging(result,offer)
                elif category=='activities':
                    from .ActivityPrices import apply_activity_price
                    apply_activity_price(result,offer)
            self._invalidate_unavailable(result,category,response)
            expire_offers(result);RankingService.recompute(result)
            emit('offer_partial',copy.deepcopy(result))
            emit('phase',provider.name+': '+STATUS_LABELS[response['status']]+(' · '+response['message'] if response['message'] else ''))
        expire_offers(result);RankingService.recompute(result)
        return result

    @staticmethod
    def _remember_previous(response,previous):
        if previous and (previous.get('offers') or previous.get('previous_offers')):
            response['previous_offers']=(previous.get('offers') or previous['previous_offers'])[:8]

    @staticmethod
    def _invalidate_unavailable(trip,category,response):
        # A failed refresh never deletes history or changes the user's chosen index.
        confirmed={o['identifier'] for o in response.get('offers',[])}
        collection=trip.get('lodgings',[]) if category=='lodging' else [x for x in trip.get('transports',[]) if x['mode']=={'rail':'Zug','flight':'Flug'}.get(category)]
        for item in collection:
            if not item.get('offer_id'):continue
            if item['offer_id'] in confirmed:continue
            item['offer_refresh_status']=response['status']
            if response['status'] in ('no_offers','found'):
                for cost in [item.get('price',{})]+item.get('costs',[]):
                    if cost.get('low') is not None:cost['status']='veraltet'
                item['booking_status']='Gewähltes Angebot in der neuen Prüfung nicht bestätigt; Alternativen prüfen'
                item['status']=item['booking_status']

    @staticmethod
    def _cost(offer,label):
        return CostItem(label,offer['eur_amount'],offer['eur_amount'],'aktuell abgerufen',offer['source'],offer['retrieved_at'],
                        f"{offer['parameters']['adults']} Erwachsene · {offer['parameters']['start']} bis {offer['parameters']['end']}",
                        offer.get('evidence',{}).get('normalization','Direkter Gesamtpreis des Angebots')).to_dict()

    @classmethod
    def _apply_transport(cls,trip,offer,mode):
        if offer['price_basis']!='group_roundtrip':return
        indices=[i for i,x in enumerate(trip.get('transports',[])) if x['mode']==mode]
        if not indices:
            # Comparison alternative only: keep request modes and selected index intact.
            trip.setdefault('transports',[]).append({'mode':mode,'comparison_only':True})
            indices=[len(trip['transports'])-1]
        matching=next((trip['transports'][i] for i in indices if trip['transports'][i].get('offer_id')==offer['identifier']),None)
        empty=next((trip['transports'][i] for i in indices if not trip['transports'][i].get('offer_id')),None)
        option=matching if matching is not None else empty
        if option is None:
            option={'mode':mode};trip['transports'].append(option)
        option.pop('offer_refresh_status',None)
        legs=offer.get('details',{}).get('legs',[])
        hours=[leg.get('duration_hours') for leg in legs if leg.get('duration_hours') is not None]
        option.update(offer_id=offer['identifier'],offer=offer,status='Angebot zum Abrufzeitpunkt · '+offer['provider'],
                      scope=f"{offer['parameters']['adults']} Erwachsene, Hin- und Rückreise",notes=list(offer.get('included',[])),
                      links=[{'label':offer['provider']+' · passende Verbindungssuche','url':offer['source'],'kind':'Geprüfte Angebotsquelle'}],
                      costs=[cls._cost(offer,mode+' für gesamte Gruppe hin und zurück')],
                      hours_low=min(hours) if len(hours)==2 else None,hours_high=max(hours) if len(hours)==2 else None,
                      connections=legs,retrieved_at=offer['retrieved_at'],filter_status='belegt')
        for label in offer.get('unresolved',[]):
            option['costs'].append(CostItem(label).to_dict())
        limit=trip['request'].get('max_hours')
        if limit and option['hours_high'] is not None and option['hours_high']>float(limit):option['filter_status']='überschritten';option['notes'].append('Gewähltes Angebot überschreitet die gewünschte Reisezeit.')

    @classmethod
    def _apply_lodging(cls,trip,offer):
        if offer['price_basis']!='group_stay':return
        property_data=offer.get('details',{}).get('property') or {}
        identity=property_data.get('id')
        matches=[x for x in trip.get('lodgings',[]) if x.get('id')==identity] if identity else []
        if not matches:
            if not identity or not property_data.get('address') or not property_data.get('source'):return
            request=trip['request']
            if request.get('max_center_km') or any(property_data.get('amenities',{}).get(k) is not True for k in request.get('required',[])):return
            item=dict(property_data,latitude=None,longitude=None,distance_km=None,rooms=1,price={},
                      link_kind='Geprüfte direkte Buchungsstrecke',search_url=offer['source'],open_criteria=[],
                      data_status='Identität und Standort aus direkter Anbieter-Buchungsstrecke',source_updated='Direkte Angebotsantwort')
            trip.setdefault('lodgings',[]).append(item);matches=[item]
        item=matches[0];item.pop('offer_refresh_status',None)
        offers=item.setdefault('offers',[])
        offers[:]=[x for x in offers if x.get('identifier')!=offer['identifier']]+[copy.deepcopy(offer)]
        offers[:]=offers[-8:]
        item.update(offer_id=offer['identifier'],offer=offer,price=cls._cost(offer,'Unterkunft für Gruppe und Aufenthalt'),
                                   occupancy_status='Angefragte Zimmerbelegung im Angebot bestätigt',
                                   booking_status='Zum Abrufzeitpunkt angeboten; keine Reservierung',retrieved_at=offer['retrieved_at'])
        item['price']['scope']=f"{offer['parameters']['adults']} Erwachsene / {offer['parameters']['rooms']} Zimmer / {trip['nights']} Nächte"
        item['mandatory_costs']=[CostItem(fee['label'],fee.get('eur_amount'),fee.get('eur_amount'),'aktuell abgerufen' if fee.get('eur_amount') is not None else 'unbekannt',offer['source'],offer['retrieved_at']).to_dict() for fee in offer.get('additional_fees',[])]
        item['mandatory_costs'] += [CostItem(label).to_dict() for label in offer.get('unresolved',[])]
