"""Bounded map evidence and explicit unknowns, never a POI popularity ranking."""
from .PlaceResearch import distance, deduplicate

TOPICS=('Wandern','Baden','Natur','Ruhe','Kultur','Feiern','Barhopping','Restaurants','Berge')


def spatial_distance(base,feature):
    if feature.get('_distance_origin')==[base['latitude'],base['longitude']]:return feature['_query_distance_km']
    points=(feature.get('geometry') or {}).get('points') or []
    return min((distance(base,dict(latitude=p[0],longitude=p[1])) for p in points),default=distance(base,feature))


def feature_topics(tags):
    if tags.get('access') in ('no','private') or tags.get('disused')=='yes' or tags.get('abandoned')=='yes':return []
    topics=[]
    if tags.get('route')=='hiking' and tags.get('type')=='route':topics+=['Wandern']
    if tags.get('leisure') in ('nature_reserve','park') or tags.get('boundary') in ('national_park','protected_area'):topics+=['Natur']
    if tags.get('swimming')!='no' and (tags.get('leisure') in ('swimming_area','water_park') or tags.get('sport')=='swimming' or tags.get('natural')=='beach'):topics+=['Baden']
    if tags.get('tourism') in ('museum','gallery','artwork','attraction') or tags.get('historic') in ('castle','archaeological_site','monument','ruins'):topics+=['Kultur']
    if tags.get('amenity')=='nightclub':topics+=['Feiern']
    if tags.get('amenity') in ('bar','pub'):topics+=['Barhopping']
    if tags.get('amenity')=='restaurant':topics+=['Restaurants']
    if tags.get('natural') in ('peak','ridge'):topics+=['Berge']
    return list(dict.fromkeys(topics))


def _bar_cluster(bars):
    # A compact walkable-looking group, not bars scattered across a 4 km diameter.
    # Walking connectivity and opening times still need verification.
    if len(bars)<2:return bars
    best=[]
    for bar in bars[:200]:
        group=[b for b in bars if distance(bar,b)<=.8]
        if len(group)>len(best):best=group
        if len(best)>=6:break
    return best


