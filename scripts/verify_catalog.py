"""Explicit developer maintenance, not a periodic task. Grouped Wikimedia reads, maximum 40 titles per call.

Usage: PYTHONPATH=. .venv/bin/python scripts/verify_catalog.py
Updates coordinates/source provenance, not editorial interests.
"""
import json
from pathlib import Path
from urllib.parse import urlencode, unquote
from src.vacation_planner.infrastructure.planning.PublicHttpClient import PublicHttpClient
from src.vacation_planner.core.planning.SearchContext import SearchContext

path=Path('src/vacation_planner/infrastructure/planning/data/destinations.json')
items=json.loads(path.read_text())
for d in items:
    if d['name']=='Lagos':d['source']='https://de.wikivoyage.org/wiki/Lagos_(Portugal)'
    if d['name']=='Bergen':d['source']='https://de.wikivoyage.org/wiki/Bergen_(Norwegen)'
context=SearchContext(seconds=300,budget=20)
http=PublicHttpClient()
reports=[]
for offset in range(0,len(items),40):
    batch=items[offset:offset+40]
    titles='|'.join(unquote(d['source'].rsplit('/',1)[1]).replace('_',' ') for d in batch)
    params=dict(action='query',titles=titles,prop='coordinates|pageprops',ppprop='disambiguation',colimit='max',coprimary='primary',redirects=1,format='json')
    data,stamp=http.json('https://de.wikivoyage.org/w/api.php?'+urlencode(params),context)
    reports.append(data)
    pages={p['title']:p for p in data['query']['pages'].values()}
    redirects={p['from']:p['to'] for p in data['query'].get('redirects',[])}
    for d in batch:
        title=unquote(d['source'].rsplit('/',1)[1]).replace('_',' ')
        title=redirects.get(title,title)
        p=pages[title]
        if 'missing' in p or 'disambiguation' in p.get('pageprops',{}):
            raise ValueError('Katalogquelle nicht eindeutig: '+d['name'])
        if p.get('coordinates'):
            coordinate=p['coordinates'][0]
            d['latitude'],d['longitude']=coordinate['lat'],coordinate['lon']
            d['coordinate_source']=d['source']
        d['source_checked_at']=stamp
        d.pop('checked_at',None)
        print(d['name'], 'verified', bool(p.get('coordinates')))
path.write_text(json.dumps(items,ensure_ascii=False,indent=2))
Path('docs/KATALOGPRUEFUNG.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2))
