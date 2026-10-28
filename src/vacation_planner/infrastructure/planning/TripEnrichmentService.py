from __future__ import annotations

import copy
import hashlib
import html
import json
from pathlib import Path
import re
import subprocess
import time
from urllib.parse import quote, urlencode, urlsplit

from .TripStore import timestamp


class TripEnrichmentService:
    """Bounded, explicit enrichment using exact Wikimedia identities only."""
    API='https://commons.wikimedia.org/w/api.php'
    WIKIDATA='https://www.wikidata.org/w/api.php'
    ALLOWED=('cc0','public domain','cc by','cc-by','cc by-sa','cc-by-sa')

    def __init__(self,store,http):
        self.store,self.http=store,http
        self.cache_dir=Path(store.path).parent/'image-cache';self.cache_dir.mkdir(parents=True,exist_ok=True)

    def enrich(self,trip,context,emit=lambda *args:None):
        result=copy.deepcopy(trip);destination=result.get('destination') or {}
        emit('phase','Ortsangaben aktualisieren')
        try:
            places=self.http and self._refresh_places(destination,context)
            if places:
                self._merge_places(result,places)
        except (OSError,ValueError,KeyError,json.JSONDecodeError) as exc:emit('warning','Ortsangaben konnten nicht aktualisiert werden: '+str(exc))
        targets=[('destination',destination)]
        targets += [('lodging',x) for x in (result.get('lodgings') or [])[:3]]
        targets += [('activity',x) for x in (result.get('activities') or [])[:8]]
        for kind,item in targets:
            context.check();emit('phase','Passendes Bild prüfen: '+item.get('name','Eintrag'))
            try:
                image=self._exact_image(item,kind,context)
                if image:item['image']=image
            except (OSError,ValueError,KeyError,json.JSONDecodeError) as exc:emit('warning',item.get('name','Eintrag')+': kein verwendbares Bild ('+str(exc)+')')
        result['enriched_at']=timestamp();return result

    def _refresh_places(self,destination,context):
        if not destination.get('source'):return None
        body,stamp=self.http.get(destination['source'],context)
        from .WikivoyageParser import WikivoyageParser
        return WikivoyageParser().parse(body,destination,stamp)

    @staticmethod
    def _merge_places(trip,places):
        by_id={x.get('id'):x for x in places.get('lodgings',[])+places.get('activities',[]) if x.get('id')}
        for group in ('lodgings','activities'):
            for item in trip.get(group,[]):
                fresh=by_id.get(item.get('id'))
                if fresh:
                    for key in ('address','url','latitude','longitude','retrieved_at','source_updated'):
                        if fresh.get(key) not in (None,''):item[key]=fresh[key]

    def _exact_image(self,item,kind,context):
        title=''
        identity=str(item.get('id',''))
        if re.fullmatch(r'Q\d+',identity):
            data,_=self.http.json(self.WIKIDATA+'?'+urlencode({'action':'wbgetentities','ids':identity,'props':'claims','format':'json','origin':'*'}),context)
            claim=data.get('entities',{}).get(identity,{}).get('claims',{}).get('P18',[])
            if claim:title='File:'+claim[0]['mainsnak']['datavalue']['value']
        elif kind=='destination' and item.get('source'):
            page=quote(item['source'].rstrip('/').rsplit('/',1)[-1],safe='')
            api='https://de.wikivoyage.org/w/api.php?'+urlencode({'action':'query','prop':'pageimages','piprop':'name','titles':page,'format':'json','origin':'*'})
            data,_=self.http.json(api,context);pages=data.get('query',{}).get('pages',{})
            if pages:title=next(iter(pages.values())).get('pageimage','')
            if title and not title.startswith('File:'):title='File:'+title
        if not title:return None
        data,_=self.http.json(self.API+'?'+urlencode({'action':'query','prop':'imageinfo','iiprop':'url|extmetadata','iiurlwidth':1400,'titles':title,'format':'json','origin':'*'}),context)
        page=next(iter(data.get('query',{}).get('pages',{}).values()),{});info=(page.get('imageinfo') or [{}])[0];meta=info.get('extmetadata') or {}
        license_name=self._plain(meta.get('LicenseShortName',{}).get('value',''))
        usage=self._plain(meta.get('UsageTerms',{}).get('value',''))
        if not any(x in (license_name+' '+usage).casefold() for x in self.ALLOWED):raise ValueError('Lizenz nicht in der Freigabeliste')
        url=info.get('thumburl') or info.get('url','');source=info.get('descriptionurl','')
        if not url or urlsplit(url).scheme!='https' or not source:raise ValueError('Bildquelle unvollständig')
        suffix=Path(urlsplit(url).path).suffix.lower()
        if suffix not in ('.jpg','.jpeg','.png','.webp'):suffix='.jpg'
        path=self.cache_dir/(hashlib.sha256(url.encode()).hexdigest()+suffix)
        if not path.exists():self._download(url,path,context)
        return {'title':title.removeprefix('File:'),'cache_path':str(path),'source_page':source,
                'author':self._plain(meta.get('Artist',{}).get('value',''))[:180],
                'license':license_name or usage,'retrieved_at':timestamp(),'assigned_to':item.get('name','')}

    @staticmethod
    def _plain(value):return re.sub(r'\s+',' ',html.unescape(re.sub('<[^>]+>',' ',value or ''))).strip()

    @staticmethod
    def _download(url,path,context):
        temp=path.with_suffix(path.suffix+'.part');process=subprocess.Popen(['curl','--silent','--show-error','--location','--max-redirs','3','--proto','=https','--proto-redir','=https','--max-time','20','--connect-timeout','8','--max-filesize','8000000','--output',str(temp),url])
        try:
            while process.poll() is None:context.check();time.sleep(.1)
            if process.returncode or not temp.exists() or temp.stat().st_size<500:raise OSError('Bildabruf fehlgeschlagen')
            temp.replace(path)
        finally:
            if process.poll() is None:process.kill();process.wait()
            if temp.exists():temp.unlink()
