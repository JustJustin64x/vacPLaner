"""Small public-only, DNS-pinned HTTPS transport for explicit enrichment.

No arbitrary URL/tool access is exposed to the model. No test-network switch.
The wire method is replaceable in tests; production DNS and URL gates stay on.
"""
from __future__ import annotations
import ipaddress
import json
from pathlib import Path
import re
import queue
import socket
import subprocess
import tempfile
import threading
import time
from urllib.parse import unquote, urljoin, urlsplit, urlunsplit
from .PublicHttpClient import PublicHttpClient
from .TripStore import timestamp


class RobotsRules:
    def __init__(self,text,agent='vacationplanner'):
        groups=[];agents=[];rules=[];delay=None;seen=False
        def flush():
            if agents:groups.append((list(agents),list(rules),delay))
        for line in text.splitlines():
            line=line.split('#',1)[0].strip()
            if ':' not in line:continue
            key,value=(x.strip() for x in line.split(':',1));key=key.lower()
            if key=='user-agent':
                if seen:flush();agents=[];rules=[];delay=None;seen=False
                agents.append(value.lower())
            elif agents:
                seen=True
                if key in ('allow','disallow') and value:rules.append((key,value))
                elif key=='crawl-delay':
                    try:delay=max(0,float(value))
                    except ValueError:pass
        flush()
        scored=[(max((len(a) if a!='*' else 0 for a in aa if a=='*' or a in agent),default=-1),rr,dd) for aa,rr,dd in groups]
        best=max((s for s,_,_ in scored),default=-1)
        self.rules=[r for score,rr,_ in scored if score==best and score>=0 for r in rr]
        self.delay=max((d for score,_,d in scored if score==best and d is not None),default=0)

    @staticmethod
    def normal(value):
        def esc(m):
            n=int(m[1],16);c=chr(n)
            return c if c.isascii() and (c.isalnum() or c in '-._~') else '%'+m[1].upper()
        return re.sub(r'%([0-9a-fA-F]{2})',esc,value)

    def allowed(self,url):
        p=urlsplit(url);path=self.normal(p.path+('?' + p.query if p.query else ''))
        matches=[]
        for kind,pattern in self.rules:
            pattern=self.normal(pattern);end=pattern.endswith('$')
            expr='^'+re.escape(pattern[:-1] if end else pattern).replace(r'\*','.*')+('$' if end else '')
            if re.search(expr,path):matches.append((len(pattern.replace('*','').rstrip('$')),kind=='allow'))
        return max(matches,default=(0,True))[1]


