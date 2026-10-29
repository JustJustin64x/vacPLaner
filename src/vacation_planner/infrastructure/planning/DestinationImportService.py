"""Explicit country setup and small regional updates, never startup downloads."""
import hashlib
import io
import json
import re
import subprocess
import tempfile
import time
from pathlib import Path
from urllib.parse import urlencode
import zipfile

from .PublicHttpClient import PublicHttpClient
from .TripStore import timestamp

COUNTRIES={'AL':'Albanien','AD':'Andorra','AT':'Österreich','BE':'Belgien','BA':'Bosnien und Herzegowina','BG':'Bulgarien','HR':'Kroatien',
 'CY':'Zypern','CZ':'Tschechien','DK':'Dänemark','EE':'Estland','FI':'Finnland','FR':'Frankreich','DE':'Deutschland','GR':'Griechenland',
 'HU':'Ungarn','IS':'Island','IE':'Irland','IT':'Italien','LV':'Lettland','LI':'Liechtenstein','LT':'Litauen','LU':'Luxemburg',
 'MT':'Malta','MD':'Moldau','MC':'Monaco','ME':'Montenegro','NL':'Niederlande','MK':'Nordmazedonien','NO':'Norwegen','PL':'Polen',
 'PT':'Portugal','RO':'Rumänien','SM':'San Marino','RS':'Serbien','SK':'Slowakei','SI':'Slowenien','ES':'Spanien','SE':'Schweden',
 'CH':'Schweiz','UA':'Ukraine','GB':'Vereinigtes Königreich','VA':'Vatikanstadt','XK':'Kosovo','AX':'Åland','FO':'Färöer'}
REGIONS={
 'Tirol: Inntal und Innsbruck':(47.12,11.10,47.40,11.65),
 'Slowenien: Bled und Bohinj':(46.22,13.75,46.48,14.25),
 'Kroatien: Split und Trogir':(43.40,16.10,43.65,16.60),
}
EXTRACTS={
 'Tirol: Inntal und Innsbruck':('https://download.openstreetmap.fr/extracts/europe/austria/tirol-latest.osm.pbf','Tirol, etwa 116 MiB'),
 'Slowenien: Bled und Bohinj':('https://download.geofabrik.de/europe/slovenia-latest.osm.pbf','Slowenien, etwa 299 MB'),
 'Kroatien: Split und Trogir':('https://download.geofabrik.de/europe/croatia-latest.osm.pbf','Kroatien, etwa 191 MB'),
}
SETTLEMENTS={'PPL','PPLA','PPLA2','PPLA3','PPLA4','PPLA5','PPLC','PPLL'}
REGION_CODES={'LK','LKS','BAY','BAYS','MTS','MT','PK','PRK','RESN','RGN'}