def feature_profile(features,base,coverage):
    evidence={};counts={};landscapes=[];bars=[];distances={};primary={}
    features=deduplicate(features)
    distances={f['id']:spatial_distance(base,f) for f in features}
    for f in features:
        if 'Barhopping' in feature_topics(f.get('tags',{})) and distances[f['id']]<=2:bars.append(f)
    clustered={f['id'] for f in _bar_cluster(bars)}
    for f in sorted(features,key=lambda f:(distances[f['id']],f['id'])):
        tags=f.get('tags',{});km=distances[f['id']]
        for topic in feature_topics(tags):
            radius={'Barhopping':2,'Feiern':3,'Kultur':3,'Restaurants':3,'Wandern':10,'Baden':8}.get(topic,15)
            if km>radius or (topic=='Barhopping' and f['id'] not in clustered):continue
            counts[topic]=counts.get(topic,0)+1;evidence.setdefault(topic,[])
            if len(evidence[topic])<6:
                geometry=f.get('geometry') or {}
                evidence[topic].append(dict(id=f['id'],name=f['name'],source=f['source'],retrieved_at=f['retrieved_at'],distance_km=round(km,2),
                    distance_kind='Luftlinie zu Stichproben der Geometrie' if geometry.get('points') else 'Luftlinie zum repräsentativen Kartenpunkt',
                    access_status='Zugang und tatsächlicher Weg ungeprüft',geometry_complete=geometry.get('complete'),
                    latitude=f['latitude'],longitude=f['longitude'],difficulty=tags.get('sac_scale') or tags.get('difficulty') or 'unbekannt',route_ref=tags.get('ref','')))
        if km<=3 and 'Kultur' in feature_topics(tags) and (tags.get('tourism') in ('museum','gallery') or tags.get('historic') in ('castle','archaeological_site','ruins')):
            primary.setdefault('Kultur',[]).append(dict(latitude=f['latitude'],longitude=f['longitude'],cultural_anchor=True,named=bool(tags.get('name') or tags.get('name:de')),id=f['id'],name=f['name'],source=f['source'],retrieved_at=f['retrieved_at'],distance_km=round(km,2),distance_kind='Luftlinie zum Kartenobjekt; Geometrie gegebenenfalls vereinfacht',access_status='Zugang und tatsächlicher Weg ungeprüft',geometry_complete=(f.get('geometry') or {}).get('complete')))
        if km<=15 and (tags.get('natural') in ('water','beach') or tags.get('leisure')=='swimming_area'):landscapes.append('See/Küste')
        if km<=15 and (tags.get('natural') in ('peak','ridge') or tags.get('boundary')=='national_park'):landscapes.append('Berge/Natur')
    thresholds={'Wandern':4,'Baden':3,'Natur':3,'Ruhe':3,'Kultur':5,'Feiern':3,'Barhopping':4,'Restaurants':4,'Berge':4}
    strengths={k:min(1,n/thresholds[k]) for k,n in counts.items()}
    for k in ('Wandern','Feiern','Barhopping'):
        if counts.get(k)==1:strengths[k]=.15
    if 'Barhopping' in strengths:strengths['Barhopping']=min(.65,strengths['Barhopping'])
    if 'Wandern' in strengths:strengths['Wandern']=min(.7,strengths['Wandern'])
    if 'Baden' in strengths:
        strengths['Baden']=min(.8 if any(f.get('tags',{}).get('leisure') in ('swimming_area','water_park') or f.get('tags',{}).get('swimming')=='yes' for f in features if distances[f['id']]<=8 and 'Baden' in feature_topics(f.get('tags',{}))) else .6,strengths['Baden'])
        if all(p['distance_km']>5 for p in evidence['Baden']):strengths['Baden']=min(.4,strengths['Baden'])
    if 'Kultur' in strengths and not any(f.get('tags',{}).get('tourism') in ('museum','gallery') or f.get('tags',{}).get('historic') in ('castle','archaeological_site','ruins') for f in features if distances[f['id']]<=3 and 'Kultur' in feature_topics(f.get('tags',{}))):strengths['Kultur']=min(.35,strengths['Kultur'])
    if 'Wandern' in strengths and any(p['geometry_complete'] is not True for p in evidence['Wandern']):strengths['Wandern']=min(.4,strengths['Wandern'])
    if base.get('type') in ('Großstadt','Klein-/Mittelstadt'):
        strengths['Städte']=1 if base['type']=='Großstadt' else .6;counts['Städte']=1
        evidence['Städte']=[dict(id=base['id'],name=base['name'],source=base['source'],retrieved_at=base.get('source_checked_at',''),distance_km=0)]
    categories={}
    for topic in TOPICS:
        queried=[c for c in coverage if topic in c.get('categories',TOPICS)]
        categories[topic]='evidence_present' if counts.get(topic) else 'observed_no_matches' if queried and any(c.get('radius_complete') for c in queried) else 'partial' if queried else 'not_investigated'
        if topic=='Ruhe':categories[topic]='not_investigated' # no measured noise or verified quietness
    for topic,proof in primary.items():
        merged={}
        for p in sorted(proof,key=lambda p:(not p.get('named'),p['distance_km']))[:2]+evidence.get(topic,[]):merged.setdefault(p['id'],p)
        evidence[topic]=list(merged.values())[:6]
    if counts.get('Städte'):categories['Städte']='evidence_present'
    return dict(strengths=strengths,counts=counts,evidence=evidence,coverage='regional' if coverage else 'unknown',
        category_status=categories,regions=[x.get('name') for x in coverage],landscapes=list(dict.fromkeys(landscapes)),
        limitations='Kartierung ist keine Vollerhebung. Öffnung, Saison, Fußwege, Wander-Eignung und Ruhe bleiben ungeprüft. Grünflächen belegen keine Ruhe; Gewässer keine Badestelle. Unbekannt erhält keinen Eignungsbonus.')


