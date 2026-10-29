"""Separate, replaceable discovery data; never changes the user's trip database."""
from contextlib import contextmanager
import json
import math
import sqlite3
from uuid import uuid4
from pathlib import Path

from .TripStore import timestamp
from ...core.planning.PlaceResearch import distance

ATTRIBUTIONS=[{'label':'GeoNames · CC BY 4.0','url':'https://www.geonames.org/about.html'},
              {'label':'© OpenStreetMap-Mitwirkende · ODbL','url':'https://www.openstreetmap.org/copyright'},
              {'label':'Wikidata · CC0','url':'https://www.wikidata.org/wiki/Wikidata:Licensing'}]


class DestinationInventory:
    def __init__(self,path):
        self.path=Path(path);self.path.parent.mkdir(parents=True,exist_ok=True)
        with self.connect() as db:
            db.execute('PRAGMA journal_mode=WAL')
            db.executescript('''
            CREATE TABLE IF NOT EXISTS datasets(key TEXT PRIMARY KEY,payload TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS places(id TEXT UNIQUE NOT NULL,country TEXT NOT NULL,kind TEXT NOT NULL,lat REAL,lon REAL,payload TEXT NOT NULL);
            CREATE INDEX IF NOT EXISTS places_country ON places(country,kind);
            CREATE VIRTUAL TABLE IF NOT EXISTS place_geo USING rtree(id,minlat,maxlat,minlon,maxlon);
            CREATE TABLE IF NOT EXISTS features(id TEXT UNIQUE NOT NULL,region TEXT NOT NULL,lat REAL,lon REAL,payload TEXT NOT NULL);
            CREATE INDEX IF NOT EXISTS features_region ON features(region);
            CREATE TABLE IF NOT EXISTS feature_membership(region TEXT NOT NULL,id TEXT NOT NULL,PRIMARY KEY(region,id));
            CREATE VIRTUAL TABLE IF NOT EXISTS feature_geo USING rtree(id,minlat,maxlat,minlon,maxlon);
            CREATE TABLE IF NOT EXISTS entities(id TEXT PRIMARY KEY,payload TEXT NOT NULL,updated TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS derived_catalog(key TEXT PRIMARY KEY,payload BLOB NOT NULL);
            ''')
            db.execute('INSERT OR IGNORE INTO feature_membership SELECT region,id FROM features')

    @contextmanager
    def connect(self):
        db=sqlite3.connect(self.path,timeout=20)
        try:
            with db:yield db
        finally:db.close()

    def coverage(self):
        with self.connect() as db:return [json.loads(x[0]) for x in db.execute('SELECT payload FROM datasets ORDER BY key')]

    def replace_country(self,code,rows,metadata,context):
        # SQLite rolls the complete country update back on cancellation or parse error.
        with self.connect() as db:
            db.execute('DELETE FROM place_geo WHERE id IN (SELECT rowid FROM places WHERE country=?)',(code,))
            db.execute('DELETE FROM places WHERE country=?',(code,))
            counts={};count=0
            for item in rows:
                if count%250==0:context.check()
                db.execute('INSERT INTO places VALUES(?,?,?,?,?,?)',(item['id'],code,item['kind'],item['latitude'],item['longitude'],json.dumps(item,ensure_ascii=False)))
                rid=db.execute('SELECT rowid FROM places WHERE id=?',(item['id'],)).fetchone()[0]
                db.execute('INSERT INTO place_geo VALUES(?,?,?,?,?)',(rid,item['latitude'],item['latitude'],item['longitude'],item['longitude']))
                count+=1;counts[item['kind']]=counts.get(item['kind'],0)+1
            if not count:raise ValueError('Länderdatei enthält keine verwendbaren geografischen Objekte; alter Stand bleibt erhalten.')
            context.check();metadata={**metadata,'key':'geonames:'+code,'country':code,'count':count,'kinds':counts,'updated_at':timestamp(),'revision':str(uuid4()),'status':'imported'}
            db.execute('INSERT OR REPLACE INTO datasets VALUES(?,?)',(metadata['key'],json.dumps(metadata,ensure_ascii=False)))
        return metadata

    @staticmethod
    def _near(db,table,lat,lon,km):
        dy=km/110.5;dx=dy/max(.15,math.cos(math.radians(lat)))
        geo='place_geo' if table=='places' else 'feature_geo'
        rows=db.execute(f'SELECT p.payload FROM {table} p JOIN {geo} g ON p.rowid=g.id WHERE g.minlat<=? AND g.maxlat>=? AND g.minlon<=? AND g.maxlon>=?',(lat+dy,lat-dy,lon+dx,lon-dx))
        center={'latitude':lat,'longitude':lon}
        return [p for (raw,) in rows if distance(center,p:=json.loads(raw))<=km]

    def nearby(self,lat,lon,km,kind='places'):
        if kind not in ('places','features'):raise ValueError('Ungültige Datenauswahl')
        with self.connect() as db:return self._near(db,kind,lat,lon,km)

    def replace_features(self,key,bounds,elements,context,source):
        seen=set();rows=[]
        for e in elements:
            context.check();center=e.get('center') or e
            if center.get('lat') is None or center.get('lon') is None:continue
            tags=e.get('tags') or {};identity='osm:'+e['type']+':'+str(e['id'])
            if identity in seen:continue
            seen.add(identity)
            rows.append(dict(id=identity,name=tags.get('name:de') or tags.get('name') or 'Erfasstes Freizeitmerkmal',
                latitude=center['lat'],longitude=center['lon'],tags=tags,source='https://www.openstreetmap.org/'+e['type']+'/'+str(e['id']),
                retrieved_at=timestamp(),license='ODbL',source_region=key))
        with self.connect() as db:
            db.execute('DELETE FROM feature_membership WHERE region=?',(key,))
            for p in rows:
                context.check()
                old=db.execute('SELECT rowid FROM features WHERE id=?',(p['id'],)).fetchone()
                if old:db.execute('DELETE FROM feature_geo WHERE id=?',old)
                db.execute('INSERT OR REPLACE INTO features VALUES(?,?,?,?,?)',(p['id'],key,p['latitude'],p['longitude'],json.dumps(p,ensure_ascii=False)))
                rid=db.execute('SELECT rowid FROM features WHERE id=?',(p['id'],)).fetchone()[0]
                db.execute('INSERT INTO feature_geo VALUES(?,?,?,?,?)',(rid,p['latitude'],p['latitude'],p['longitude'],p['longitude']))
                db.execute('INSERT OR IGNORE INTO feature_membership VALUES(?,?)',(key,p['id']))
            db.execute('DELETE FROM feature_geo WHERE id IN (SELECT rowid FROM features WHERE id NOT IN (SELECT id FROM feature_membership))')
            db.execute('DELETE FROM features WHERE id NOT IN (SELECT id FROM feature_membership)')
            context.check()
            meta=dict(key='osm:'+key,name=key.rsplit(':',1)[0],bounds=bounds,count=len(rows),updated_at=timestamp(),revision=str(uuid4()),status='imported',source=source,license='ODbL')
            db.execute('INSERT OR REPLACE INTO datasets VALUES(?,?)',(meta['key'],json.dumps(meta,ensure_ascii=False)))
        return meta

    def candidates(self,context=None):
        import hashlib
        import zlib
        if context:context.check()
        with self.connect() as db:
            version=db.execute('SELECT max(updated) FROM entities').fetchone()[0]
            key=hashlib.sha256(json.dumps([self.coverage(),version,'features-v6'],sort_keys=True).encode()).hexdigest()
            cached=db.execute('SELECT payload FROM derived_catalog WHERE key=?',(key,)).fetchone()
            if cached:return json.loads(zlib.decompress(cached[0]))
        result=self._build_candidates(context)
        with self.connect() as db:
            db.execute('DELETE FROM derived_catalog')
            db.execute('INSERT INTO derived_catalog VALUES(?,?)',(key,zlib.compress(json.dumps(result,ensure_ascii=False).encode(),3)))
        return result

    def _build_candidates(self,context=None):
        from ...core.planning.DestinationFeatures import feature_profile
        coverage=[x for x in self.coverage() if x['key'].startswith('osm:')]
        result=[]
        with self.connect() as db:
            for (raw,) in db.execute("SELECT payload FROM places WHERE kind='settlement'"):
                if context and len(result)%250==0:context.check()
                p=json.loads(raw);lat,lon=p['latitude'],p['longitude']
                inside=[c for c in coverage if c['bounds'][0]<=lat<=c['bounds'][2] and c['bounds'][1]<=lon<=c['bounds'][3]]
                p['feature_profile']=feature_profile(self._near(db,'features',lat,lon,15) if inside else [],p,inside)
                if inside:
                    regions=self._near(db,'places',lat,lon,20)
                    relevant=sorted((r for r in regions if r['kind']=='region' and r['feature_code'] in ('LK','LKS','MTS','PRK','RESN')),key=lambda r:distance(p,r))[:2]
                    p['tourist_regions']=[dict(id=r['id'],name=r['name'],source=r['source'],distance_km=round(distance(p,r),1)) for r in relevant]
                    if relevant:p['area_id']=relevant[0]['id'];p['regions']+= [r['name'] for r in relevant]
                p['landscapes']=p['feature_profile']['landscapes']
                result.append(p)
            # OSM settlements are additional identities, only with a verifiable country context.
            for (raw,) in db.execute('SELECT payload FROM features'):
                if context:context.check()
                f=json.loads(raw);tags=f['tags']
                if tags.get('place') not in ('town','village','hamlet') or not tags.get('name'):continue
                qid=tags.get('wikidata');entity=self.entity(qid) if qid else None
                claims=(entity or {}).get('claims',{})
                linked=[str(c.get('mainsnak',{}).get('datavalue',{}).get('value')) for c in claims.get('P1566',[])]
                gid=tags.get('geonames:id') or tags.get('geonames')
                if gid:linked.append(gid)
                nearby=[p for p in self._near(db,'places',f['latitude'],f['longitude'],1) if p['kind']=='settlement']
                same=next((p for p in result if p.get('geonames_id') in linked),None) if linked else None
                if same is None:
                    from .DestinationCatalog import normalize
                    match=next((p for p in nearby if normalize(tags['name']) in {normalize(n) for n in [p['name'],*p.get('aliases',[])]} and distance(p,f)<.5),None)
                    if match:same=next((p for p in result if p['id']==match['id']),None)
                if same:
                    same.setdefault('source_identities',[]).append(f['id'])
                    if qid:same['wikidata_id']=qid
                    if entity:
                        same['wikidata_relationships']={k:claims.get(k,[]) for k in ('P31','P131','P361')}
                        wiki=entity.get('sitelinks',{}).get('dewikivoyage',{}).get('title')
                        if wiki:
                            from urllib.parse import quote
                            same['wikivoyage_source']='https://de.wikivoyage.org/wiki/'+quote(wiki.replace(' ','_'))
                    continue
                from .DestinationImportService import COUNTRIES
                verified_code=tags.get('addr:country') or tags.get('is_in:country_code')
                if verified_code not in COUNTRIES or not nearby:continue  # Never infer a country across a nearby border.
                anchor=min(nearby,key=lambda p:distance(p,f))
                if anchor['code']!=verified_code:continue
                p=dict(anchor,id=f['id'],name=tags['name'],aliases=[tags['name']],latitude=f['latitude'],longitude=f['longitude'],source=f['source'],
                       type='Dorf/Ferienort' if tags['place'] in ('village','hamlet') else 'Klein-/Mittelstadt',source_identities=[f['id']],wikidata_id=qid or '',license='ODbL')
                p.pop('geonames_id',None);p['inventory_place']=True;p.pop('population',None)
                p.update(region='Verwaltungseinheit nicht bestätigt',regions=[],admin1='',admin2='',admin3='',admin4='',coordinate_source=f['source'],
                         coordinate_note='OSM-Ortskoordinate; keine Unterkunftszufahrt',attributions=ATTRIBUTIONS[:2])
                inside=[c for c in coverage if c['bounds'][0]<=p['latitude']<=c['bounds'][2] and c['bounds'][1]<=p['longitude']<=c['bounds'][3]]
                p['feature_profile']=feature_profile(self._near(db,'features',p['latitude'],p['longitude'],15),p,inside);p['landscapes']=p['feature_profile']['landscapes']
                result.append(p)
        return result

    def save_entities(self,entities):
        with self.connect() as db:
            for identity,item in entities.items():db.execute('INSERT OR REPLACE INTO entities VALUES(?,?,?)',(identity,json.dumps(item,ensure_ascii=False),timestamp()))
            db.execute('DELETE FROM derived_catalog')

    def entity(self,identity):
        with self.connect() as db:
            row=db.execute('SELECT payload FROM entities WHERE id=?',(identity,)).fetchone()
            return json.loads(row[0]) if row else None

    def stale_entity_ids(self,ids):
        from datetime import datetime, timezone
        with self.connect() as db:
            result=[]
            for identity in ids:
                row=db.execute('SELECT updated FROM entities WHERE id=?',(identity,)).fetchone()
                if not row or (datetime.now(timezone.utc)-datetime.fromisoformat(row[0])).total_seconds()>7*86400:result.append(identity)
        return result