class ResearchHttp:
    MAX_BYTES=2_000_000
    _lock=threading.Lock()
    _last={}
    _dns_slots=threading.BoundedSemaphore(2)
    def __init__(self,store):self.store=store;self.memory={};self.robot_memory={};self.audit=[]

    @staticmethod
    def validate_url(url):
        if not isinstance(url,str) or len(url)>2000 or any(ord(c)<=32 or ord(c)>=127 for c in url) or '\\' in url:
            raise ValueError('Ungültige öffentliche Quellenadresse.')
        p=urlsplit(url)
        if p.scheme!='https' or p.username or p.password or p.port not in (None,443) or p.fragment:
            raise ValueError('Nur öffentliche HTTPS-Quellen ohne Zugangsdaten oder Sonderport erlaubt.')
        host=p.hostname
        decoded=unquote(p.path)
        if '..' in decoded.split('/') or '\\' in decoded:raise ValueError('Nicht erlaubter Quellenpfad.')
        permitted=(host=='de.wikivoyage.org' and (p.path=='/robots.txt' or (p.path.startswith('/wiki/') and ':' not in decoded[6:]) or p.path=='/w/api.php') or
                   host=='www.wikidata.org' and (p.path=='/robots.txt' or re.fullmatch(r'/wiki/Special:EntityData/Q[1-9]\d*\.json',decoded) or p.path=='/w/api.php') or
                   host=='commons.wikimedia.org' and p.path in ('/robots.txt','/w/api.php') or
                   host=='upload.wikimedia.org' and (p.path=='/robots.txt' or p.path.startswith('/wikipedia/commons/')))
        if not permitted:raise ValueError('Quelle außerhalb der freigegebenen Hosts/Pfade.')
        if p.query and p.path!='/w/api.php':raise ValueError('Keine beliebigen Abfrageparameter für Quellenartikel erlaubt.')
        if p.path=='/w/api.php':
            from urllib.parse import parse_qs
            q=parse_qs(p.query)
            if q.get('action') not in (['query'],['wbgetentities']) or q.get('format')!=['json']:
                raise ValueError('Nur begrenzte lesende Wikimedia-Abfragen erlaubt.')
        return urlunsplit((p.scheme,host,p.path,p.query,''))

    @staticmethod
    def public_addresses(host,context=None):
        if context is None:infos=socket.getaddrinfo(host,443,type=socket.SOCK_STREAM)
        else:
            deadline=min(context.deadline,time.monotonic()+4)
            while not ResearchHttp._dns_slots.acquire(timeout=.05):
                context.check()
                if time.monotonic()>=deadline:raise TimeoutError('Zeitlimit bei der öffentlichen DNS-Auflösung.')
            output=queue.Queue(maxsize=1)
            def resolve():
                try:output.put((socket.getaddrinfo(host,443,type=socket.SOCK_STREAM),None))
                except Exception as exc:output.put((None,exc))
                finally:ResearchHttp._dns_slots.release()
            threading.Thread(target=resolve,name='public-research-dns',daemon=True).start()
            while True:
                context.check()
                if time.monotonic()>=deadline:raise TimeoutError('Zeitlimit bei der öffentlichen DNS-Auflösung.')
                try:infos,error=output.get(timeout=.05);break
                except queue.Empty:continue
            if error:raise OSError('Öffentliche DNS-Auflösung fehlgeschlagen.') from error
        values=list(dict.fromkeys(info[4][0] for info in infos))
        if not values:raise OSError('Öffentliche Quelle konnte nicht aufgelöst werden.')
        for value in values:
            ip=ipaddress.ip_address(value)
            if not ip.is_global or ip.is_multicast or ip.is_unspecified or ip.is_reserved or ip.is_loopback or (ip.version==6 and (ip.ipv4_mapped or ip.sixtofour or ip.teredo)):
                raise ValueError('Nicht öffentliche DNS-Adresse gesperrt.')
        return values

    def _wire(self,url,ip,context,maximum):
        """Exactly one pinned request, no implicit redirects/proxies/config."""
        host=urlsplit(url).hostname;bound='['+ip+']' if ':' in ip else ip
        with tempfile.TemporaryDirectory(prefix='vac-source-') as directory:
            body=Path(directory)/'body';header=Path(directory)/'header'
            command=['curl','--disable','--silent','--show-error','--noproxy','*','--proxy','','--proto','=https','--max-redirs','0',
                '--resolve',host+':443:'+bound,'--connect-timeout','4','--max-time',str(max(.05,min(18,context.deadline-time.monotonic()))),
                '--max-filesize',str(maximum),'--user-agent',PublicHttpClient.USER_AGENT,'--header','Accept-Encoding: identity',
                '--dump-header',str(header),'--output',str(body),'--write-out','%{json}',url]
            process=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            try:
                while True:
                    context.check()
                    if (body.exists() and body.stat().st_size>maximum) or (header.exists() and header.stat().st_size>65536):raise ValueError('Quellenantwort überschreitet das Größenlimit.')
                    try:out,err=process.communicate(timeout=.05);break
                    except subprocess.TimeoutExpired:continue
                if process.returncode:raise OSError('Begrenzter Quellenabruf fehlgeschlagen (curl '+str(process.returncode)+').')
                meta=json.loads(out)
                if meta.get('remote_ip')!=ip:raise ValueError('Verbindung stimmt nicht mit geprüfter DNS-Adresse überein.')
                if not body.exists() or body.stat().st_size>maximum:raise ValueError('Quellenantwort zu groß oder leer.')
                if not header.exists() or header.stat().st_size>65536:raise ValueError('Quellenheader überschreiten das Größenlimit.')
                raw=body.read_bytes();headers={}
                for line in header.read_text(errors='replace').splitlines():
                    if ':' in line:
                        k,v=line.split(':',1);headers[k.lower().strip()]=v.strip()
                return dict(status=int(meta['http_code']),headers=headers,body=raw)
            finally:
                if process.poll() is None:process.kill();process.communicate()

    def _one(self,url,context,maximum,delay=1.1):
        url=self.validate_url(url);host=urlsplit(url).hostname
        if host in context.disabled:raise OSError('Quelle nach Sperrantwort deaktiviert: '+host)
        while not self._lock.acquire(timeout=.05):context.check()
        try:
            context.wait(max(0,delay-(time.monotonic()-self._last.get(host,0))))
            context.consume();ips=self.public_addresses(host,context)
            # No retry loop: one verified address per request; IPv4 preferred.
            ip=next((x for x in ips if ':' not in x),ips[0]);response=self._wire(url,ip,context,maximum)
            if len(response['body'])>maximum:raise ValueError('Quellenantwort überschreitet das Größenlimit.')
            if response['status'] in (401,403,406,429):context.disabled.add(host)
            self.audit.append(dict(url=url,status=response['status'],bytes=len(response['body']),retrieved_at=timestamp()))
            return response
        finally:self._last[host]=time.monotonic();self._lock.release()

    def _robots(self,url,context):
        p=urlsplit(url);origin='https://'+p.netloc
        if origin in self.robot_memory:return self.robot_memory[origin]
        key='research-robots-v1:'+origin;cached=self.store.cache_get(key,86400)
        if cached:
            text=cached[0]['text']
        else:
            current=origin+'/robots.txt'
            for _ in range(3):
                response=self._one(current,context,128000)
                if response['status'] in (301,302,303,307,308):
                    current=self.validate_url(urljoin(current,response['headers'].get('location','')))
                    if current!=origin+'/robots.txt':raise ValueError('Robots-Weiterleitung außerhalb desselben Robots-Pfads.')
                    continue
                if response['status']==404:text='';break
                if response['status']!=200:raise OSError('Robots-Regeln nicht abrufbar; Quelle bleibt gesperrt.')
                if response['headers'].get('content-type','').split(';')[0].strip().lower()!='text/plain' or response['headers'].get('content-encoding','identity').lower()!='identity':raise ValueError('Robots-Antwort ist keine unterstützte Textdatei.')
                text=response['body'].decode('utf-8');break
            else:raise ValueError('Zu viele Robots-Weiterleitungen.')
            self.store.cache_set(key,dict(text=text),timestamp())
        rules=RobotsRules(text)
        if rules.delay>60:raise ValueError('Crawl-delay überschreitet das interaktive Recherchebudget.')
        self.robot_memory[origin]=rules;return rules

    def fetch(self,url,context,types=('text/html','application/json'),maximum=None):
        maximum=maximum or self.MAX_BYTES;original=self.validate_url(url);current=original
        for _ in range(4):
            current=self.validate_url(current);rules=self._robots(current,context)
            if not rules.allowed(current):raise ValueError('Robots-Regeln sperren diesen Quellenpfad.')
            if current in self.memory:
                cached=self.memory[current]
                if cached['content_type'] not in types or len(cached['body'])>maximum:raise ValueError('Gecachte Quellenantwort passt nicht zu Inhaltstyp/Größenlimit.')
                return dict(cached,cache_used=True,original_url=original)
            response=self._one(current,context,maximum,max(1.1,rules.delay))
            status=response['status'];headers=response['headers']
            if status in (301,302,303,307,308):
                location=headers.get('location')
                if not location:raise ValueError('Weiterleitung ohne Ziel.')
                current=self.validate_url(urljoin(current,location));continue
            if status!=200:
                if status in (401,403,406,429):context.disabled.add(urlsplit(current).hostname)
                raise OSError('Quelle HTTP '+str(status)+'; keine Sperrumgehung.')
            mime=headers.get('content-type','').split(';')[0].strip().lower()
            if mime not in types or headers.get('content-encoding','identity').lower()!='identity':raise ValueError('Nicht unterstützter Inhaltstyp oder Inhaltskodierung.')
            record=dict(body=response['body'],retrieved_at=timestamp(),original_url=original,final_url=current,content_type=mime,cache_used=False)
            self.memory[current]=record;return dict(record)
        raise ValueError('Zu viele Quellenweiterleitungen.')

    def get(self,url,context,headers=None):
        record=self.fetch(url,context)
        return record['body'].decode('utf-8'),record['retrieved_at']

    def json(self,url,context,headers=None):
        r=self.fetch(url,context,('application/json',));return json.loads(r['body']),r['retrieved_at']
