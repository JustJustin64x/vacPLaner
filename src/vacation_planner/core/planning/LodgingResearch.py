"""Per-property ledger. No network/model access and no provider identities."""
import copy
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone

LABELS={
 'pending':'Noch nicht geprüft','running':'Prüfung läuft',
 'confirmed':'Passendes Angebot einschließlich Pflichtkosten belegt',
 'partial':'Teilweise geprüft; Pflichtangaben fehlen',
 'no_matching_availability':'Keine passende Verfügbarkeit laut Quelle',
 'criteria_mismatch':'Nachweislich nicht passend','identity_uncertain':'Zuordnung unklar',
 'no_booking_source':'Keine auswertbare Buchungsquelle gefunden',
 'unsupported_variant':'System oder Variante nicht unterstützt',
 'blocked':'Abruf gesperrt','source_error':'Quellenfehler',
 'deferred_budget':'Wegen Zeit-/Abrufbudget offen','cancelled':'Abgebrochen',
 'interaction_required':'Nutzerinteraktion erforderlich'}


def stamp():return datetime.now(timezone.utc).isoformat(timespec='seconds')


def query_key(trip):
    from .TravelOffers import OfferQuery
    data={'query':OfferQuery.from_trip(trip).to_dict(),
          'destination':{k:trip['destination'].get(k) for k in ('id','code','country_code','latitude','longitude')},
          'required':trip['request'].get('required',[]),
          'radius':trip['request'].get('lodging_radius_km'),
          'center_limit':trip['request'].get('max_center_km')}
    return hashlib.sha256(json.dumps(data,sort_keys=True,ensure_ascii=False).encode()).hexdigest()


def initialize(trip,items=None):
    key=query_key(trip);old=trip.get('lodging_research',{})
    if old.get('query_key')==key:
        ledger=old
    else:
        ledger={'schema_version':1,'query_key':key,'entries':[],
                'coverage':copy.deepcopy(trip.get('lodging_coverage',[])),'runs':[]}
    by_id={e['id']:e for e in ledger['entries']}
    for item in items if items is not None else trip.get('lodgings',[]):
        identity=item.get('id') or 'source:'+hashlib.sha256((item.get('source','')+'|'+item['name']).encode()).hexdigest()[:24]
        if identity in by_id:
            existing=by_id[identity]['lodging']
            existing['source_aliases']=list(dict.fromkeys(existing.get('source_aliases',[])+[item.get('source','')]))
            continue
        e={'id':identity,'lodging':copy.deepcopy(dict(item,id=identity)),
           'state':'pending','stage':'website','attempts':0,'reason':'Noch keine Angebotsprüfung',
           'history':[],'offers':[],'official_website':False,'system':'','variant':'',
           'offer_checks':0,'network_calls':0}
        ledger['entries'].append(e);by_id[identity]=e
    trip['lodging_research']=ledger
    summarize(ledger)
    return ledger


def summarize(ledger):
    entries=ledger['entries'];counts=Counter(e['state'] for e in entries)
    ledger['metrics']={'found':len(entries),'states':dict(counts),
        'official_websites':sum(bool(e.get('official_website')) for e in entries),
        'systems':dict(Counter((e.get('system','')+' / '+e.get('variant','')) for e in entries if e.get('system'))),
        'offer_checks':sum(e.get('offer_checks',0) for e in entries),
        'selection_responses':sum(e.get('selection_responses',0) for e in entries),
        'rejected_responses':sum(len(e.get('rejected_responses',[])) for e in entries),
        'confirmed_properties':counts['confirmed'],
        'partial_properties':counts['partial'],
        'confirmed_offers':sum(sum(o.get('quality',{}).get('status')=='verified' for o in e.get('offers',[])) for e in entries),
        'source_quotes':sum(len(e.get('offers',[])) for e in entries)}
    assert sum(counts.values())==len(entries)
    return ledger['metrics']


def finish(entry,state,reason):
    if state not in LABELS:raise ValueError('Unbekannter Unterkunftsstatus')
    entry.update(state=state,reason=reason,last_attempt=stamp())
    entry.setdefault('history',[]).append({'state':state,'reason':reason,'at':entry['last_attempt']})
    entry['history']=entry['history'][-8:]
