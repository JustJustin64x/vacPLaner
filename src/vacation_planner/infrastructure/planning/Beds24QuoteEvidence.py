"""Source-scoped room/rate evidence; unknown prose never becomes a guarantee."""
import re
from datetime import date,timedelta,datetime
from zoneinfo import ZoneInfo
from bs4 import BeautifulSoup
from ...core.planning.ChildAgeRange import ChildAgeRange


def bounded_text(node,maximum):
    if node is None:return '',False
    for n in node.select('script,style,nav'):n.decompose()
    text=' '.join(node.get_text(' ',strip=True).split())
    return text[:maximum],len(text)>maximum


def child_age_contract(html,query):
    if not query.children_ages:return None
    soup=BeautifulSoup(html,'html.parser');ranges=[]
    for control in soup.select('form#formlook [name="numchild"],form#formlook [name^="ncc"]'):
        labels=[control.get('aria-label',''),control.get('title','')]
        if control.get('id'):labels += [n.get_text(' ',strip=True) for n in soup.find_all('label',attrs={'for':control['id']})]
        for label in labels:
            policy=ChildAgeRange.parse(label)
            if policy:ranges.append(policy)
    bounds={(r.minimum,r.maximum) for r in ranges}
    if len(bounds)!=1 or not ranges[0].accepts(query.children_ages):
        raise ValueError('Veröffentlichte Kinder-Altersgruppe fehlt, widerspricht sich oder passt nicht; keine Ersatzsuche für Erwachsene')
    return ranges[0].to_dict()


def unnegated(text,pattern):
    for match in re.finditer(pattern,text,re.I):
        before=text[max(0,match.start()-24):match.start()]
        if not re.search(r'\b(?:kein(?:e[nsrm]?)?|nicht|ohne|not|no|without)\s*(?:ein(?:e[nsrm]?)?\s*)?$',before,re.I):return True
    return False


def room_facts(room_text,tariff_text,start,now=None):
    facts={};proof={}
    private=unnegated(room_text,r'eigen(?:es|em|en)\s+(?:bad|badezimmer)|private\s+bathroom|en[- ]?suite(?:\s+bathroom)?')
    shared=unnegated(room_text,r'gemeinschaftsbad|shared\s+bathroom|gemeinsames\s+badezimmer') or bool(re.search(r'kein\s+eigenes\s+bad|ohne\s+eigenes\s+bad|no\s+private\s+bathroom',room_text,re.I))
    clauses=lambda text:[x.strip(' .!') for x in re.split(r'[;\n.!]',text) if x.strip()]
    private_hint=private
    private=private and any(re.fullmatch(r'(?:eigenes (?:Bad|Badezimmer)|private bathroom|en[- ]?suite(?: bathroom)?)',c,re.I) for c in [room_text.strip(' .!')])
    if private!=shared and not (shared and private_hint):facts['Eigenes Bad']=private;proof['Eigenes Bad']=room_text
    breakfast=unnegated(tariff_text,r'frühstück\s+(?:ist\s+)?(?:inklusive|inbegriffen|enthalten)|breakfast\s+included')
    excluded=bool(re.search(r'frühstück\s+(?:ist\s+)?nicht\s+(?:enthalten|inbegriffen)|ohne\s+frühstück|breakfast\s+not\s+included',tariff_text,re.I))
    breakfast_hint=breakfast
    breakfast=breakfast and any(re.fullmatch(r'(?:Frühstück (?:ist )?(?:inklusive|inbegriffen|enthalten)|Breakfast included)',c,re.I) for c in [tariff_text.strip(' .!')])
    if breakfast!=excluded and not (excluded and breakfast_hint):facts['Frühstück']=breakfast;proof['Frühstück']=tariff_text
    nonref=bool(re.search(r'nicht\s+erstattungsfähig|non[- ]?refundable|keine\s+(?:änderung\s+oder\s+)?stornierung|stornierung[^.]{0,70}nicht\s+(?:kostenlos|möglich)',tariff_text,re.I))
    free=unnegated(tariff_text,r'kostenlose?\s+stornierung|kostenlos\s+(?:möglich|stornierbar)|free\s+cancellation')
    if nonref and not free:facts['Kostenlose Stornierung']=False;proof['Kostenlose Stornierung']=tariff_text
    elif free and not nonref and not re.search(r'zubuchbar|optional|aufpreis|extra\s+charge',tariff_text,re.I):
        match=re.search(r'(?:bis|until)\s+(\d{1,3})\s+(?:tage|days)\s+(?:vor|before)\s+(?:anreise|arrival|check[- ]?in)',tariff_text,re.I)
        today=now or datetime.now(ZoneInfo('Europe/Berlin')).date()
        exact=any(re.fullmatch(r'(?:Kostenlose Stornierung|Free cancellation) (?:bis|until) \d{1,3} (?:Tage|days) (?:vor|before) (?:Anreise|arrival|check[- ]?in)',c,re.I) for c in [tariff_text.strip(' .!')])
        if match and exact:
            deadline=date.fromisoformat(start)-timedelta(days=int(match[1]))
            if today!=deadline:facts['Kostenlose Stornierung']=today<deadline;proof['Kostenlose Stornierung']=tariff_text
        elif any(re.fullmatch(r'jederzeit\s+kostenlos\s+stornierbar',c,re.I) for c in [tariff_text.strip(' .!')]):facts['Kostenlose Stornierung']=True;proof['Kostenlose Stornierung']=tariff_text
    return facts,proof


