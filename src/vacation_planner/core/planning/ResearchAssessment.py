"""Reviewed v1: limited culture evidence; no model scores or hard-filter effects."""
import copy
from datetime import datetime,timezone
import json
import math
import re
from urllib.parse import urlsplit
from .PlaceResearch import distance
from .RankingService import RankingService
from .DestinationFeatures import supplement_activities,request_profile


class RejectedEvidence(ValueError):pass


def name_key(value):return ' '.join(str(value).casefold().split())


def same_object(a,b):
    aa={str(a.get(k,'')) for k in ('id','wikidata_id')}-{''};bb={str(b.get(k,'')) for k in ('id','wikidata_id')}-{''}
    if aa&bb:return True
    return name_key(a.get('name'))==name_key(b.get('name')) and all(p.get(k) is not None for p in (a,b) for k in ('latitude','longitude')) and distance(a,b)<=.1


def assess_research(trip,request,now=None):
    """In-place only on newly built working trips; explicit opt-in required."""
    if not request.ai_discovery or trip.get('research_assessment'):return trip
    now=now or datetime.now(timezone.utc)
    before=trip['interest_match'];accepted=[];rejected=[]
    destination=trip['destination'];profile=request_profile(supplement_activities(destination,trip['activities']),request)
    existing=[p for rows in (profile or {}).get('evidence',{}).values() for p in rows]+trip['activities']
    evidence=trip.get('source_research',{}).get('evidence',[])
    blocked={e.get('subject',{}).get('id') for e in evidence if e.get('conflict') or (e.get('kind') in ('published_hours','access_note') and re.search(r'dauerhaft geschlossen|permanent(?:ly)? closed|auf unbestimmte zeit geschlossen',e.get('quote',''),re.I))}
    for e in evidence:
        reason=None
        try:
            if e['kind']!='listing' or e['subject']['id'] in blocked or e.get('conflict') or e['target_id']!=destination['id']:raise RejectedEvidence('Aussageart, Konflikt oder Zielzuordnung nicht freigegeben')
            if not request.interests.get('Kultur'):raise RejectedEvidence('Kein ausdrücklich gewähltes Kulturinteresse')
            p=json.loads(e['quote']);identity=e['identity'];subject=e['subject'];point=subject['coordinates']
            if urlsplit(e['source_url']).scheme!='https' or urlsplit(e['source_url']).hostname!='de.wikivoyage.org':raise RejectedEvidence('Quellenherkunft nicht freigegeben')
            if p['name']!=subject['name'] or p['country']!=destination['code'] or p['location_qid']!=identity['qid'] or p['country']!=identity['country'] or not set(p['type'])&{'museum','gallery','castle'} or not set(p['group'])&{'see','do'}:raise RejectedEvidence('Strukturierter Kultur-Nachweis nicht passend')
            if not all(type(point[k]) in (int,float) and math.isfinite(point[k]) for k in ('latitude','longitude')) or not -90<=point['latitude']<=90 or not -180<=point['longitude']<=180:raise RejectedEvidence('Ungültige Nachweis-Koordinaten')
            if p['latitude']!=point['latitude'] or p['longitude']!=point['longitude']:raise RejectedEvidence('Nachweis-Koordinaten widersprechen sich')
            stamp=datetime.fromisoformat(e.get('last_seen_at') or e['retrieved_at'])
            age=(now-stamp).total_seconds()
            if not 0<=age<=30*86400:raise RejectedEvidence('Alter oder unbekannter/falscher Quellenstand')
            if distance(destination,point)>min(3,float(request.activity_radius_km),float('inf') if request.surroundings else 2):raise RejectedEvidence('Außerhalb des freigegebenen Kulturumkreises')
            proof=dict(id=subject['id'],name=subject['name'],**point,source=e['source_url'],retrieved_at=e['retrieved_at'],distance_km=distance(destination,point),
                distance_kind='Luftlinie zum Quelleneintrag',access_status='Quelleintrag; aktuelle Öffnung und Zugang ungeprüft',evidence_kind='source_listing_v1',source_evidence_id=e['id'])
            if any(same_object(proof,p) for p in existing+accepted):raise RejectedEvidence('Doppelter Eintrag/gemeinsame Objektidentität; kein mehrfacher Beitrag')
            if len(accepted)>=3:raise RejectedEvidence('Sättigung bei drei zusätzlichen Kulturidentitäten')
            accepted.append(proof)
        except RejectedEvidence as exc:reason=str(exc)
        except (ValueError,TypeError,KeyError,OverflowError):reason='Nicht freigegebener, alter, unpassender oder doppelter Nachweis'
        if reason:rejected.append(dict(id=e.get('id'),reason=reason))
    signal=min(.25,len(accepted)*.1)
    raw=before
    if accepted:
        if profile is None:
            # No profile-based baseline: only bounded lower-bound culture signal,
            # never replace stronger existing editorial/guide evidence.
            total=sum(request.interests.values())
            raw=max(before,signal*request.interests.get('Kultur',0)/total) if total else before
        else:
            augmented=copy.deepcopy(profile)
            augmented['strengths']['Kultur']=max(augmented['strengths'].get('Kultur',0),signal)
            augmented.setdefault('evidence',{}).setdefault('Kultur',[]).extend(accepted)
            raw=RankingService.interest_match(dict(destination,feature_profile=augmented),request)
    after=min(before+.05,max(before,raw))
    trip['interest_match']=after
    trip['research_assessment']=dict(version=1,before=before,raw_after=raw,after=after,delta=after-before,signal=signal,
        accepted=accepted,rejected=rejected,rule='Nur zugeordnete frische Kultur-Einträge; höchstens 0,25 Signal und absolut 0,05 Interessenanstieg. Keine Öffnungs-/Qualitätszusage. Andere Themen ohne neue Wirkung.')
    if after>before:
        culture=trip.setdefault('interest_evidence',{}).setdefault('Kultur',dict(editorial=False,local=0,vicinity=0,confidence=0,explanation='',sources=[],evidence=[]))
        culture.setdefault('evidence',[]).extend(accepted);culture['sources']=list(dict.fromkeys(culture.get('sources',[])+[p['source'] for p in accepted]))
        culture['explanation']+=' · Zusätzliche zugeordnete Kultur-Quelleneinträge, begrenzt bewertet; keine Öffnungs-/Qualitätszusage.'
        culture['source_listing_count']=len(accepted)
        culture['status']='evidence_present';culture['confidence']=max(culture.get('confidence',0),.25)
        trip['evidence_confidence']=sum(v.get('confidence',0) for v in trip['interest_evidence'].values())/len(trip['interest_evidence'])
        trip['explanation']+=' · '+trip['research_assessment']['rule']
    RankingService.recompute(trip)
    return trip
