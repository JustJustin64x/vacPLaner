"""Independent transport scenarios; never add mutually exclusive journeys."""
import copy
from urllib.parse import urlencode

from .CostService import CostService
from .TravelOffers import STATUS_LABELS, expire_offers


def comparison(trip):
    trip=expire_offers(copy.deepcopy(trip))
    request=trip['request'];lodgings=trip.get('lodgings') or []
    lodging=lodgings[min(max(0,trip.get('selected_lodging',0)),len(lodgings)-1)] if lodgings else {}
    accommodation=[lodging.get('price') or {'label':'Unterkunft für Gruppe und Aufenthalt','low':None,'status':'unbekannt'}]+lodging.get('mandatory_costs',[])
    rows=[]
    for mode,category in (('Auto',None),('Zug','rail'),('Flug','flight')):
        options=[x for x in trip.get('transports',[]) if x['mode']==mode]
        search=trip.get('offer_searches',{}).get(category,{})
        if not options:
            q=f"{request.get('origin','')} nach {trip.get('destination',{}).get('name','')} {trip.get('start')} Rückreise {trip.get('end')} {request.get('adults')} Erwachsene"
            url=('https://www.bahn.de/buchung/start' if mode=='Zug' else 'https://www.google.com/travel/flights?'+urlencode({'q':q}) if mode=='Flug' else 'https://www.openstreetmap.org/directions')
            options=[{'mode':mode,'status':'Nicht geprüft; keine Aussage zur Verfügbarkeit','costs':[{'label':mode+' Hin-/Rückreise einschließlich Zubringern','low':None,'status':'unbekannt'}],
                      'links':[{'label':'Suchparameter dort prüfen: '+q,'url':url}], 'notes':[]}]
        for option in options:
            option=copy.deepcopy(option)
            if search and not option.get('offer_id'):
                option['status']=STATUS_LABELS.get(search.get('status'),'Nicht geprüft')+': '+search.get('message','')
            summary=CostService.summarize(option.get('costs') or [{'label':mode+' Hin-/Rückreise','low':None,'status':'unbekannt'}],request.get('budget','0'))
            scenario=CostService.summarize(accommodation+(option.get('costs') or [{'label':mode+' Hin-/Rückreise','low':None,'status':'unbekannt'}]),request.get('budget','0'))
            rows.append({'option':option,'transport_cost':summary,'scenario':scenario})
    return rows
