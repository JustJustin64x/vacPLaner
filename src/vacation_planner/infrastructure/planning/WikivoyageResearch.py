"""Source-specific extraction from exact Wikimedia identities, no general crawl."""
import json
import math
import re
import unicodedata
from urllib.parse import quote,urlsplit,unquote
from bs4 import BeautifulSoup
from ...core.planning.PlaceResearch import distance
from ...core.planning.SourceEvidence import evidence_id,LIMITATION

TOPIC_TYPES={'Kultur':{'museum','gallery','castle','church','palace','monument','archaeological_site'},
 'Natur':{'lake','park','forest','waterfall','nature_reserve','national_park','viewpoint'},
 'Berge':{'mountain','peak'},'Baden':{'swimming','swimming_pool','bathing','lido','public_bath','beach'},
 'Wandern':{'hiking','hiking_trail','walking_trail','nature_trail'},
 'Feiern':{'bar','pub','nightclub','disco','club','dance_club'},'Barhopping':{'bar','pub'},'Restaurants':{'restaurant','cafe'}}


def normal(value):return ' '.join(unicodedata.normalize('NFKC',str(value)).casefold().split())


def clean(node):
    if node is None:return ''
    # Complete field only. Never sever its negation or trailing qualification.
    clone=BeautifulSoup(str(node),'html.parser')
    for tag in clone.select('script,style,nav,button,.voy-listing-edit-buttons'):tag.decompose()
    return ' '.join(clone.get_text(' ',strip=True).split())


def values(entity,prop):
    rows=entity.get('claims',{}).get(prop,[])
    rows=[r for r in rows if r.get('rank')!='deprecated' and r.get('mainsnak',{}).get('snaktype')=='value']
    preferred=[r for r in rows if r.get('rank')=='preferred'];rows=preferred or rows
    return [r['mainsnak']['datavalue']['value'] for r in rows if 'datavalue' in r['mainsnak']]


def coordinates(lat,lon):
    lat,lon=float(lat),float(lon)
    if not math.isfinite(lat) or not math.isfinite(lon) or not -90<=lat<=90 or not -180<=lon<=180:raise ValueError('Ungültige Quellenkoordinaten.')
    return dict(latitude=lat,longitude=lon)


def page_identity(body,destination):
    soup=BeautifulSoup(body,'html.parser');geo=soup.select_one('#voy-geo-indicator[data-lat][data-lon]')
    link=soup.select_one('#t-wikibase a[href]')
    if geo is None or link is None:raise ValueError('Artikel enthält keine eindeutige Ortsidentität/Geoangabe.')
    m=re.fullmatch(r'https://www\.wikidata\.org/wiki/(?:Special:EntityPage/)?(Q[1-9]\d*)',link['href'])
    if not m:raise ValueError('Keine erlaubte verknüpfte Wikidata-Identität.')
    point=coordinates(geo['data-lat'],geo['data-lon'])
    if geo.get('data-country')!=destination.get('code') or distance(destination,point)>5:raise ValueError('Land oder Artikelkoordinaten passen nicht zum ausgewählten Ort.')
    return soup,dict(qid=m[1],point=point,country=geo.get('data-country'))


def confirm_identity(page,destination,entity,country):
    qid=page['qid']
    if entity.get('id')!=qid:raise ValueError('Wikidata-Antwort gehört zu einem anderen Ort.')
    existing=destination.get('wikidata_id') or (destination.get('id') if re.fullmatch(r'Q\d+',str(destination.get('id',''))) else None)
    if existing and existing!=qid:raise ValueError('Vorhandene und recherchierte Wikidata-Identität widersprechen sich.')
    names={normal(x) for x in [destination.get('name',''),destination.get('base_name','')]+destination.get('aliases',[]) if x}
    labels=[v['value'] for k,v in entity.get('labels',{}).items() if k in ('de','en')]
    labels += [v['value'] for k,rows in entity.get('aliases',{}).items() if k in ('de','en') for v in rows]
    if not names & {normal(x) for x in labels}:raise ValueError('Ortsbezeichnung nicht durch Wikidata-Identität bestätigt.')
    points=values(entity,'P625')
    if len(points)!=1 or points[0].get('globe')!='http://www.wikidata.org/entity/Q2':raise ValueError('Keine eindeutigen irdischen Wikidata-Koordinaten.')
    point=coordinates(points[0]['latitude'],points[0]['longitude'])
    if distance(destination,point)>5 or distance(page['point'],point)>3:raise ValueError('Wikidata-Koordinaten widersprechen der Ortszuordnung.')
    countries=values(entity,'P17')
    if len(countries)!=1 or countries[0].get('id')!=country.get('id') or values(country,'P297')!=[destination.get('code')]:raise ValueError('Land nicht unabhängig über ISO-Code zugeordnet.')
    gn=destination.get('geonames_id')
    if gn and values(entity,'P1566') and str(gn) not in values(entity,'P1566'):raise ValueError('GeoNames-Identität widerspricht der Recherche.')
    return dict(qid=qid,country=destination['code'],coordinates=point,wikidata_url='https://www.wikidata.org/wiki/'+qid,
        method='Artikel-Land/Koordinaten und verknüpfte Wikidata-Identität mit Länder-ISO-Code geprüft',
        source_revision=entity.get('lastrevid'),revision_modified_at=entity.get('modified'),independent_truth_confirmation=False)


