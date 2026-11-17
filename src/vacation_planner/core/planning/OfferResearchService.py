from __future__ import annotations

import copy
import time
from datetime import datetime

from .CostItem import CostItem
from .RankingService import RankingService
from .TravelOffers import OfferQuery, OfferResult, STATUS_LABELS, expire_offers


class OfferResearchService:
    """Independent providers; commit each successful category to an isolated snapshot."""
    def __init__(self,providers,analysis=None):self.providers=list(providers);self.analysis=analysis

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
        result=copy.deepcopy(trip);result.pop('offer_analysis',None);query=OfferQuery.from_trip(result)
        searches=result.setdefault('offer_searches',{})
        previous_searches=copy.deepcopy(searches);collected={}
        for provider in self.providers:
            category=provider.category
            if categories and category not in categories:continue
            if category in getattr(context,'skipped_categories',set()) or (not categories and category in result.get('skipped_offer_categories',[])):
                emit('phase',provider.name+': auf Nutzerwunsch übersprungen');continue
            emit('phase',f'Preisprüfung {query.destination}: {provider.name} · {query.start} bis {query.end} · {query.group_label}')
            previous=previous_searches.get(category)
            try:
                context.check()
                if query.children_ages and not getattr(provider,'supports_child_ages',False):
                    response=OfferResult(provider.name,category,'unsupported',query.to_dict(),message='Kinderalter für diese Quelle noch nicht unabhängig prüfbar; keine Ersatzanfrage nur für Erwachsene.').to_dict()
                else:response=provider.search(query,result,context).to_dict()
                if response['parameters']!=query.to_dict():raise ValueError('Anbieterantwort gehört zu anderen Reiseparametern')
                for offer in response['offers']:
                    if offer['parameters']!=query.to_dict():raise ValueError('Angebot gehört zu anderen Reiseparametern')
            except InterruptedError as exc:
                response=OfferResult(provider.name,category,'cancelled',query.to_dict(),message=str(exc)).to_dict()
                self._remember_previous(response,previous)
                collected.setdefault(category,[]).append(response);searches[category]=self._aggregate(collected[category])
                emit('warning',provider.name+': '+str(exc));break
            except (OSError,ValueError,KeyError,TypeError) as exc:
                blocked=any(code in str(exc) for code in ('HTTP 401','HTTP 403','HTTP 406','HTTP 429','Robots','Sperrantwort'))
                response=OfferResult(provider.name,category,'blocked' if blocked else 'error',query.to_dict(),message=str(exc)).to_dict()
                response['retryable']=isinstance(exc,OSError) and not blocked
            if result['request'].get('ai_offer_analysis') and response['status']=='error' and response.get('retryable') and context.deadline-time.monotonic()>1 and getattr(context,'offer_rechecks',0)<1:
                response=self._recheck(provider,query,result,context,response,emit)
            from .OfferQuality import assess,mark_conflicts
            for offer in response['offers']:offer['quality']=assess(offer,query,result['request'])
            mark_conflicts(response['offers'])
            self._remember_previous(response,previous)
            collected.setdefault(category,[]).append(response)
            searches[category]=self._aggregate(collected[category])
            for offer in response['offers']:
                if offer.get('eur_amount') is None or offer.get('price_status')!='aktuell abgerufen' or (category!='activities' and not offer['quality']['price_eligible']):continue
                if category=='rail':self._apply_transport(result,offer,'Zug')
                elif category=='flight':self._apply_transport(result,offer,'Flug')
                elif category=='lodging':self._apply_lodging(result,offer)
                elif category=='activities':
                    from .ActivityPrices import apply_activity_price
                    apply_activity_price(result,offer)
            self._invalidate_unavailable(result,category,searches[category])
            expire_offers(result);RankingService.recompute(result)
            emit('offer_partial',copy.deepcopy(result))
            emit('phase',provider.name+': '+STATUS_LABELS[response['status']]+(' · '+response['message'] if response['message'] else ''))
        expire_offers(result);RankingService.recompute(result)
        if self.analysis and result['request'].get('ai_offer_analysis'):
            try:result=self.analysis.analyze(result,context,emit)
            except InterruptedError:raise
            except (OSError,ValueError,KeyError,TypeError):
                result['offer_analysis']={'status':'unavailable_or_rejected','accepted':[],'model_calls':0}
                emit('warning','Angebotsanalyse fehlgeschlagen; vorhandene deterministische Ergebnisse bleiben erhalten.')
        return result

    @staticmethod
    def _aggregate(responses):
        if len(responses)==1:return responses[0]
        latest=copy.deepcopy(responses[-1]);latest['providers']=copy.deepcopy(responses)
        latest['provider']='Mehrere geprüfte Quellen'
        latest['offers']=[copy.deepcopy(o) for r in responses for o in r.get('offers',[])]
        latest['sources']=list(dict.fromkeys(s for r in responses for s in r.get('sources',[])))
        latest['status']='found' if latest['offers'] else responses[-1]['status']
        latest['message']=' · '.join(r['provider']+': '+STATUS_LABELS[r['status']] for r in responses)
        return latest

    @staticmethod
    def _recheck(provider,query,trip,parent,original,emit):
        from .SearchContext import SearchContext
        parent.offer_rechecks=getattr(parent,'offer_rechecks',0)+1
        child=SearchContext(parent.cancel,seconds=min(15,max(.01,parent.deadline-time.monotonic())),budget=min(4,max(0,parent.budget-parent.calls)))
        child.disabled.update(parent.disabled)
        if child.budget==0:return dict(original,recheck=dict(status='budget_limited',calls=0))
        emit('phase','Begrenzte erneute Prüfung derselben unterstützten Angebotsquelle: '+provider.name)
        response=original;status='failed'
        try:
            fresh=provider.search(query,trip,child).to_dict()
            if fresh['parameters']!=query.to_dict() or any(o['parameters']!=query.to_dict() for o in fresh['offers']):raise ValueError('Abweichende Nachprüfungsparameter')
            if fresh['status']=='found':response=fresh;status='found'
            else:status=fresh['status']
        except InterruptedError:
            if parent.cancel.is_set():raise
            status='budget_limited'
        except (OSError,ValueError,KeyError,TypeError):pass
        finally:parent.calls+=child.calls;parent.disabled.update(child.disabled)
        response['recheck']=dict(status=status,calls=child.calls,seconds=time.monotonic()-child.started,previous_status=original['status'])
        return response

    @staticmethod
    def _remember_previous(response,previous):
        if previous and (previous.get('offers') or previous.get('previous_offers')):
            response['previous_offers']=(previous.get('offers') or previous['previous_offers'])[:8]

    @staticmethod
    def _invalidate_unavailable(trip,category,response):
        # A failed refresh never deletes history or changes the user's chosen index.
        confirmed={o['identifier'] for o in response.get('offers',[]) if o.get('quality',{}).get('price_eligible',True)}
        collection=trip.get('lodgings',[]) if category=='lodging' else [x for x in trip.get('transports',[]) if x['mode']=={'rail':'Zug','flight':'Flug'}.get(category)]
        for item in collection:
            if not item.get('offer_id'):continue
            if item['offer_id'] in confirmed:continue
            if category=='lodging' and trip.get('lodging_research'):
                entry=next((e for e in trip['lodging_research']['entries'] if e['id']==item.get('id')),None)
                if entry and entry['state'] not in ('no_matching_availability','criteria_mismatch'):
                    item['offer_refresh_status']=entry['state']
                    continue  # another house's found result is not a negative refresh of this one
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
        from .OfferQuality import fee_costs
        option['costs']+=fee_costs(offer)[0]
        for gap in offer.get('quality',{}).get('gaps',[]):
            if gap['field'] in ('fees','surcharge','directions','required'):option['costs'].append(CostItem(gap['message']).to_dict())
        for label in dict.fromkeys(offer.get('unresolved',[])):
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
            if request.get('max_center_km') and (property_data.get('distance_km') is None or property_data['distance_km']>float(request['max_center_km'])):return
            if any(property_data.get('amenities',{}).get(k) is not True for k in request.get('required',[])):return
            item=dict(property_data,latitude=property_data.get('latitude'),longitude=property_data.get('longitude'),distance_km=property_data.get('distance_km'),rooms=offer.get('details',{}).get('units'),price={},
                      link_kind='Geprüfte direkte Buchungsstrecke',search_url=offer['source'],open_criteria=[],
                      data_status='Identität und Standort aus direkter Anbieter-Buchungsstrecke',source_updated='Direkte Angebotsantwort',
                      source_place=trip['destination']['name'])
            trip.setdefault('lodgings',[]).append(item);matches=[item]
        item=matches[0];item.pop('offer_refresh_status',None)
        item['amenities']=dict(property_data.get('amenities',item.get('amenities',{})))
        offers=item.setdefault('offers',[])
        offers[:]=[x for x in offers if x.get('identifier')!=offer['identifier']]+[copy.deepcopy(offer)]
        offers[:]=offers[-8:]
        item.update(offer_id=offer['identifier'],offer=offer,price=cls._cost(offer,'Unterkunft für Gruppe und Aufenthalt'),
                                   occupancy_status='Angefragte Zimmerbelegung im Angebot bestätigt',
                                   booking_status='Zum Abrufzeitpunkt angeboten; keine Reservierung',retrieved_at=offer['retrieved_at'])
        missing=[k for k in trip['request'].get('required',[]) if item['amenities'].get(k) is not True]
        if missing:
            reason='Pflichtausstattung unbelegt: '+', '.join(missing)
            item['open_criteria']=list(dict.fromkeys(item.get('open_criteria',[])+[reason]))
            trip['open_criteria']=list(dict.fromkeys(trip.get('open_criteria',[])+[reason]));trip['filter_status']='offen'
        if all(item['amenities'].get(k) is True for k in trip['request'].get('required',[])):
            item['open_criteria']=[r for r in item.get('open_criteria',[]) if not r.startswith('Pflichtausstattung unbelegt:')]
            # Only this selected source-backed room may resolve this criterion.
            if not item.get('open_criteria'):
                trip['open_criteria']=[r for r in trip.get('open_criteria',[]) if not r.startswith('Pflichtausstattung unbelegt:')]
                if not trip['open_criteria']:trip['filter_status']='passend'
        item['rooms']=offer.get('details',{}).get('units',item.get('rooms'))
        item['price']['scope']=f"{offer['parameters']['adults']} Erwachsene"+(f" und {len(offer['parameters'].get('children_ages',[]))} Kinder" if offer['parameters'].get('children_ages') else '')+f" / {offer['parameters']['rooms']} Zimmer / {trip['nights']} Nächte"
        from .OfferQuality import fee_costs
        item['mandatory_costs']=fee_costs(offer)[0]
        for gap in offer.get('quality',{}).get('gaps',[]):
            if gap['field'] in ('fees','occupancy','required'):item['mandatory_costs'].append(CostItem(gap['message']).to_dict())
        known_labels={c['label'] for c in item['mandatory_costs']}
        item['mandatory_costs'] += [CostItem(label).to_dict() for label in dict.fromkeys(offer.get('unresolved',[])) if label not in known_labels]
