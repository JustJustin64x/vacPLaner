"""Evidence, coverage and saturation instead of population or raw POI popularity."""
from .PlaceResearch import distance, deduplicate


def feature_topics(tags):
    if tags.get('access') in ('no','private') or tags.get('disused')=='yes':return []
    topics=[]
    if tags.get('route')=='hiking' and tags.get('type')=='route':topics+=['Wandern']
    if tags.get('leisure') in ('nature_reserve','park') or tags.get('boundary') in ('national_park','protected_area'):topics+=['Natur','Ruhe']
    if tags.get('leisure') in ('swimming_area','water_park') or tags.get('sport')=='swimming' or (tags.get('natural')=='beach' and tags.get('swimming')!='no'):topics+=['Baden']
    if tags.get('tourism') in ('museum','gallery','artwork','attraction') or tags.get('historic') in ('castle','archaeological_site','monument','ruins'):topics+=['Kultur']
    if tags.get('amenity')=='nightclub':topics+=['Feiern']
    if tags.get('amenity') in ('bar','pub'):topics+=['Barhopping']
    if tags.get('amenity')=='restaurant':topics+=['Restaurants']
    if tags.get('natural') in ('peak','ridge'):topics+=['Berge']
    return list(dict.fromkeys(topics))


def feature_profile(features,base,coverage):
    evidence={};counts={};landscapes=[]
    for f in deduplicate(features):
        tags=f.get('tags',{})
        for topic in feature_topics(tags):
            radius={'Barhopping':2,'Feiern':5,'Kultur':5,'Restaurants':3,'Ruhe':5}.get(topic,15)
            if distance(base,f)>radius:continue
            counts[topic]=counts.get(topic,0)+1
            evidence.setdefault(topic,[])
            if len(evidence[topic])<6:evidence[topic].append({'id':f['id'],'name':f['name'],'source':f['source'],'retrieved_at':f['retrieved_at'],'distance_km':round(distance(base,f),1)})
        if tags.get('natural') in ('water','beach') or tags.get('leisure')=='swimming_area':landscapes.append('See/Küste')
        if tags.get('natural') in ('peak','ridge') or tags.get('boundary')=='national_park':landscapes.append('Berge/Natur')
    thresholds={'Wandern':4,'Baden':3,'Natur':3,'Ruhe':3,'Kultur':5,'Feiern':3,'Barhopping':4,'Restaurants':4,'Berge':4}
    strengths={k:min(1,n/thresholds[k]) for k,n in counts.items()}
    if base.get('type') in ('Großstadt','Klein-/Mittelstadt'):
        strengths['Städte']=1 if base['type']=='Großstadt' else .6;counts['Städte']=1
        evidence['Städte']=[{'id':base['id'],'name':base['name'],'source':base['source'],'retrieved_at':base.get('source_checked_at',''),'distance_km':0}]
    # A single trail/club/bar is evidence, not a destination-wide recommendation.
    for k in ('Wandern','Feiern','Barhopping'):
        if counts.get(k)==1:strengths[k]=.15
    if 'Ruhe' in strengths:
        strengths['Ruhe']*=.65  # Nature mapping is a proxy, never a noise measurement.
        if counts.get('Feiern',0)>=2 or counts.get('Barhopping',0)>=8:strengths['Ruhe']*=.4
    return {'strengths':strengths,'counts':counts,'evidence':evidence,'coverage':'regional' if coverage else 'unknown',
            'regions':[x.get('name') for x in coverage], 'landscapes':list(dict.fromkeys(landscapes)),
            'limitations':'Karteneinträge belegen weder aktuelle Öffnung noch Saison, Zugänglichkeit oder gemessene Ruhe. Fehlende Merkmale sind unbekannt.'}


def evidence_score(destination,request):
    profile=destination.get('feature_profile')
    if profile is None:return None
    total=sum(request.interests.values())
    if not total:return .5
    aliases={'Natur und Ruhe':'Ruhe','Nachtleben':'Feiern','Kultur und Sehenswürdigkeiten':'Kultur'}
    # Unknown is deliberately not given a default suitability bonus.
    return sum(weight*profile['strengths'].get(aliases.get(topic,topic),0) for topic,weight in request.interests.items())/total
