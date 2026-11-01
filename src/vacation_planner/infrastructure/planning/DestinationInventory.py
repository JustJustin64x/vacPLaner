"""Separate, replaceable discovery data; never changes the user's trip database."""
from contextlib import contextmanager
import json
import math
import sqlite3
from uuid import uuid4
from pathlib import Path

from .TripStore import timestamp
from ...core.planning.PlaceResearch import distance
from ...core.planning.DestinationFeatures import spatial_distance as self_feature_distance

ATTRIBUTIONS=[{'label':'GeoNames · CC BY 4.0','url':'https://www.geonames.org/about.html'},
              {'label':'© OpenStreetMap-Mitwirkende · ODbL','url':'https://www.openstreetmap.org/copyright'},
              {'label':'Wikidata · CC0','url':'https://www.wikidata.org/wiki/Wikidata:Licensing'}]


class DestinationInventory:
    FEATURE_VERSION='features-v14'
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
            CREATE TABLE IF NOT EXISTS index_versions(key TEXT PRIMARY KEY,coverage TEXT,catalog_key TEXT);
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

    def record_attempt(self,key,bounds,source,status,error,categories=None):
        with self.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS import_attempts(key TEXT PRIMARY KEY,payload TEXT NOT NULL)')
            item=dict(key=key,bounds=bounds,source=source,status=status,error=error,updated_at=timestamp(),categories=categories or [])
            db.execute('INSERT OR REPLACE INTO import_attempts VALUES(?,?)',(key,json.dumps(item,ensure_ascii=False)))

    def attempts(self):
        with self.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS import_attempts(key TEXT PRIMARY KEY,payload TEXT NOT NULL)')
            return [json.loads(r[0]) for r in db.execute('SELECT payload FROM import_attempts ORDER BY key')]

    def replace_country(self,code,rows,metadata,context):
        # SQLite rolls the complete country update back on cancellation or parse error.
        with self.connect() as db:
            db.execute('DELETE FROM place_geo WHERE id IN (SELECT rowid FROM places WHERE country=?)',(code,))
            db.execute('DELETE FROM places WHERE country=?',(code,))
            counts={};count=0
            for item in rows:
                if count%250==0:context.check()
                db.execute('DELETE FROM place_geo WHERE id IN (SELECT rowid FROM places WHERE id=?)',(item['id'],))
                db.execute('INSERT OR REPLACE INTO places VALUES(?,?,?,?,?,?)',(item['id'],code,item['kind'],item['latitude'],item['longitude'],json.dumps(item,ensure_ascii=False)))
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
        result=[]
        for (raw,) in rows:
            p=json.loads(raw);separation=self_feature_distance(center,p)
            if separation<=km:
                if table=='features':p['_distance_origin']=[lat,lon];p['_query_distance_km']=separation
                result.append(p)
        return result

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
                retrieved_at=timestamp(),license='ODbL',source_region=key,geometry=e.get('geometry'),geometry_status=e.get('geometry_status','representative_only'),member_count=e.get('member_count')))
        with self.connect() as db:
            db.execute('DELETE FROM feature_membership WHERE region=?',(key,))
            for p in rows:
                context.check()
                old=db.execute('SELECT rowid FROM features WHERE id=?',(p['id'],)).fetchone()
                if old:db.execute('DELETE FROM feature_geo WHERE id=?',old)
                db.execute('INSERT OR REPLACE INTO features VALUES(?,?,?,?,?)',(p['id'],key,p['latitude'],p['longitude'],json.dumps(p,ensure_ascii=False)))
                rid=db.execute('SELECT rowid FROM features WHERE id=?',(p['id'],)).fetchone()[0]
                b=(p.get('geometry') or {}).get('bounds',[p['latitude'],p['longitude'],p['latitude'],p['longitude']])
                db.execute('INSERT INTO feature_geo VALUES(?,?,?,?,?)',(rid,b[0],b[2],b[1],b[3]))
                db.execute('INSERT OR IGNORE INTO feature_membership VALUES(?,?)',(key,p['id']))
            db.execute('DELETE FROM feature_geo WHERE id IN (SELECT rowid FROM features WHERE id NOT IN (SELECT id FROM feature_membership))')
            db.execute('DELETE FROM features WHERE id NOT IN (SELECT id FROM feature_membership)')
            context.check()
            meta=dict(key='osm:'+key,name=key.rsplit(':',1)[0],bounds=bounds,count=len(rows),updated_at=timestamp(),revision=str(uuid4()),status='partial',categories=['Wandern','Baden','Natur','Ruhe','Kultur','Feiern','Barhopping','Restaurants','Berge','Unterkünfte'],coverage_note='Kartierte Merkmale; keine Vollerhebung',source=source,license='ODbL')
            db.execute('INSERT OR REPLACE INTO datasets VALUES(?,?)',(meta['key'],json.dumps(meta,ensure_ascii=False)))
        return meta

    def candidates(self,context=None,request=None):
        import hashlib
        import zlib
        if context:context.check()
        with self.connect() as db:
            version=db.execute('SELECT max(updated) FROM entities').fetchone()[0]
            key=hashlib.sha256(json.dumps([self.coverage(),version,self.FEATURE_VERSION,[request.countries,request.regions,request.excluded,request.target_type] if request else None],sort_keys=True).encode()).hexdigest()
            cached=db.execute('SELECT payload FROM derived_catalog WHERE key=?',(key,)).fetchone()
            if cached:return self.annotate_attempts(json.loads(zlib.decompress(cached[0])))
            previous=db.execute("SELECT coverage,catalog_key FROM index_versions WHERE key='default'").fetchone() if request is None else None
            prior=db.execute('SELECT payload FROM derived_catalog WHERE key=?',(previous[1],)).fetchone() if previous else None
        result=None
        if prior:
            before=json.loads(previous[0]);after=self.coverage()
            countries=lambda rows:[(r['key'],r.get('revision')) for r in rows if r['key'].startswith('geonames:')]
            if countries(before)==countries(after):
                changed=[r for r in after if r not in before and r.get('bounds')]
                if changed:
                    result=json.loads(zlib.decompress(prior[0]))
                    coverage=[r for r in after if r['key'].startswith('osm:')]
                    with self.connect() as db:
                        for ix,p in enumerate(result):
                            if context and ix%100==0:context.check()
                            if any(r['bounds'][0]-.15<=p['latitude']<=r['bounds'][2]+.15 and r['bounds'][1]-.3<=p['longitude']<=r['bounds'][3]+.3 for r in changed):self.profile_place(p,coverage,db)
        self._attempt_cache=self.attempts()
        if result is None:result=self._build_candidates(context,request)
        with self.connect() as db:
            db.execute('DELETE FROM derived_catalog WHERE key=?',(key,))
            db.execute('INSERT INTO derived_catalog VALUES(?,?)',(key,zlib.compress(json.dumps(result,ensure_ascii=False).encode(),3)))
            db.execute('DELETE FROM derived_catalog WHERE key NOT IN (SELECT key FROM derived_catalog ORDER BY rowid DESC LIMIT 4) AND key NOT IN (SELECT catalog_key FROM index_versions)')
        if request is None:
            with self.connect() as db:db.execute("INSERT OR REPLACE INTO index_versions VALUES('default',?,?)",(json.dumps(self.coverage(),ensure_ascii=False),key))
        return self.annotate_attempts(result)

    def annotate_attempts(self,places):
        self._attempt_cache=self.attempts()
        failures=[a for a in self._attempt_cache if a.get('bounds') and a['status']=='failed']
        for p in places:
            profile=p.get('feature_profile')
            if not profile:continue
            errors=[]
            for a in failures:
                b=a['bounds']
                if b[0]<=p['latitude']<=b[2] and b[1]<=p['longitude']<=b[3]:
                    errors.append(a['error'])
                    for topic in a.get('categories',[]):
                        if topic!='Ruhe' and profile.get('category_status',{}).get(topic)=='not_investigated':profile['category_status'][topic]='source_unreachable'
            if errors:profile['source_errors']=list(dict.fromkeys(errors))
        return places

    @staticmethod
    def covered(c,lat,lon,radius=0):
        from .EuropeScope import in_ring
        b=c['bounds']
        def point(y,x):
            if not (b[0]<=y<=b[2] and b[1]<=x<=b[3]):return False
            rings=c.get('source_polygons')
            if not rings:return True
            return any(in_ring(y,x,r['points']) for r in rings if not r['hole']) and not any(in_ring(y,x,r['points']) for r in rings if r['hole'])
        if not point(lat,lon):return False
        if not radius:return True
        dy=radius/110.5;dx=dy/max(.15,math.cos(math.radians(lat)))
        return bool(c.get('source_polygons')) and all(point(lat+y*dy,lon+x*dx) for y,x in ((-1,-1),(-1,1),(1,-1),(1,1)))

    def sample_rows(self,db,request=None):
        # Apply geography and type BEFORE representative selection. Every imported
        # village remains eligible; bounded per-cell representatives limit RAM.
        where=["kind='settlement'"];params=[]
        if request:
            from .DestinationImportService import COUNTRIES
            from .DestinationCatalog import normalize
            allowed=[c for c,n in COUNTRIES.items() if (not request.countries or any(normalize(v) in (normalize(c),normalize(n)) for v in request.countries)) and not any(normalize(v) in (normalize(c),normalize(n)) for v in request.excluded)]
            where.append('country IN ('+','.join('?' for c in allowed)+')');params+=allowed
            if request.regions:
                where.append('('+' OR '.join('payload LIKE ?' for _ in request.regions)+')');params+=['%'+r+'%' for r in request.regions]
            if request.target_type=='kleiner Ort':where.append("json_extract(payload,'$.type')!='Großstadt'")
            elif request.target_type=='Stadt':where.append("json_extract(payload,'$.type') IN ('Großstadt','Klein-/Mittelstadt')")
        # Fine 0.35° cells, separate town/village representatives, stable identities.
        sql="""SELECT payload FROM (SELECT payload, row_number() OVER (
            PARTITION BY country,cast((lat+90)/.35 AS INT),cast((lon+180)/.35 AS INT),json_extract(payload,'$.type')
            ORDER BY id) AS rn FROM places WHERE """+' AND '.join(where)+') WHERE rn<=2'
        return db.execute(sql,params)

    def profile_place(self,p,coverage,db):
        from ...core.planning.DestinationFeatures import feature_profile
        lat,lon=p['latitude'],p['longitude']
        inside=[dict(c,radius_complete=self.covered(c,lat,lon,15)) for c in coverage if self.covered(c,lat,lon)]
        features=self._near(db,'features',lat,lon,15) if inside else []
        p['feature_profile']=feature_profile(features,p,inside)
        for attempt in getattr(self,'_attempt_cache',[]):
            if attempt.get('bounds') and attempt['status']=='failed' and self.covered(attempt,lat,lon):
                for topic in attempt.get('categories',[]):
                    if topic!='Ruhe' and p['feature_profile'].get('category_status',{}).get(topic)=='not_investigated':p['feature_profile']['category_status'][topic]='source_unreachable'
        p['landscapes']=p['feature_profile']['landscapes']
        if inside:
            relevant=sorted((r for r in self._near(db,'places',lat,lon,20) if r['kind']=='region' and r['feature_code'] in ('LK','LKS','MTS','PRK','RESN')),key=lambda r:distance(p,r))[:2]
            p['tourist_regions']=[dict(id=r['id'],name=r['name'],source=r['source'],distance_km=round(distance(p,r),1)) for r in relevant]
            if relevant:p['area_id']=relevant[0]['id'];p['regions']+= [r['name'] for r in relevant]
        return p

    def _build_candidates(self,context=None,request=None):
        from ...core.planning.DestinationFeatures import feature_profile
        coverage=[x for x in self.coverage() if x['key'].startswith('osm:')]
        result=[]
        with self.connect() as db:
            for (raw,) in self.sample_rows(db,request):
                if context and len(result)%25==0:context.check()
                result.append(self.profile_place(json.loads(raw),coverage,db))
            by_id={p['id']:p for p in result}
            extra_cells=set()
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
                same=next((by_id['geonames:'+gid] for gid in linked if 'geonames:'+gid in by_id),None) if linked else None
                if same is None and linked:
                    existing=db.execute('SELECT id FROM places WHERE id IN ('+','.join('?' for _ in linked)+')',['geonames:'+gid for gid in linked]).fetchone()
                    if existing:continue # Identity exists in the full inventory, outside this representative slice.
                if same is None:
                    from .DestinationCatalog import normalize
                    match=next((p for p in nearby if normalize(tags['name']) in {normalize(n) for n in [p['name'],*p.get('aliases',[])]} and distance(p,f)<.5),None)
                    if match:
                        same=by_id.get(match['id'])
                        if same is None:continue # Do not promote every mapped village over the geographic sample.
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
                cell=(int(f['latitude']*20),int(f['longitude']*20))
                if cell in extra_cells:continue
                extra_cells.add(cell)
                p=dict(anchor,id=f['id'],name=tags['name'],aliases=[tags['name']],latitude=f['latitude'],longitude=f['longitude'],source=f['source'],
                       type='Dorf/Ferienort' if tags['place'] in ('village','hamlet') else 'Klein-/Mittelstadt',source_identities=[f['id']],wikidata_id=qid or '',license='ODbL')
                p.pop('geonames_id',None);p['inventory_place']=True;p.pop('population',None)
                p.update(region='Verwaltungseinheit nicht bestätigt',regions=[],admin1='',admin2='',admin3='',admin4='',coordinate_source=f['source'],
                         coordinate_note='OSM-Ortskoordinate; keine Unterkunftszufahrt',attributions=ATTRIBUTIONS[:2])
                self.profile_place(p,coverage,db);result.append(p);by_id[p['id']]=p
        return result

    def find_name(self,name,country=''):
        from .DestinationCatalog import normalize
        wanted=normalize(name);matches=[]
        with self.connect() as db:
            for (raw,) in db.execute("SELECT payload FROM places WHERE kind='settlement' AND payload LIKE ? LIMIT 2000",('%'+name+'%',)):
                p=json.loads(raw)
                if country and normalize(country) not in (normalize(p['code']),normalize(p['country'])):continue
                if wanted in {normalize(x) for x in [p['name'],*p.get('aliases',[])]}:matches.append(p)
        return matches

    def exact_named_places(self,name,country,region,context):
        """Full country scan, no LIKE/2000 truncation or fuzzy first match.

        At most four opt-in lookups per search. Ambiguity stays explicit.
        """
        from .DestinationCatalog import normalize,DestinationCatalog
        wanted=normalize(name);matches=[]
        from .DestinationImportService import COUNTRIES
        if country not in COUNTRIES:return []
        catalog=DestinationCatalog() # policy aliases only; no second data store
        with self.connect() as db:
            for i,(raw,) in enumerate(db.execute("SELECT payload FROM places WHERE country=? AND kind='settlement'",(country,))):
                if i%128==0:context.check()
                p=json.loads(raw)
                if wanted not in {normalize(x) for x in [p['name'],*p.get('aliases',[])]}:continue
                if region and catalog.area(region) not in catalog.labels(p):continue
                matches.append(p)
                if len(matches)>1:return matches # region-filtered ambiguity is conclusive
        if len(matches)==1:
            coverage=[c for c in self.coverage() if c['key'].startswith('osm:')]
            with self.connect() as db:self.profile_place(matches[0],coverage,db)
        return matches

    def counts(self):
        with self.connect() as db:return dict(db.execute('SELECT kind,count(*) FROM places GROUP BY kind'))

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
