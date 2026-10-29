"""Read a downloaded regional PBF locally; retain only the requested small area."""
import math


def extract_features(path,bounds,context,emit=lambda *a:None):
    try:import osmium
    except ImportError:raise ValueError('Für regionale PBF-Dateien bitte die Projektabhängigkeiten aus requirements.txt installieren.') from None
    from ...core.planning.DestinationFeatures import feature_topics
    south,west,north,east=bounds;rows=[];way_centers={};seen=0
    def inside(lat,lon):return south<=lat<=north and west<=lon<=east
    def wanted(tags):
        return bool(feature_topics(tags)) or tags.get('tourism') in ('hotel','guest_house','apartment','chalet','camp_site') or tags.get('place') in ('town','village','hamlet') or tags.get('natural') in ('water','peak','ridge')
    class Handler(osmium.SimpleHandler):
        def check(self):
            nonlocal seen
            seen+=1
            if seen%10000==0:context.check()
            if seen%500000==0:emit('phase',f'Regionalauszug lokal lesen: {seen:,} Objekte geprüft, {len(rows)} Merkmale im Ausschnitt.')
        def node(self,n):
            self.check()
            if not n.location.valid() or not inside(n.location.lat,n.location.lon):return
            tags=dict(n.tags)
            if wanted(tags):rows.append({'type':'node','id':n.id,'lat':n.location.lat,'lon':n.location.lon,'tags':tags})
        def way(self,w):
            self.check();points=[(n.lat,n.lon) for n in w.nodes if n.location.valid() and inside(n.lat,n.lon)]
            if not points:return
            lat=sum(p[0] for p in points)/len(points);lon=sum(p[1] for p in points)/len(points)
            way_centers[w.id]=(lat,lon);tags=dict(w.tags)
            if wanted(tags):rows.append({'type':'way','id':w.id,'center':{'lat':lat,'lon':lon},'tags':tags})
        def relation(self,r):
            self.check();tags=dict(r.tags)
            if not wanted(tags):return
            points=[way_centers[m.ref] for m in r.members if m.type=='w' and m.ref in way_centers]
            if points:rows.append({'type':'relation','id':r.id,'center':{'lat':sum(p[0] for p in points)/len(points),'lon':sum(p[1] for p in points)/len(points)},'tags':tags})
    context.check();handler=Handler()
    processor=osmium.FileProcessor(str(path)).with_locations().with_filter(osmium.filter.KeyFilter(
        'amenity','tourism','natural','leisure','boundary','historic','route','place','highway','landuse'))
    for obj in processor:
        if obj.is_node():handler.node(obj)
        elif obj.is_way():handler.way(obj)
        elif obj.is_relation():handler.relation(obj)
    context.check()
    return rows