def inventory_evidence(html,room_id,offer_id,start):
    soup=html if isinstance(html,BeautifulSoup) else BeautifulSoup(html,'html.parser');room=soup.find(id='roomid'+room_id)
    tariff=soup.find(id='ajaxroomoffer'+offer_id+'-'+room_id)
    tariff_text,rate_truncated=bounded_text(tariff,3000)
    if room:
        room=BeautifulSoup(str(room),'html.parser')
        for n in room.select('[id^="ajaxroomoffer"],.b24-featurewell'):n.decompose()
        room=room.select_one('.b24-room-description,.b24-roomdesc,.at_roomdescription') or room
    room_text,room_truncated=bounded_text(room,2000)
    facts,proof=room_facts('' if room_truncated else room_text,'' if rate_truncated else tariff_text,start)
    features=[];features_truncated=False
    original=soup.find(id='roomid'+room_id)
    # Source-delivered, affirmative feature rows scoped to this physical room.
    # A property-wide footer cannot establish a selected room's bathroom/board.
    if original:
        feature_rows=original.select('.b24-featurewell p');features_truncated=len(feature_rows)>80
        for row in ([] if features_truncated else feature_rows):
            if row.select_one('.glyphicon-ok'):
                text=' '.join(row.get_text(' ',strip=True).split())
                if len(text)<=160:features.append(text)
    controlled={'Breakfast Included':('Frühstück',True),'Frühstück inklusive':('Frühstück',True),
                'Private Bathroom':('Eigenes Bad',True),'Eigenes Bad':('Eigenes Bad',True),
                'Shared Bathroom':('Eigenes Bad',False),'Gemeinschaftsbad':('Eigenes Bad',False)}
    declarations={}
    for label in features:
        if label in controlled:
            feature,val=controlled[label];declarations.setdefault(feature,[]).append((val,label))
    for feature,rows in declarations.items():
        values={value for value,_ in rows}
        if feature in facts:values.add(facts[feature])
        if len(values)>1:facts.pop(feature,None);proof.pop(feature,None)
        else:facts[feature]=rows[0][0];proof[feature]='Veröffentlichte Zimmerausstattung: '+', '.join(label for _,label in rows)
    return dict(room_id=room_id,offer_id=offer_id,room_text=room_text,tariff_text=tariff_text,
                room_text_truncated=room_truncated,tariff_text_truncated=rate_truncated,source_features=features,source_features_truncated=features_truncated,facts=facts,proof=proof)


def apply_room_evidence(offer,evidence):
    details=offer.details;properties=dict(details['property']);amenities=dict(properties.get('amenities',{}))
    # These features belong to this room/rate selection, never the whole hotel.
    for feature in ('Eigenes Bad','Frühstück','Kostenlose Stornierung'):
        values=[row.get('facts',{}).get(feature) for row in evidence]
        amenities.pop(feature,None)
        if values and any(v is False for v in values):amenities[feature]=False
        elif values and all(v is True for v in values):amenities[feature]=True
    properties['amenities']=amenities;details['property']=properties
    offer.evidence['selected_room_evidence']=evidence