class DestinationImportService:
    def __init__(self,inventory,http=None):self.inventory,self.http=inventory,http or PublicHttpClient()

    def download(self,url,path,context,emit):
        context.consume()
        process=subprocess.Popen(['curl','--silent','--show-error','--fail','--location','--proto','=https','--proto-redir','=https',
            '--connect-timeout','10','--max-time',str(min(600,max(1,context.deadline-time.monotonic()))),
            '--max-filesize','350000000','--user-agent',PublicHttpClient.USER_AGENT,'--output',str(path),url],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
        last=0
        try:
            while process.poll() is None:
                context.check()
                if time.monotonic()-last>1:
                    emit('phase',f'Download {url.rsplit("/",1)[-1]}: {(path.stat().st_size if path.exists() else 0)/1048576:.1f} MiB geladen');last=time.monotonic()
                context.cancel.wait(.1)
            if process.returncode:raise OSError('Download fehlgeschlagen (HTTP-/Netzwerkfehler); vorhandener Datenstand bleibt nutzbar.')
        finally:
            if process.poll() is None:process.kill()
            process.communicate()

    @staticmethod
    def parse_country(archive,code,admin_names=None,context=None):
        names=admin_names or {};stamp=timestamp()
        with zipfile.ZipFile(archive) as z:
            info=z.getinfo(code+'.txt')
            if info.file_size>1500000000:raise ValueError('Entpackte Länderdatei überschreitet das Sicherheitslimit.')
            with z.open(info) as raw:
                for index,line in enumerate(io.TextIOWrapper(raw,encoding='utf-8')):
                    if context and index%500==0:context.check()
                    fields=line.rstrip('\n').split('\t')
                    if len(fields)!=19:raise ValueError('Ungültiges GeoNames-Zeilenformat; Import zurückgerollt.')
                    gid,name,ascii_name,alternate,lat,lon,feature_class,feature_code,country,cc2,a1,a2,a3,a4,population,elevation,dem,zone,modified=fields
                    if country!=code:continue
                    kind='settlement' if feature_class=='P' and feature_code in SETTLEMENTS else 'region' if feature_code in REGION_CODES and feature_class in ('H','T','L') else None
                    if not kind:continue
                    lat,lon=float(lat),float(lon)
                    if not -90<=lat<=90 or not -180<=lon<=180:raise ValueError('Ungültige GeoNames-Koordinaten')
                    region=names.get(code+'.'+a1,code+' · Verwaltung '+a1)
                    yield dict(id='geonames:'+gid,geonames_id=gid,name=name,aliases=list(dict.fromkeys([ascii_name]+alternate.split(','))),
                        latitude=lat,longitude=lon,code=code,country=COUNTRIES[code],admin1=a1,admin2=a2,admin3=a3,admin4=a4,
                        region=region,regions=[region,code+'.'+a1],regional_name=region,base_name=name,kind=kind,
                        type='Region' if kind=='region' else 'Großstadt' if int(population or 0)>=100000 else 'Klein-/Mittelstadt' if feature_code in ('PPLC','PPLA','PPLA2','PPLA3','PPLA4','PPLA5') or int(population or 0)>=10000 else 'Dorf/Ferienort',
                        feature_class=feature_class,feature_code=feature_code,population=int(population or 0),elevation=elevation,timezone=zone,
                        source='https://www.geonames.org/'+gid+'/',source_updated=modified,source_checked_at=stamp,license='CC BY 4.0',
                        coordinate_source='https://www.geonames.org/'+gid+'/',coordinate_note='GeoNames-Ortskoordinate; keine Unterkunftszufahrt',
                        area_id=code+':'+a1+':'+a2,interests=[],landscapes=[],attributions=[{'label':'GeoNames · CC BY 4.0','url':'https://www.geonames.org/about.html'}])

    def import_countries(self,codes,context,emit=lambda *a:None):
        codes=list(dict.fromkeys(codes))
        if not codes or any(c not in COUNTRIES for c in codes):raise ValueError('Bitte unterstützte europäische Ländercodes wählen.')
        folder=self.inventory.path.parent/'destination-downloads';folder.mkdir(exist_ok=True)
        admin_path=folder/'admin1CodesASCII.txt'
        if not admin_path.exists() or time.time()-admin_path.stat().st_mtime>30*86400:
            with tempfile.TemporaryDirectory(dir=folder) as temp:
                staged=Path(temp)/'admin.txt';self.download('https://download.geonames.org/export/dump/admin1CodesASCII.txt',staged,context,emit)
                context.check();staged.replace(admin_path)
        names={}
        for line in admin_path.read_text().splitlines():
            parts=line.split('\t')
            if len(parts)>=2:names[parts[0]]=parts[1]
        result=[]
        for code in codes:
            context.check();url='https://download.geonames.org/export/dump/'+code+'.zip'
            with tempfile.TemporaryDirectory(dir=folder) as temp:
                path=Path(temp)/(code+'.zip');emit('phase','Länderbestand herunterladen: '+COUNTRIES[code])
                self.download(url,path,context,emit)
                digest=hashlib.sha256(path.read_bytes()).hexdigest()
                emit('phase','Orte und Urlaubsregionen importieren: '+COUNTRIES[code]+' · bisheriger Stand bleibt bis Abschluss nutzbar')
                meta=self.inventory.replace_country(code,self.parse_country(path,code,names,context),
                    {'name':COUNTRIES[code],'source':url,'sha256':digest,'license':'CC BY 4.0','compressed_bytes':path.stat().st_size},context)
                result.append(meta);emit('phase',f"{COUNTRIES[code]}: {meta['kinds'].get('settlement',0)} Aufenthaltsorte und {meta['kinds'].get('region',0)} Regionen importiert.")
        return result

    def update_region(self,name,bounds,context,emit=lambda *a:None,force=False):
        south,west,north,east=map(float,bounds)
        if not (-90<=south<north<=90 and -180<=west<east<=180) or north-south>1 or east-west>1:raise ValueError('Merkmalsabfrage auf höchstens 1 × 1 Grad begrenzen.')
        key=name+':'+','.join(f'{x:.4f}' for x in bounds)
        old=next((x for x in self.inventory.coverage() if x['key']=='osm:'+key),None)
        from datetime import datetime, timezone
        if old and not force and (datetime.now(timezone.utc)-datetime.fromisoformat(old['updated_at'])).total_seconds()<30*86400:
            emit('phase',name+': lokale Merkmale aus Cache (bis 30 Tage)');return old
        box=','.join(str(x) for x in (south,west,north,east))
        query='[out:json][timeout:18][maxsize:32000000];('+''.join([
            f'nwr["amenity"~"^(bar|pub|nightclub|restaurant)$"]({box});',f'nwr["tourism"~"^(hotel|guest_house|apartment|chalet|camp_site|museum|gallery|artwork|attraction)$"]({box});',
            f'nwr["natural"~"^(beach|water|peak|ridge)$"]({box});',f'nwr["leisure"~"^(swimming_area|water_park|nature_reserve|park)$"]({box});',
            f'nwr["boundary"~"^(national_park|protected_area)$"]({box});',f'nwr["historic"~"^(castle|archaeological_site|monument|ruins)$"]({box});',
            f'rel["type"="route"]["route"="hiking"]({box});',f'node["place"~"^(town|village|hamlet)$"]({box});'])+');out center tags;'
        url='https://overpass.private.coffee/api/interpreter?'+urlencode({'data':query})
        emit('phase',name+': gebündelte regionale OSM-Abfrage; keine Einzelabfragen je Ort')
        data,stamp=self.http.json(url,context)
        if not isinstance(data.get('elements'),list) or data.get('remark'):raise ValueError('Overpass lieferte unvollständige Daten; bisheriger Stand bleibt erhalten.')
        return self.inventory.replace_features(key,list(bounds),data['elements'],context,'https://overpass.private.coffee/')

    def enrich_wikidata(self,ids,context,emit=lambda *a:None):
        ids=list(dict.fromkeys(x for x in ids if re.fullmatch(r'Q[1-9]\d*',x)))[:20]
        ids=self.inventory.stale_entity_ids(ids)
        if not ids:return 0
        emit('phase',f'Wikidata: höchstens {len(ids)} bereits identifizierte Objekte ergänzen')
        url='https://www.wikidata.org/w/api.php?'+urlencode({'action':'wbgetentities','ids':'|'.join(ids),'props':'claims|sitelinks|labels','languages':'de|en','format':'json'})
        data,stamp=self.http.json(url,context);entities=data.get('entities')
        if not isinstance(entities,dict):raise ValueError('Wikidata-Identitäten fehlen')
        context.check();self.inventory.save_entities(entities);return len(entities)

    def import_extract(self,name,context,emit=lambda *a:None):
        if name not in EXTRACTS:raise ValueError('Für diese Region ist kein geprüfter Download hinterlegt. Eine lokale PBF-Datei kann separat importiert werden.')
        url,description=EXTRACTS[name];folder=self.inventory.path.parent/'destination-downloads';folder.mkdir(exist_ok=True)
        target=folder/url.rsplit('/',1)[-1]
        # Explicit manual action only; reuse a recent completed download.
        if not target.exists() or time.time()-target.stat().st_mtime>7*86400:
            with tempfile.TemporaryDirectory(dir=folder) as temp:
                staged=Path(temp)/target.name;emit('phase','Regionalauszug herunterladen: '+description)
                self.download(url,staged,context,emit);context.check()
                import osmium
                reader=osmium.io.Reader(str(staged));reader.close()  # Reject an HTML/error document before replacing cache.
                staged.replace(target)
        return self.import_pbf(target,name,REGIONS[name],context,emit,url)

    def import_pbf(self,path,name,bounds,context,emit=lambda *a:None,source='Lokaler OSM-Regionalauszug'):
        from .OsmRegionalExtract import extract_features
        elements=extract_features(path,bounds,context,emit)
        key=name+':'+','.join(f'{x:.4f}' for x in bounds)
        meta=self.inventory.replace_features(key,list(bounds),elements,context,source)
        meta.update(method='regional_pbf',download_bytes=Path(path).stat().st_size)
        import osmium
        reader=osmium.io.Reader(str(path))
        try:meta['source_data_timestamp']=reader.header().get('osmosis_replication_timestamp') or reader.header().get('timestamp') or 'nicht angegeben'
        finally:reader.close()
        digest=hashlib.sha256()
        with Path(path).open('rb') as stream:
            while chunk:=stream.read(1048576):context.check();digest.update(chunk)
        meta['sha256']=digest.hexdigest()
        with self.inventory.connect() as db:db.execute('UPDATE datasets SET payload=? WHERE key=?',(json.dumps(meta,ensure_ascii=False),meta['key']))
        emit('phase',f"{name}: {meta['count']} regionale Merkmale aus PBF importiert.")
        qids=[e.get('tags',{}).get('wikidata','') for e in sorted(elements,key=lambda e:not e.get('tags',{}).get('place'))]
        try:self.enrich_wikidata(qids,context,emit)
        except (OSError,ValueError) as exc:emit('phase','OSM-Daten nutzbar; Wikidata-Ergänzung fehlt: '+str(exc))
        return meta
