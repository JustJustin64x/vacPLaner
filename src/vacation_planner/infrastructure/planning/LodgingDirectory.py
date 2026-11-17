"""Bounded cold-area supplement; directory data never becomes an offer."""
from urllib.parse import urlencode
from .ResearchHttp import ResearchHttp
from .LodgingSourcePolicy import LodgingDirectoryPolicy
from .TripStore import timestamp


class LodgingDirectory:
    ENDPOINT='https://ovp.dresel.systems/api/interpreter'
    def __init__(self,store):self.store=store

    def collect(self,destination,request,context):
        lat,lon=float(destination['latitude']),float(destination['longitude'])
        radius=min(50,float(request.lodging_radius_km)) if request.surroundings else min(2,float(request.lodging_radius_km))
        key=f'lodging-directory-dresel-v1:{lat:.5f}:{lon:.5f}:{radius:.3f}'
        cached=self.store.cache_get(key,7*86400)
        if cached:return dict(cached[0],cache_used=True)
        backoff=self.store.cache_get('lodging-directory-dresel-backoff-v1',900)
        if backoff:return dict(lodgings=[],coverage={'status':'source_error','reason':backoff[0]['reason'],'radius_km':radius,'retrieved_at':backoff[1]})
        if getattr(context,'lodging_directory_calls',0)>=2:
            return dict(lodgings=[],coverage={'status':'deferred_budget','radius_km':radius,'reason':'Zwei gezielte Verzeichnisversuche je Suche erreicht'})
        context.lodging_directory_calls=getattr(context,'lodging_directory_calls',0)+1
        query=(f'[out:json][timeout:10][maxsize:2000000];'
               f'nwr(around:{round(radius*1000)},{lat:.6f},{lon:.6f})'
               '["tourism"~"^(hotel|guest_house|apartment|chalet|camp_site|hostel|motel)$"];out center tags 500;')
        url=self.ENDPOINT+'?'+urlencode({'data':query})
        http=ResearchHttp(self.store,LodgingDirectoryPolicy(url))
        try:
            data,stamp=http.json(url,context)
            if not isinstance(data.get('elements'),list) or data.get('remark'):raise ValueError('Unvollständige Verzeichnisantwort')
            rows=[]
            from ...core.planning.PlaceResearch import distance
            for x in data['elements']:
                t=x.get('tags',{});point=x.get('center') or x
                kind={'hotel':'Hotel','guest_house':'Hotel','motel':'Hotel','apartment':'Ferienwohnung','chalet':'Ferienwohnung','camp_site':'Camping'}.get(t.get('tourism'))
                if not kind or not t.get('name') or point.get('lat') is None or point.get('lon') is None:continue
                item=dict(id='osm:'+x['type']+':'+str(x['id']),name=t['name'],latitude=point['lat'],longitude=point['lon'])
                if distance(destination,item)>radius:continue
                source='https://www.openstreetmap.org/'+x['type']+'/'+str(x['id'])
                rows.append(dict(item,type=kind,source=source,url=t.get('website') or t.get('contact:website') or source,
                    identity_tags=t,geo_source='OSM',country_code=t.get('addr:country'),administrative_region=t.get('addr:state',''),
                    address=' '.join(t.get(k,'') for k in ('addr:street','addr:housenumber','addr:postcode','addr:city')).strip() or 'Anschrift unbekannt',
                    retrieved_at=stamp,source_updated='OSM-Verzeichnisabruf, keine Preisprüfung',amenities={},rooms=None,
                    link_kind='Kartierter Website-Hinweis',data_status='Verzeichniseintrag; Identität/Verfügbarkeit zu prüfen',
                    booking_status='Noch keine Angebotsprüfung',price={'label':'Unterkunft für Gruppe und Aufenthalt','low':None,'status':'unbekannt'},
                    attributions=[{'label':'© OpenStreetMap-Mitwirkende · ODbL','url':'https://www.openstreetmap.org/copyright'}]))
            result={'lodgings':rows,'coverage':{'status':'partial' if len(data['elements'])>=500 else 'directory_response',
                    'source':self.ENDPOINT,'retrieved_at':stamp,'radius_km':radius,
                    'returned':len(data['elements']),'note':'Europa-Bestand dieses Servers; OSM-Kartierung unvollständig; maximal 500 Quellelemente, keine Markt-/Preisvollständigkeit'}}
            self.store.cache_set(key,result,stamp);return result
        except InterruptedError:raise
        except (OSError,ValueError) as exc:
            self.store.cache_set('lodging-directory-dresel-backoff-v1',{'reason':str(exc)},timestamp())
            return dict(lodgings=[],coverage={'status':'source_error','radius_km':radius,'reason':str(exc),
                        'source':self.ENDPOINT,'retrieved_at':timestamp()})
