import json
from pathlib import Path
from urllib.parse import quote


class DestinationCatalog:
    def __init__(self):
        self.destinations = json.loads((Path(__file__).parent/'data/destinations.json').read_text())

    def resolve(self, name):
        return next((d for d in self.destinations if name.strip().casefold() in
                     [d['name'].casefold()]+[a.casefold() for a in d.get('aliases',[])]),None)

    def candidates(self, request):
        countries = {x.casefold() for x in request.countries}
        regions = {x.casefold() for x in request.regions}
        exclude = {x.casefold() for x in request.excluded}
        return [d for d in self.destinations if
                (not countries or d['country'].casefold() in countries or d['code'].casefold() in countries) and
                (not regions or d['region'].casefold() in regions) and
                not {d['name'].casefold(),d['country'].casefold(),d['code'].casefold(),d['region'].casefold()} & exclude and
                d['name'].casefold()!=request.origin.strip().casefold()]