def extract(soup,destination,request,identity,response):
    result=[];gaps=[]
    topics={k for k,v in request.get('interests',{}).items() if v and k in TOPIC_TYPES}
    unsupported=[k for k,v in request.get('interests',{}).items() if v and k not in TOPIC_TYPES]
    if unsupported:gaps.append('Keine neue gesicherte Auswertung für: '+', '.join(unsupported)+'.')
    radius=min(15,float(request.get('activity_radius_km','15'))) if request.get('surroundings',True) else 2
    for card in soup.select('.vcard[data-name]'):
        groups=set(re.split(r'[,;\s]+',card.get('data-group','')))
        types=set(re.split(r'[,;\s]+',card.get('data-type','')))
        # Exclude lodging, old/current events, transport and unidentified venues.
        if not groups & {'see','do','drink','eat','nature','view'} or types & {'event','festival'}:continue
        matched=sorted(k for k in topics if types & TOPIC_TYPES[k])
        if not matched:continue
        name=card.get('data-name','').strip();marker=card.select_one('[data-lat][data-lon]')
        if not name or len(name)>120 or marker is None or card.get('data-country')!=destination['code'] or card.get('data-location-qid')!=identity['qid']:
            gaps.append('Ein Quelleneintrag ohne vollständige Ortszuordnung wurde zurückgehalten.');continue
        try:point=coordinates(marker['data-lat'],marker['data-lon'])
        except (ValueError,KeyError):continue
        km=distance(destination,point)
        if km>radius:continue
        subject_id=card.get('data-wikidata')
        if not re.fullmatch(r'Q\d+',str(subject_id or '')):subject_id=evidence_id([name,point])
        fragment=card.get('id','')
        url=response['final_url']+('#'+quote(fragment,safe='') if fragment else '')
        subject=dict(id=subject_id,name=name,coordinates=point,distance_km=round(km,3),distance_kind='Luftlinie zum Quelleneintrag')
        literal=json.dumps(dict(name=name,group=sorted(groups),type=sorted(types),latitude=point['latitude'],longitude=point['longitude'],country=card['data-country'],location_qid=card['data-location-qid']),ensure_ascii=False,sort_keys=True)
        fields=[('listing',literal)]
        for kind,selector in [('published_hours','.voy-listing-hours'),('access_note','.voy-listing-directions')]:
            nodes=card.select(selector)
            if len(nodes)==1:
                text=clean(nodes[0])
                if text and len(text)<=400:fields.append((kind,text))
                elif text:gaps.append(name+': langes Quellenfeld nicht gekürzt als Behauptung übernommen.')
        for kind,text in fields:
            if len(result)>=8:break
            result.append(dict(id=evidence_id([destination['id'],subject_id,url,kind,text]),kind=kind,quote=text,
                source='Wikivoyage (Community-Reiseführer)',source_url=url,original_url=response['original_url'],final_url=response['final_url'],
                retrieved_at=response['retrieved_at'],publication_at=None,source_update_note=clean(card.select_one('.voy-listing-lastedit'))[:120],
                subject=subject,target_id=destination['id'],identity=identity,topics=matched,verification_status='Aussage der Quelle; Identität und Originalnachweis technisch geprüft',
                limitations=LIMITATION,cache_used=response.get('cache_used',False),extraction_truncated=False,ranking_effect=False,
                licensing='Wikivoyage CC BY-SA; Wikidata CC0',attribution_url='https://de.wikivoyage.org/wiki/Wikivoyage:Lizenzbestimmungen'))
        if len(result)>=8:break
    if not result:gaps.append('Keine ausreichend zugeordneten strukturierten Einträge im gewählten Themen-/Ortsumfang gefunden. Dies belegt kein fehlendes Angebot.')
    gaps.append('Auswahl begrenzt auf höchstens acht Quellenfelder und maximal 15 km Luftlinie. Keine Vollerhebung oder aktuelle Buchbarkeitsprüfung.')
    return result,list(dict.fromkeys(gaps))
