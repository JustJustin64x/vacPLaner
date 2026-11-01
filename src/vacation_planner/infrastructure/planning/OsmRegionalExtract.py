"""Two-pass PBF reader: retain untagged relation members and disk-backed locations.

Only derived, bounded geometries enter the local index. A map representative or
sampled vertex is never labelled a trailhead or a verified walking distance.
"""
import tempfile
from pathlib import Path


def extract_features(path,bounds,context,emit=lambda *a:None):
    import osmium
    from ...core.planning.DestinationFeatures import feature_topics
    south,west,north,east=bounds
    rows=[];relations={};needed=set();way_geometry={};node_geometry={};seen=0
    def inside(p):return south<=p[0]<=north and west<=p[1]<=east
    def wanted(tags):
        return bool(feature_topics(tags)) or tags.get('tourism') in ('hotel','guest_house','apartment','chalet','camp_site') or tags.get('place') in ('town','village','hamlet') or tags.get('natural') in ('water','peak','ridge') or tags.get('entrance') in ('yes','main') or tags.get('information') in ('guidepost','trailhead')
    def pack(points,complete=True):
        # Spatially distributed samples from the actual geometry, never clipped means.
        unique=list(dict.fromkeys(points));step=max(1,len(unique)//64)
        sample=unique[::step][:64]
        return dict(points=sample,bounds=[min(p[0] for p in unique),min(p[1] for p in unique),max(p[0] for p in unique),max(p[1] for p in unique)],
                    complete=complete,point_count=len(points),precision='sampled_geometry; Luftlinie, Zugang und Wegverlauf ungeprüft')
    def append(kind,identity,tags,geom,extra=None):
        points=geom['points'];local=[p for p in points if inside(p)]
        b=geom['bounds']
        if not local and not (b[0]<=north and b[2]>=south and b[1]<=east and b[3]>=west):return
        p=(local or points)[0]
        rows.append(dict(type=kind,id=identity,center=dict(lat=p[0],lon=p[1]),tags=tags,geometry=geom,**(extra or {})))
    context.check();emit('phase','Relationen und sämtliche benötigten Mitglieder bestimmen (erster Durchlauf).')
    for r in osmium.FileProcessor(str(path),entities=osmium.osm.RELATION):
        tags=dict(r.tags)
        relations[r.id]=(tags,[(m.type,m.ref,m.role) for m in r.members])
    roots={rid for rid,(tags,_) in relations.items() if wanted(tags)}
    pending=list(roots);visited=set()
    while pending:
        rid=pending.pop()
        if rid in visited:continue
        visited.add(rid)
        for kind,ref,role in relations.get(rid,({},[]))[1]:
            needed.add((kind,ref))
            if kind=='r':pending.append(ref)
    emit('phase','Wege und Flächen mit vollständigen Knotenreferenzen lesen (zweiter Durchlauf).')
    with tempfile.TemporaryDirectory(prefix='vacation-osm-') as folder:
        processor=osmium.FileProcessor(str(path)).with_locations('sparse_file_array,'+str(Path(folder)/'locations.idx'))
        # No tag filter: untagged relation members and all location references survive.
        for obj in processor:
            seen+=1
            if seen%10000==0:context.check()
            if seen%500000==0:emit('phase',f'{seen:,} Objekte geprüft; {len(rows):,} regionale Merkmale.')
            if obj.is_node():
                if not obj.location.valid():continue
                p=(obj.location.lat,obj.location.lon);tags=dict(obj.tags)
                if ('n',obj.id) in needed:node_geometry[obj.id]=pack([p])
                if inside(p) and wanted(tags):append('node',obj.id,tags,pack([p]))
            elif obj.is_way():
                tags=dict(obj.tags);required=('w',obj.id) in needed
                if not required and not wanted(tags):continue
                points=[(n.lat,n.lon) for n in obj.nodes if n.location.valid()]
                if not points:continue
                geom=pack(points,len(points)==len(obj.nodes))
                if required:way_geometry[obj.id]=geom
                if wanted(tags):append('way',obj.id,tags,geom,dict(closed=obj.is_closed()))
    def relation_geometry(rid,stack):
        if rid in stack:return None
        points=[];complete=True;members=relations.get(rid,({},[]))[1]
        for kind,ref,role in members:
            geom=way_geometry.get(ref) if kind=='w' else node_geometry.get(ref) if kind=='n' else relation_geometry(ref,stack|{rid})
            if geom:points.extend(geom['points']);complete &= geom['complete']
            else:complete=False
        return pack(points,complete) if points else None
    for rid in sorted(roots):
        context.check();tags,members=relations[rid];geom=relation_geometry(rid,set())
        if geom:append('relation',rid,tags,geom,dict(member_count=len(members),geometry_status='complete_references' if geom['complete'] else 'missing_members'))
    context.check();return rows
