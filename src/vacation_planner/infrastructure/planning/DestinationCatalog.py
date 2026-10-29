import json
import unicodedata
import difflib
from pathlib import Path
from ...core.domain.value_objects.GeographicCoordinates import GeographicCoordinates


def normalize(value):
    value=value.strip().casefold().replace('ß','ss')
    for a,b in [('ä','ae'),('ö','oe'),('ü','ue')]: value=value.replace(a,b)
    return ''.join(c for c in unicodedata.normalize('NFKD',value) if not unicodedata.combining(c))


def distance(a,b):
    return GeographicCoordinates(a['latitude'],a['longitude']).calculate_distance_in_kilometers_to(
        GeographicCoordinates(b['latitude'],b['longitude']))


class DestinationCatalog:
    VERSION=2
    AREA_ALIASES={'black forest':'Schwarzwald','saxon switzerland':'Sächsische Schweiz',
                  'austria':'Österreich','czechia':'Tschechien','czech republic':'Tschechien',
                  'germany':'Deutschland','bohemian switzerland':'Böhmische Schweiz',
                  'mecklenburg lake district':'Mecklenburgische Seenplatte','dolomites':'Dolomiten',
                  'boehmische schweiz':'Böhmische Schweiz','tyrol':'Tirol','carinthia':'Kärnten','styria':'Steiermark',
                  'upper austria':'Oberösterreich','lower austria':'Niederösterreich','vienna':'Wien'}

    def __init__(self,inventory=None,context=None):
        self.inventory=inventory
        self.refresh(context)

    def refresh(self,context=None):
        legacy=json.loads((Path(__file__).parent/'data/destinations.json').read_text())
        if not self.inventory:
            self.destinations=legacy;return
        imported=self.inventory.candidates(context);by_name={}
        for d in imported:
            for name in [d['name'],*d.get('aliases',[])]:
                by_name.setdefault((d['code'],normalize(name)),[]).append(d)
        for old in legacy:
            options=by_name.get((old['code'],normalize(old['name'])),[])
            same=next((d for d in options if distance(old,d)<.8),None)
            if same:
                same['legacy_source']=old['source'];same['wikivoyage_source']=old['source']
                same['aliases']=list(dict.fromkeys(same.get('aliases',[])+[old['name']]+old.get('aliases',[])))
                same['name']=old['name'];same['regions']=list(dict.fromkeys(same['regions']+old.get('regions',[])))
                same['legacy_id']=old['id']
            else:imported.append(old)
        self.destinations=imported

    def resolve(self,name):
        pieces=name.split(',',1);wanted=normalize(pieces[0]);country=normalize(pieces[1]) if len(pieces)>1 else ''
        matches=[d for d in self.destinations if (not country or country in (normalize(d['code']),normalize(d['country']))) and wanted in
                 {normalize(d['name']),*(normalize(a) for a in d.get('aliases',[]))}]
        exact=[d for d in matches if normalize(d['name'])==wanted]
        matches=exact or matches
        return matches[0] if len(matches)==1 else None

    def area(self,value):
        value=normalize(value)
        return normalize(self.AREA_ALIASES.get(value,value))

    def labels(self,d):
        return {self.area(v) for v in [d['name'],d['country'],d['code'],d['region'],
                *d.get('regions',[]),*d.get('aliases',[])]}

    def supported(self,kind):
        if kind=='countries':return sorted({v for d in self.destinations for v in (d['country'],d['code'])})
        if kind=='regions':return sorted({v for d in self.destinations for v in [d['region'],*d.get('regions',[])]})
        return sorted({v for d in self.destinations for v in [d['name'],d['country'],d['code'],d['region'],*d.get('regions',[]),*d.get('aliases',[])]})

    def validate_areas(self,request):
        for kind in ('countries','regions','excluded'):
            labels=self.supported(kind)
            lookup={self.area(v):v for v in labels}
            for value in getattr(request,kind):
                if self.area(value) not in lookup:
                    if self.inventory and kind=='countries':
                        from .DestinationImportService import COUNTRIES
                        code=next((c for c,n in COUNTRIES.items() if self.area(value) in (self.area(c),self.area(n))),None)
                        if code:raise ValueError(COUNTRIES[code]+': geografischer Grundbestand noch nicht importiert. Unter „Zieldaten einrichten“ herunterladen.')
                    near=difflib.get_close_matches(self.area(value),lookup,n=3,cutoff=.3)
                    raise ValueError(f'Gebiet nicht erkannt: „{value}“. '+('Meinten Sie: '+', '.join(lookup[n] for n in near)+'?' if near else 'Bitte ein unterstütztes Gebiet auswählen.'))

    def allowed(self,d,request):
        labels=self.labels(d)
        return ((not request.countries or bool({self.area(v) for v in request.countries}&{self.area(d['country']),self.area(d['code'])})) and
                (not request.regions or bool({self.area(v) for v in request.regions}&labels)) and
                not bool({self.area(v) for v in request.excluded}&labels))

    def country_allowed(self,code,request):
        from .DestinationImportService import COUNTRIES
        labels={self.area(code),self.area(COUNTRIES.get(code,code))}
        return (not request.countries or bool(labels & {self.area(v) for v in request.countries})) and not bool(labels & {self.area(v) for v in request.excluded})

    def candidates(self,request):
        self.validate_areas(request)
        origin=self.resolve(request.origin)
        return [d for d in self.destinations if self.allowed(d,request) and
                (origin is None or d.get('id',d['name'])!=origin.get('id',origin['name'])) and
                normalize(d['name'])!=normalize(request.origin) and
                (request.target_type=='gemischt' or request.target_type in d.get('landscapes',[]) or
                 (request.target_type=='Stadt' and d.get('type') in ('Großstadt','Klein-/Mittelstadt')) or
                 (request.target_type=='kleiner Ort' and d.get('base_type',d.get('type')) in ('Dorf/Ferienort','Klein-/Mittelstadt')))]

    def nearby(self,base,request):
        radius=max(float(request.lodging_radius_km),float(request.activity_radius_km))
        # Only verified catalog places; no unconstrained link crawling.
        pool=self.destinations
        if self.inventory and base.get('geonames_id'):
            pool=self.inventory.nearby(base['latitude'],base['longitude'],radius)
            pool=[d for d in pool if d.get('kind')=='settlement']
        return sorted([d for d in pool if d['source']!=base['source'] and self.allowed(d,request)
                       and distance(base,d)<=radius],key=lambda d:distance(base,d))[:2]

    def nearest(self,item):
        if self.inventory:
            pool=[d for d in self.inventory.nearby(item['latitude'],item['longitude'],20) if d.get('kind')=='settlement']
            if pool:return min(pool,key=lambda d:distance(item,d))
        return min(self.destinations,key=lambda d:distance(item,d))

    def coverage(self):
        return self.inventory.coverage() if self.inventory else []

    def coverage_status(self,request):
        if not self.inventory:return None
        from .DestinationImportService import COUNTRIES
        imported={d['country'] for d in self.coverage() if d['key'].startswith('geonames:')}
        missing=[code for code in COUNTRIES if code not in imported]
        warnings=[COUNTRIES[code]+': breiter Grundbestand noch nicht importiert; nur vorhandene Reiseführerziele werden geprüft. „Zieldaten einrichten“ erweitert die Abdeckung.' for code in missing
                  if any(self.area(v) in (self.area(code),self.area(COUNTRIES[code])) for v in request.countries)]
        return {'imported_count':len(imported),'not_imported':missing,'warnings':warnings}
