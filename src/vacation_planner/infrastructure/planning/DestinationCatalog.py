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
                  'boehmische schweiz':'Böhmische Schweiz'}

    def __init__(self):
        self.destinations=json.loads((Path(__file__).parent/'data/destinations.json').read_text())

    def resolve(self,name):
        return next((d for d in self.destinations if normalize(name) in
                     {normalize(d['name']),*(normalize(a) for a in d.get('aliases',[]))}),None)

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
                    near=difflib.get_close_matches(self.area(value),lookup,n=3,cutoff=.3)
                    raise ValueError(f'Gebiet nicht erkannt: „{value}“. '+('Meinten Sie: '+', '.join(lookup[n] for n in near)+'?' if near else 'Bitte ein unterstütztes Gebiet auswählen.'))

    def allowed(self,d,request):
        labels=self.labels(d)
        return ((not request.countries or bool({self.area(v) for v in request.countries}&{self.area(d['country']),self.area(d['code'])})) and
                (not request.regions or bool({self.area(v) for v in request.regions}&labels)) and
                not bool({self.area(v) for v in request.excluded}&labels))

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
        return sorted([d for d in self.destinations if d['source']!=base['source'] and self.allowed(d,request)
                       and distance(base,d)<=radius],key=lambda d:distance(base,d))[:2]
