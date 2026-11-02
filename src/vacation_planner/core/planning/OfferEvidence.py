"""Source-bound observations. Model selects references, never authors values."""
import hashlib
import itertools
import json
import re
import threading
from .TravelOffers import amount

VERSION=1
FIELDS=('price','currency','basis','period','occupancy','availability','fee','amenity','condition')
_counter=itertools.count(1);_lock=threading.Lock()


def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,allow_nan=False).encode()).hexdigest()


def observation(offer_id,url,stamp,pointer,field,value,unit=''):
    if field not in FIELDS or not pointer.startswith('/') or not url.startswith('https://'):raise ValueError('Ungültiger Originalnachweis')
    text=json.dumps(value,ensure_ascii=False,sort_keys=True,allow_nan=False)
    if len(text)>400:return None
    row=dict(offer_id=offer_id,source_id='os-'+digest(url)[:20],source_url=url,retrieved_at=stamp,pointer=pointer,field=field,quote=text,unit=unit)
    row['id']='of-'+digest(row)[:24]
    return row


def fact(row,offer):
    original={k:v for k,v in row.items() if k!='id'}
    if row['id']!='of-'+digest(original)[:24] or row['offer_id']!=offer['identifier'] or row['source_id']!='os-'+digest(row['source_url'])[:20]:raise ValueError('Fremde oder veränderte Fundstelle')
    if row['source_url'] not in offer.get('evidence',{}).get('sources',[]) or row['retrieved_at']!=offer.get('evidence',{}).get('source_times',{}).get(row['source_url'],offer['retrieved_at']):raise ValueError('Quelle oder Quellenstand falsch zugeordnet')
    value=json.loads(row['quote']);field=row['field'];unit=row['unit'];status='structured_source_value'
    if field=='price':
        if isinstance(value,dict):
            # Complete explicit structured basis; never parse an arbitrary euro amount out of prose.
            if set(value)-{'amount','currency','basis','qualifier'} or not {'amount','currency','basis'}<=set(value):raise ValueError('Unvollständiger Preisnachweis')
            if value['currency'] not in ('EUR','USD','GBP','CHF','CZK'):raise ValueError('Nicht belegte Währung')
            if value.get('qualifier') not in (None,'from','exact'):raise ValueError('Unbekannter Preisvorbehalt')
            if value['basis'] not in ('per_night','per_person','per_room','per_room_night','total','oneway','roundtrip'):raise ValueError('Unbekannte Preisbasis')
            value=dict(value,amount=str(amount(value['amount'])))
            unit=value['currency']+' / '+value['basis']
        else:
            if unit not in ('EUR','USD','GBP','CHF','CZK'):raise ValueError('Währung der Preisstelle nicht belegt')
            value=str(amount(value))
    elif field=='currency':
        if value not in ('EUR','USD','GBP','CHF','CZK','€'):raise ValueError('Unbekannte Währung')
    elif field=='amenity':
        if not isinstance(value,str):raise ValueError('Ungültige Leistungsstelle')
        m=re.fullmatch(r'(Frühstück|WLAN|Küche|Pool|Parkplatz|Haustiere|Kostenlose Stornierung)(?: (inklusive|enthalten|optional|gegen Aufpreis|nicht enthalten|nicht erlaubt))?',value)
        if not m:status='source_hint_only'
        else:value=dict(name=m[1],state={'inklusive':'included','enthalten':'included','optional':'extra','gegen Aufpreis':'extra','nicht enthalten':'excluded','nicht erlaubt':'excluded',None:'described_only'}[m[2]])
    elif field=='fee':
        if not isinstance(value,dict) or not {'amount','currencyCode'}<=set(value):raise ValueError('Gebührenbetrag oder Währung nicht belegt')
        amount(value['amount'],allow_negative=True);unit=value['currencyCode'];status='included_component_source_value'
    elif field=='condition':
        if not isinstance(value,str) or not value:raise ValueError('Leere Bedingung')
        status='source_hint_only' # no general cancellation/refund promise from prose
    elif field=='availability':
        if type(value) is not bool:raise ValueError('Verfügbarkeit nicht strukturiert belegt')
    elif field=='occupancy':
        if type(value) is not int or value<1:raise ValueError('Ungültige Personen-/Einheitenzahl')
        status='capacity_only' if unit=='capacity' else 'structured_source_value'
    elif field=='basis':
        if type(value) is not int or value<1 or unit!='nights':raise ValueError('Nächte nicht strukturiert belegt')
    elif field=='period':
        from datetime import date
        if not isinstance(value,str) or date.fromisoformat(value).isoformat()!=value:raise ValueError('Zeitraum nicht strukturiert belegt')
    else:raise ValueError('Nicht freigegebene Aussageart')
    return dict(observation_id=row['id'],offer_id=row['offer_id'],source_id=row['source_id'],source_url=row['source_url'],pointer=row['pointer'],
        original_quote=row['quote'],retrieved_at=row['retrieved_at'],field=field,value=value,unit=unit,validation=status)


class References:
    def __init__(self,offers):
        with _lock:serial=next(_counter)
        self.offers={};self.rows={};self.payload=[]
        for i,offer in enumerate(offers[:4]):
            key=f'A{serial:X}O{i+1}';self.offers[key]=offer
            for row in offer.get('evidence',{}).get('observations',[]):
                if len(self.rows)>=12:break
                if not row:continue
                ref=f'A{serial:X}S{len(self.rows)+1}'
                # Context itself is checked; corrupt cached provenance never reaches the model.
                try:fact(row,offer)
                except (ValueError,TypeError,KeyError):continue
                self.rows[ref]=(key,row)
                self.payload.append(dict(offer_ref=key,source_ref=ref,field=row['field'],quote=row['quote'],unit=row['unit']))
    def schema(self):
        return dict(type='object',properties=dict(selections=dict(type='array',maxItems=12,items=dict(type='object',properties=dict(
            offer_ref=dict(type='string',enum=list(self.offers)),source_ref=dict(type='string',enum=list(self.rows)),field=dict(type='string',enum=list(FIELDS))),
            required=['offer_ref','source_ref','field'],additionalProperties=False))),required=['selections'],additionalProperties=False)
    def validate(self,response):
        if set(response)!={'selections'} or not isinstance(response['selections'],list) or len(response['selections'])>12:raise ValueError('Ungültiger Analysevertrag')
        accepted=[];seen=set()
        for selection in response['selections']:
            if set(selection)!={'offer_ref','source_ref','field'}:raise ValueError('Nicht erlaubte Werte oder Summen')
            key,row=self.rows[selection['source_ref']]
            if key!=selection['offer_ref'] or row['field']!=selection['field'] or row['id'] in seen:raise ValueError('Doppelte, fremde oder falsch interpretierte Fundstelle')
            seen.add(row['id']);accepted.append(fact(row,self.offers[key]))
        return accepted
