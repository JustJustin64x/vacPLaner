"""Explicit bounded maintenance: validate seed identities via grouped Wikimedia reads.
No geocoding, no schedule, no invented coordinates; missing/ambiguous pages are excluded.
"""
import json
from pathlib import Path
from urllib.parse import urlencode,quote,unquote
from src.vacation_planner.infrastructure.planning.PublicHttpClient import PublicHttpClient
from src.vacation_planner.core.planning.SearchContext import SearchContext

ROOT=Path(__file__).resolve().parents[1]
path=ROOT/'src/vacation_planner/infrastructure/planning/data/destinations.json'
items=json.loads(path.read_text())
seeds=[]
for line in (ROOT/'scripts/catalog_seeds.tsv').read_text().splitlines():
    code,country,region,area,landscape,names=line.split('|')
    for name in names.split(';'):
        seeds.append(dict(name=name,code=code,country=country,region=region,regions=[region,area],
                          area_id=code+':'+area,landscapes=[landscape],type='Dorf/Ferienort',
                          interests=['Natur','Berge','Wandern'] if landscape=='Berge/Natur' else ['Natur','Baden'],
                          editorial_note='Redaktionelle Landschaftspräferenz, keine belegte Aktivität; Ortsstatus laut verlinkter Reiseführerquelle.'))
context=SearchContext(seconds=300,budget=30);http=PublicHttpClient();reports=[];accepted=[];rejected=[]
for offset in range(0,len(seeds),40):
    batch=seeds[offset:offset+40]
    params=dict(action='query',titles='|'.join(d['name'] for d in batch),prop='coordinates|pageprops|extracts',
                ppprop='disambiguation',colimit='max',coprimary='primary',redirects=1,format='json',exintro=1,explaintext=1,exsentences=2,exlimit='max')
    data,stamp=http.json('https://de.wikivoyage.org/w/api.php?'+urlencode(params),context)
    reports.append(dict(retrieved_at=stamp,response=data))
    pages={p['title']:p for p in data['query']['pages'].values()}
    redirects={p['from']:p['to'] for p in data['query'].get('normalized',[])+data['query'].get('redirects',[])}
    for d in batch:
        title=d['name'];seen=set()
        while title in redirects and title not in seen:seen.add(title);title=redirects[title]
        p=pages.get(title,{})
        if not p.get('coordinates') or 'missing' in p or 'disambiguation' in p.get('pageprops',{}):
            rejected.append(dict(name=d['name'],reason='Keine eindeutige Seite mit Primärkoordinaten'));continue
        if any(x.get('id')=='wv-de:'+str(p['pageid']) for x in accepted):continue
        coord=p['coordinates'][0]
        d.update(id='wv-de:'+str(p['pageid']),latitude=coord['lat'],longitude=coord['lon'],
                 source='https://de.wikivoyage.org/wiki/'+quote(title.replace(' ','_'),safe='()'),
                 source_checked_at=stamp,aliases=[title] if title!=d['name'] else [],
                 source_intro=p.get('extract',''),base_name=d['name'],catalog_version=2)
        d['coordinate_source']=d['source'];d['type_source']=d['source']
        # Settlement vs region typing uses the actual source introduction when available.
        intro=d['source_intro'].lower()
        if 'stadt' in intro:d['type']='Klein-/Mittelstadt'
        # The seed selection contains no capitals/large cities. Words such as
        # Bezirkshauptstadt or 'near Barcelona' cannot turn a small place into one.
        d['interest_strengths']={k:3 if k in ('Wandern','Baden') else 4 for k in d['interests']}
        accepted.append(d)
    print(offset+len(batch),'/',len(seeds),'accepted',len(accepted),flush=True)
# Original identities retain coordinates and provenance. Explicit, reviewable classification.
small={'Bled','Zell am See','Hallstatt','Kranjska Gora','Zakopane','Chamonix','Lagos','Kotor'}
medium={'Freiburg','Heidelberg','Konstanz','Rostock','Split','Dubrovnik','Zadar','Pula','Innsbruck','Salzburg','Luzern','Interlaken','Annecy','La Rochelle','Biarritz','Braga','Faro','Galway','Killarney','Visby','Tromsø','Tartu','Pärnu','Mostar','Sarajevo','Brașov','Sibiu','Burgas','Varna'}
for d in items:
    d.setdefault('id','wv-de-title:'+unquote(d['source'].rsplit('/',1)[1]))
    d.setdefault('type','Dorf/Ferienort' if d['name'] in small else 'Klein-/Mittelstadt' if d['name'] in medium else 'Großstadt')
    d.setdefault('regions',[d['region']]);d.setdefault('landscapes',[])
    if 'Wandern' in d['interests']:d['landscapes'].append('Berge/Natur')
    if 'Baden' in d['interests']:d['landscapes'].append('See/Küste')
    d['landscapes']=sorted(set(d['landscapes']))
    d.setdefault('area_id',d['code']+':'+d['name']);d.setdefault('base_name',d['name']);d['catalog_version']=2
    d.setdefault('aliases',[]);d['interest_strengths']={k:3 for k in d['interests'] if k not in ('Kostenlos','Veranstaltungen')}
    if d['name']=='Freiburg':d['regions']+=['Schwarzwald'];d['aliases']+=['Freiburg im Breisgau'];d['area_id']='DE:Schwarzwald'
    if d['name']=='Bled':d['regions']+=['Julische Alpen','Triglav/Bohinj'];d['area_id']='SI:Julische Alpen'
for d in accepted:
    old=next((x for x in items if unquote(x['source'])==unquote(d['source']) or x['name']==d['name']),None)
    if old:old.update(d)
    else:items.append(d)
overrides=json.loads((ROOT/'scripts/catalog_overrides.json').read_text())
for d in items:
    if d['name'] in overrides:d.update(overrides[d['name']])
    d.setdefault('regional_name',d.get('regions',[])[-1] if d.get('regions') else d['region'])
path.write_text(json.dumps(items,ensure_ascii=False,indent=2)+'\n')
(ROOT/'docs/KATALOGERWEITERUNG_2026-10-28.json').write_text(json.dumps(dict(calls=context.calls,accepted=len(accepted),rejected=rejected,reports=reports),ensure_ascii=False,indent=2)+'\n')
print('Total',len(items),'countries',len({d['code'] for d in items}),'nonlarge',sum(d['type']!='Großstadt' for d in items))
