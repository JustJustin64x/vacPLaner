"""Score the broad geographic set before bounding expensive investigation."""
from .RankingService import RankingService
from .PlaceResearch import distance


def select_candidates(candidates,request,origin,context):
    scored=[];weights=request.normalized_weights();iw,tw=float(weights['Interessen']),float(weights['Reisezeit'])
    if not iw+tw:iw=tw=.5
    for index,d in enumerate(candidates):
        if index%250==0:context.check()
        km=distance(origin,d)
        if km<=5 or (request.max_distance_km and km>float(request.max_distance_km)):continue
        suitability=RankingService.interest_match(d,request)
        proximity=max(0,1-km/2000)
        # Interest evidence has first say; proximity breaks equally fitting groups.
        score=(suitability*iw+proximity*tw)/(iw+tw)
        scored.append((score,suitability,d))
    scored.sort(key=lambda x:(-x[0],-x[1],str(x[2].get('id',x[2]['source']))))
    # Bounded diversity step; complexity never quadratic in the imported country set.
    import math
    limit=max(request.candidate_pool*5,100);pool=[];cells={};included=set()
    for row in scored:
        d=row[2];cell=(math.floor(d['latitude']/.3),math.floor(d['longitude']/.3))
        if cells.get(cell,0)>=3:continue
        cells[cell]=cells.get(cell,0)+1;pool.append(row);included.add(d['source'])
        if len(pool)>=limit:break
    for row in scored:
        if len(pool)>=limit:break
        if row[2]['source'] not in included:pool.append(row);included.add(row[2]['source'])
    # Reserve bounded *research* opportunities with a known guide page when
    # suitability is still entirely unknown. No positive fit is manufactured.
    hints=[row for row in scored if row[1]==0 and row[2].get('wikivoyage_source')]
    for row in hints[:3]:
        if row[2]['source'] not in included:pool.append(row);included.add(row[2]['source'])
    explored=0
    selected=[];scores={d['source']:s for s,_,d in pool}
    while pool and len(selected)<request.candidate_pool:
        context.check()
        fitting=pool
        if any(request.interests.values()) and iw>0:
            strongest=max(row[1] for row in pool)
            fitting=[row for row in pool if row[1]>=strongest-.15]
        exploratory=[row for row in fitting if row[1]==0 and row[2].get('wikivoyage_source')] if explored<3 and max(row[1] for row in fitting)==0 else []
        best=max(exploratory or fitting,key=lambda row:(scores[row[2]['source']],row[1],str(row[2].get('id',''))))
        if exploratory:explored+=1
        pool.remove(best);suitability=best[1];d=best[2];selected.append(d)
        for _,fit,other in pool:
            # Diversity only among similarly fitting possibilities.
            if abs(fit-suitability)>.15:continue
            overlap=distance(d,other)
            same_area=same_holiday_region(d,other) or bool(d.get('area_id') and d.get('area_id')==other.get('area_id'))
            penalty=.32 if same_area else .16 if overlap<35 else .025 if d['code']==other['code'] else 0
            scores[other['source']]-=penalty
    return selected,{'geographic_considered':len(scored),'with_interest_evidence':sum(any(n and (not any(request.interests.values()) or request.interests.get(k,0)) for k,n in d.get('feature_profile',{}).get('counts',{}).items()) for _,_,d in scored),
        'features_unknown':sum(not d.get('feature_profile') or d['feature_profile'].get('coverage')=='unknown' for _,_,d in scored),'deep_candidates':len(selected),'source_guided_unknown_research':explored}


def same_holiday_region(a,b):
    """Geography and shared evidence cross national borders; admin codes don't."""
    km=distance(a,b)
    if km<8:return True
    if km>60:return False
    def identities(d):return {p['id'] for rows in d.get('feature_profile',{}).get('evidence',{}).values() for p in rows}
    x,y=identities(a),identities(b);shared=len(x&y)
    if shared>=2 and shared/max(1,min(len(x),len(y)))>=.5:return True
    regions_a={r['id'] for r in a.get('tourist_regions',[])}
    regions_b={r['id'] for r in b.get('tourist_regions',[])}
    return km<30 and bool(regions_a&regions_b) and shared>=1