def evidence_score(destination,request):
    profile=request_profile(destination,request)
    if profile is None:return None
    total=sum(request.interests.values())
    if not total:return .5
    aliases={'Natur und Ruhe':'Ruhe','Nachtleben':'Feiern','Kultur und Sehenswürdigkeiten':'Kultur'}
    values=[(weight,profile['strengths'].get(aliases.get(topic,topic),0)) for topic,weight in request.interests.items() if weight]
    average=sum(w*v for w,v in values)/total
    # Combinations require both interests nearby; one abundant category cannot substitute.
    score=.6*average+.4*min(v for _,v in values) if len(values)>1 else average
    if request.interests.get('Kultur') and (request.interests.get('Feiern') or request.interests.get('Barhopping')) and not evening_cluster(profile):score=min(.45,score)
    return score


def request_profile(destination,request):
    """Reduce evidence to the requested radius without inventing missing entries."""
    source=destination.get('feature_profile')
    if source is None:return None
    radius=float(request.activity_radius_km) if request.surroundings else min(2,float(request.activity_radius_km))
    result=dict(source,strengths=dict(source['strengths']),counts=dict(source.get('counts',{})),evidence={})
    for topic,proof in source.get('evidence',{}).items():
        kept=[p for p in proof if p.get('distance_km',float('inf'))<=radius]
        result['evidence'][topic]=kept
        topic_radius={'Barhopping':2,'Feiern':3,'Kultur':3,'Restaurants':3,'Wandern':10,'Baden':8}.get(topic,15)
        if radius<topic_radius:
            result['counts'][topic]=len(kept)
            result['strengths'][topic]=source['strengths'].get(topic,0)*len(kept)/max(1,len(proof))
    return result


def evening_cluster(profile):
    culture=profile.get('evidence',{}).get('Kultur',[])
    anchors=[p for p in culture if p.get('cultural_anchor')]
    evening=profile.get('evidence',{}).get('Feiern',[])+profile.get('evidence',{}).get('Barhopping',[])
    return any(distance(a,b)<=1.5 for a in (anchors or culture) for b in evening if all(p.get(k) is not None for p in (a,b) for k in ('latitude','longitude')))


def supplement_activities(destination,activities):
    """Keep source-verified guide entries useful even with an empty OSM profile.

    A bounded hint (max .4) never substitutes for a strong mapped/verified offer.
    Unlocated entries, OSM duplicates and unmeasured quietness are excluded.
    """
    source=destination.get('feature_profile')
    if source is None or not activities:return destination
    activities=deduplicate([a for a in activities if a.get('geo_source')!='OSM' and not a.get('id','').startswith('osm:')])
    if not activities:return destination
    profile=dict(source,strengths=dict(source['strengths']),counts=dict(source['counts']),evidence={k:list(v) for k,v in source['evidence'].items()},category_status=dict(source.get('category_status',{})))
    for topic in TOPICS:
        if topic=='Ruhe':continue
        radius={'Barhopping':2,'Feiern':3,'Kultur':3,'Restaurants':3,'Wandern':10,'Baden':8}.get(topic,15)
        hits=[a for a in activities if topic in a.get('topics',[]) and a.get('geo_source')!='OSM' and not a.get('id','').startswith('osm:') and a.get('source') and a.get('distance_km') is not None and a['distance_km']<=radius and all(a.get(k) is not None for k in ('latitude','longitude'))]
        if topic=='Barhopping':hits=_bar_cluster(hits)
        if not hits:continue
        value=min(.4,len(hits)/5)
        if len(hits)==1 and topic in ('Wandern','Feiern','Barhopping'):value=.15
        if value<=profile['strengths'].get(topic,0):continue
        profile['strengths'][topic]=value;profile['counts'][topic]=len(hits)
        profile['category_status'][topic]='evidence_present'
        profile['evidence'][topic]=[dict(id=a.get('id') or a['source']+'#'+a['name'],name=a['name'],source=a['source'],retrieved_at=a.get('retrieved_at',''),latitude=a['latitude'],longitude=a['longitude'],distance_km=round(a['distance_km'],2),distance_kind=a.get('distance_kind','Luftlinie'),access_status='Quelleneintrag; Öffnung und Zugang ungeprüft',geometry_complete=None,evidence_kind='guide_entry') for a in hits[:6]]
    return dict(destination,feature_profile=profile)
