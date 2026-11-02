"""Bounded, call-scoped references; no model-generated geographic facts trusted."""
import itertools
import math
import re
import threading
from .PlaceResearch import distance
from .CandidateSelection import same_holiday_region
from .RankingService import RankingService

MAX_IDEAS=4
MAX_DEEP=2
MAX_REFERENCES=12
_counter=itertools.count(1)
_lock=threading.Lock()


def geographic_allowed(catalog,d,request,origin):
    if d.get('kind') not in (None,'settlement') or not catalog.allowed(d,request):return False
    if not all(type(d.get(k)) in (int,float) and math.isfinite(d[k]) for k in ('latitude','longitude')):return False
    if not -90<=d['latitude']<=90 or not -180<=d['longitude']<=180:return False
    if not catalog.european_place(d):return False
    km=distance(origin,d)
    if km<=5 or (request.max_distance_km and km>float(request.max_distance_km)):return False
    kind=d.get('base_type',d.get('type'))
    return (request.target_type=='gemischt' or request.target_type in d.get('landscapes',[]) or
            request.target_type=='Stadt' and kind in ('Großstadt','Klein-/Mittelstadt') or
            request.target_type=='kleiner Ort' and kind in ('Dorf/Ferienort','Klein-/Mittelstadt'))


class IdeaReferences:
    def __init__(self,places):
        with _lock:call=next(_counter)
        self.mapping={f'C{call:X}P{i+1:X}':p for i,p in enumerate(places[:MAX_REFERENCES])}

    def resolve(self,row):
        ref=row['reference']
        if ref not in self.mapping:raise ValueError('Unbekannte oder fremde Aufrufreferenz.')
        d=self.mapping[ref]
        # A reference cannot be used to smuggle another name/country.
        if row['name']!=d['name'] or row['country']!=d['code']:raise ValueError('Referenz und Ortsangaben widersprechen sich.')
        return d

    def schema(self,countries):
        return dict(type='object',properties=dict(ideas=dict(type='array',maxItems=MAX_IDEAS,items=dict(type='object',properties=dict(
            reference=dict(type='string',enum=['',*self.mapping],description='Aufrufreferenz exakt kopieren oder leer für einen zusätzlichen Ortsnamen.'),
            name=dict(type='string',description='Konkreter Aufenthaltsort; keine Landschaft, Region oder Aktivität.'),
            country=dict(type='string',enum=list(countries),description='ISO-Ländercode des Orts.'),
            region=dict(type='string',description='Nur bekannte eindeutige Region, sonst leer.')),
            required=['reference','name','country','region'],additionalProperties=False))),required=['ideas'],additionalProperties=False)

    def messages(self,request,avoided):
        public=[dict(reference=ref,name=p['name'],country=p['code'],region=p.get('region',''),type=p.get('base_type',p.get('type')),
                     mapped_topics=[k for k,n in p.get('feature_profile',{}).get('counts',{}).items() if n and request.interests.get(k)]) for ref,p in self.mapping.items()]
        import json
        return [dict(role='system',content='Schlage höchstens vier zusätzliche konkrete europäische Aufenthaltsorte vor. Bevorzuge die angegebenen geprüften Ortsreferenzen, du darfst auch andere Ortsnamen mit leerer Referenz nennen. Die Referenzen liegen außerhalb der bisherigen vertieften Vorauswahl. Bei Referenz Name und ISO-Land exakt kopieren, Region darf leer sein. Keine Koordinaten, URLs, Preise oder Eignungszusagen. Regionen/Seen/Wanderwege sind keine Übernachtungsorte. Bevorzuge zu den ausdrücklich gewählten Interessen passende kleinere Basisorte, soweit sinnvoll. Unbekannte Daten nicht erfinden. Antworte nur gemäß JSON-Vertrag.'),
                dict(role='user',content=json.dumps(dict(countries=request.countries,regions=request.regions,excluded=request.excluded,target_type=request.target_type,
                    interests={k:v for k,v in request.interests.items() if v},already_considered=avoided[:16],references=public),ensure_ascii=False))]


def reference_places(catalog,candidates,chosen,results,request,origin,context):
    blocked={d['id'] for d in chosen};pool=[]
    for i,d in enumerate(candidates):
        if i%200==0:context.check()
        if d.get('id') in blocked or not geographic_allowed(catalog,d,request,origin):continue
        if any(same_holiday_region(d,t['destination']) for t in results):continue
        pool.append(d)
    pool.sort(key=lambda d:(-RankingService.interest_match(d,request),distance(origin,d),str(d['id'])))
    selected=[]
    for d in pool:
        if any(same_holiday_region(d,p) for p in selected):continue
        selected.append(d)
        if len(selected)==MAX_REFERENCES:break
    return selected


def valid_name(value):
    return isinstance(value,str) and 1<=len(value)<=80 and not any(ord(c)<32 for c in value) and not re.search(r'[:/\\<>]',value)
