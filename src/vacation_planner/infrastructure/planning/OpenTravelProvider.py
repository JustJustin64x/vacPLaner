import json
import os
from pathlib import Path
from urllib.parse import urlencode, quote
from .PublicHttpClient import PublicHttpClient
from .WikivoyageParser import WikivoyageParser
from .DestinationCatalog import DestinationCatalog


class OpenTravelProvider:
    def __init__(self, store, http=None):
        self.store,self.http = store,http or PublicHttpClient()
        self.catalog = DestinationCatalog()
        self.parser = WikivoyageParser()
        self.routing_base = os.environ.get('VACATION_ROUTING_URL','https://routing.openstreetmap.de/routed-car').rstrip('/')

    def research_offers(self,trip,context,emit=lambda *args:None,categories=None,samples=False):
        from ...core.planning.OfferResearchService import OfferResearchService
        from .RegioJetOfferProvider import RegioJetOfferProvider
        from .SmoobuOfferProvider import SmoobuOfferProvider
        from .FlightAccessDiagnostics import FlightAccessDiagnostics
        from .OfficialActivityPrices import OfficialActivityPrices
        providers=[SmoobuOfferProvider(self.http),OfficialActivityPrices(self.http)]
        providers.append(RegioJetOfferProvider(self.http,self.store))
        providers.append(FlightAccessDiagnostics())
        service=OfferResearchService(providers)
        return service.research_samples(trip,context,emit,categories) if samples else service.research(trip,context,emit,categories)

    def origin(self, name, address, context):
        known = self.catalog.resolve(name)
        if known and not address:
            return dict(known, precision='Ortszentrum; Startadresse fehlt')
        # Deliberate restricted geocoding: one user-submitted city, no autocomplete/bulk.
        # Exact personal addresses are not transmitted to the public service.
        if known:
            return dict(known, precision='Startadresse lokal gespeichert; Route ab Ortszentrum, Adresse nicht geocodiert')
        key = 'origin:'+name.strip().casefold()
        cached = self.store.cache_get(key,30*86400)
        if cached:
            return cached[0]
        base = os.environ.get('VACATION_GEOCODING_URL','https://nominatim.openstreetmap.org/search')
        data,stamp = self.http.json(base+'?'+urlencode(dict(q=name,format='jsonv2',limit=1)),context)
        if not data:
            raise ValueError('Startort nicht gefunden. Bitte Ort und Land angeben.')
        row = data[0]
        result = dict(name=name,latitude=float(row['lat']),longitude=float(row['lon']),
                      precision='Ortszentrum aus OpenStreetMap; genaue Startadresse nicht geocodiert',
                      source='https://www.openstreetmap.org/copyright',retrieved_at=stamp)
        self.store.cache_set(key,result,stamp)
        return result

    def places(self, destination, context):
        key = 'places-v4:'+destination['source']
        cached = self.store.cache_get(key,7*86400)
        if cached:
            return dict(cached[0],cache_note='Ortsdaten aus Cache (bis 7 Tage); keine gespeicherten Live-Preise',warnings=[])
        try:
            html,stamp = self.http.get(destination['source'],context)
            parsed = self.parser.parse(html,destination,stamp)
            self.store.cache_set(key,parsed,stamp)
            return dict(parsed,cache_note='Ortsdaten neu abgerufen',warnings=[])
        except InterruptedError:
            raise
        except (OSError,ValueError) as exc:
            stale = self.store.cache_get(key)
            if stale:
                return dict(stale[0],cache_note='Veraltete Ortsdaten: '+stale[1],warnings=[str(exc)])
            snapshot = Path(__file__).parent/'data/place_snapshots.json'
            data = json.loads(snapshot.read_text()) if snapshot.exists() else {}
            if destination['name'] in data:
                snapshot_data=self.parser.migrate_snapshot(data[destination['name']])
                return dict(snapshot_data,cache_note='Mitgelieferter Quellenstand vom 27.10.2026; möglicherweise veraltet',warnings=[str(exc)])
            return dict(lodgings=[],activities=[],cache_note='Keine Ortsdaten abrufbar',warnings=[str(exc)])

    def route(self, origin, destination, context):
        a = f"{origin['longitude']},{origin['latitude']}"
        b = f"{destination['longitude']},{destination['latitude']}"
        url = self.routing_base+'/route/v1/driving/'+a+';'+b+';'+a+'?overview=false&steps=false'
        data,stamp = self.http.json(url,context)
        if data.get('code') != 'Ok' or not data.get('routes'):
            raise OSError('Keine befahrbare Straßenroute verfügbar.')
        route = data['routes'][0]
        if len(route.get('legs',[]))!=2 or any(x['distance'] < 0 or x['duration'] < 0 for x in route['legs']):
            raise ValueError('Unvollständige Straßenroute')
        return dict(legs=route['legs'],source=url,retrieved_at=stamp,precision=origin['precision'])
