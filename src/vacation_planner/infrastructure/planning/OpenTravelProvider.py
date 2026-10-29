import json
import os
from pathlib import Path
from urllib.parse import urlencode, quote
from .PublicHttpClient import PublicHttpClient
from .WikivoyageParser import WikivoyageParser
from .DestinationCatalog import DestinationCatalog
from .TripStore import timestamp


class OpenTravelProvider:
    def __init__(self, store, http=None,catalog=None):
        self.store,self.http = store,http or PublicHttpClient()
        from .DestinationInventory import DestinationInventory
        self.inventory=getattr(catalog,'inventory',None) or DestinationInventory(store.path.with_name('destinations.sqlite3'))
        self.catalog = catalog or DestinationCatalog(self.inventory)
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

    def enrich_candidates(self,candidates,request,origin,context,emit):
        """At most three small regional queries, independent of the number of villages."""
        if not request.regional_queries or not any(d.get('geonames_id') for d in candidates):return candidates
        from .DestinationImportService import DestinationImportService
        from ...core.planning.PlaceResearch import distance
        backoff=self.store.cache_get('regional-source-backoff-v1',6*3600)
        if backoff:
            emit('warning','Regionale Online-Ergänzung vorübergehend ausgesetzt: '+backoff[0]['message']+' · lokale Daten bleiben nutzbar. Manuell unter Zieldaten erneut prüfbar.')
            return candidates
        eligible=[d for d in candidates if d.get('geonames_id') and d.get('feature_profile',{}).get('coverage')=='unknown'
                  and (not request.max_distance_km or distance(origin,d)<=float(request.max_distance_km))]
        if not eligible:return candidates
        # Geographic regions guide where to look, never stand in for interest evidence.
        codes={'LK','LKS','BAY'} if request.interests.get('Baden',0) else {'MTS','PRK','RESN'} if request.interests.get('Wandern',0) or request.interests.get('Natur',0) else set()
        seeds=[]
        if codes:
            with self.inventory.connect() as db:
                for (raw,) in db.execute("SELECT payload FROM places WHERE kind='region'"):
                    d=json.loads(raw)
                    if d['feature_code'] in codes and self.catalog.allowed(d,request):seeds.append(d)
        seeds=sorted(seeds or eligible,key=lambda d:(distance(origin,d),d['id']))
        chosen=[];service=DestinationImportService(self.inventory,self.http)
        for seed in seeds:
            context.check()
            if len(chosen)>=request.regional_queries or context.calls>=max(0,context.budget-4):break
            if any(distance(seed,old)<35 for old in chosen):continue
            # Need an allowed actual stay nearby; never research a lake as overnight base.
            stays=[d for d in self.inventory.nearby(seed['latitude'],seed['longitude'],15) if d['kind']=='settlement' and self.catalog.allowed(d,request)]
            if not stays:continue
            if any(d.get('feature_profile',{}).get('coverage')=='regional' and distance(seed,d)<8 for d in candidates):continue
            lat,lon=seed['latitude'],seed['longitude'];bounds=(round(lat-.08,4),round(lon-.10,4),round(lat+.08,4),round(lon+.10,4))
            emit('phase','Fehlende Interessenmerkmale gezielt ergänzen: Umgebung '+seed['name']+' · kleine gebündelte Abfrage')
            try:service.update_region('Umgebung '+seed['name'],bounds,context,emit)
            except (OSError,ValueError) as exc:
                self.store.cache_set('regional-source-backoff-v1',{'message':str(exc)},timestamp())
                emit('warning','Regionale Zusatzquelle nicht verfügbar: '+str(exc)+' · Suche läuft mit lokalen Daten weiter.');break
            chosen.append(seed)
        if chosen:
            self.catalog.refresh(context);return self.catalog.candidates(request)
        return candidates

    def places(self, destination, context):
        if destination.get('geonames_id') or destination.get('inventory_place'):
            local=self._inventory_places(destination)
            source=destination.get('wikivoyage_source')
            if not source:return local
            destination=dict(destination,source=source)
        else:local=None
        key = 'places-v4:'+destination['source']
        cached = self.store.cache_get(key,7*86400)
        if cached:
            return self._merge_local(dict(cached[0],cache_note='Ortsdaten aus Cache (bis 7 Tage); keine gespeicherten Live-Preise',warnings=[]),local)
        try:
            html,stamp = self.http.get(destination['source'],context)
            parsed = self.parser.parse(html,destination,stamp)
            self.store.cache_set(key,parsed,stamp)
            return self._merge_local(dict(parsed,cache_note='Ortsdaten neu abgerufen',warnings=[]),local)
        except InterruptedError:
            raise
        except (OSError,ValueError) as exc:
            stale = self.store.cache_get(key)
            if stale:
                return self._merge_local(dict(stale[0],cache_note='Veraltete Ortsdaten: '+stale[1],warnings=[str(exc)]),local)
            snapshot = Path(__file__).parent/'data/place_snapshots.json'
            data = json.loads(snapshot.read_text()) if snapshot.exists() else {}
            if destination['name'] in data:
                snapshot_data=self.parser.migrate_snapshot(data[destination['name']])
                return self._merge_local(dict(snapshot_data,cache_note='Mitgelieferter Quellenstand vom 27.10.2026; möglicherweise veraltet',warnings=[str(exc)]),local)
            return self._merge_local(dict(lodgings=[],activities=[],cache_note='Keine Ortsdaten abrufbar',warnings=[str(exc)]),local)

    @staticmethod
    def _merge_local(data,local):
        if local:
            from ...core.planning.PlaceResearch import deduplicate
            for key in ('lodgings','activities'):data[key]=deduplicate(data.get(key,[])+local[key])
            data['cache_note']+=' · '+local['cache_note']
        return data

    def _inventory_places(self,destination):
        from ...core.planning.DestinationFeatures import feature_topics
        result=dict(lodgings=[],activities=[],warnings=[],cache_note='Lokale OSM-Merkmale; keine aktuelle Öffnungs- oder Verfügbarkeitsprüfung')
        for f in self.inventory.nearby(destination['latitude'],destination['longitude'],50,'features'):
            tags=f['tags']
            if tags.get('access') in ('no','private'):continue
            lodging_type={'hotel':'Hotel','guest_house':'Hotel','apartment':'Ferienwohnung','chalet':'Ferienwohnung','camp_site':'Camping'}.get(tags.get('tourism'))
            url=tags.get('website') or tags.get('contact:website') or f['source']
            if not url.startswith('https://'):url=f['source']
            item=dict(id=f['id'],name=f['name'],latitude=f['latitude'],longitude=f['longitude'],source=f['source'],url=url,
                retrieved_at=f['retrieved_at'],link_kind='OSM-Objekt / Anbieterinformation',data_status='Kartierter Eintrag; keine Verfügbarkeitszusage',
                source_updated='Stand des regionalen OSM-Abrufs',address=' '.join(tags[k] for k in ('addr:street','addr:housenumber','addr:postcode','addr:city') if tags.get(k)) or 'Koordinaten aus OSM; Anschrift nicht erfasst',
                wikidata_id=tags.get('wikidata',''),attributions=[{'label':'© OpenStreetMap-Mitwirkende · ODbL','url':'https://www.openstreetmap.org/copyright'}])
            country=tags.get('addr:country') or tags.get('is_in:country_code')
            country=country.strip().upper() if isinstance(country,str) and len(country.strip())==2 else None
            item.update(geo_source='OSM',country_code=country,administrative_region=tags.get('addr:state') or '')
            if lodging_type and (tags.get('name') or tags.get('name:de')):
                result['lodgings'].append(dict(item,type=lodging_type,amenities={},price={'label':'Unterkunft für Gruppe und Aufenthalt','low':None,'status':'unbekannt'},
                    booking_status='Kartierte Unterkunftsidentität; Belegung und Verfügbarkeit unbestätigt',rooms=None))
            topics=feature_topics(tags)
            if (tags.get('boundary')=='protected_area' or tags.get('leisure')=='nature_reserve') and tags.get('access') not in ('yes','permissive','designated'):
                # A habitat/protection zone is context, not evidence of a visitor activity.
                topics=[topic for topic in topics if topic not in ('Natur','Ruhe')]
            if topics:
                result['activities'].append(dict(item,type='OSM-Freizeitmerkmal',topics=topics,description='Kartiertes Angebot; aktuelle Öffnung, Saison und Zugang vor Ort prüfen.',
                    price_status='Preis nicht ermittelt; nicht als kostenlos bestätigt',duration='Dauer unbekannt'))
        return result

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
