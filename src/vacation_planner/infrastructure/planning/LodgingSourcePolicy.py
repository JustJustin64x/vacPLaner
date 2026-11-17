"""Ephemeral exact-URL grants from a directory/observed HTML, never from AI.

This policy does not replace DNS/TLS/robots checks in ResearchHttp. No credential,
guest, payment, reservation submission or arbitrary form action is permitted.
"""
import ipaddress
import re
from urllib.parse import urlsplit,urlunsplit,parse_qs,urlencode,unquote


def normalize(url):
    if not isinstance(url,str) or len(url)>2000 or any(ord(c)<=32 for c in url) or '\\' in url:
        raise ValueError('Ungültige Quellenadresse')
    p=urlsplit(url)
    if p.scheme!='https' or not p.hostname or p.username or p.password or p.port not in (None,443):
        raise ValueError('Nur öffentliche HTTPS-Quellen ohne Zugangsdaten')
    host=p.hostname.encode('idna').decode('ascii').lower()
    if host=='localhost' or '.' not in host or host.endswith(('.local','.internal','.localhost','.home','.lan')):
        raise ValueError('Internes Quellenziel gesperrt')
    try:
        ip=ipaddress.ip_address(host)
        if not ip.is_global or ip.is_multicast:raise ValueError('Interne Quellenadresse')
    except ValueError:
        if re.fullmatch(r'[\d.:]+',host):raise ValueError('Numerische Quellenziele gesperrt')
    path=p.path or '/'
    decoded=unquote(unquote(path))
    if '..' in decoded.split('/') or '\\' in decoded or any(ord(c)<32 for c in decoded):raise ValueError('Ungültiger Quellenpfad')
    if any(ord(c)>=127 for c in path+p.query):
        from urllib.parse import quote
        path=quote(path,safe='/%:@-._~');query=quote(p.query,safe='=&%:+,;-._~')
    else:query=p.query
    return urlunsplit(('https',host,path,query,''))


def public_link(url):
    p=urlsplit(url);q=parse_qs(p.query,keep_blank_values=True)
    for k in ('booking','session','token'):q.pop(k,None)
    return urlunsplit((p.scheme,p.netloc,p.path,urlencode({k:v[0] for k,v in q.items()}),''))


class LodgingSourcePolicy:
    BOOKING_HOSTS={'beds24.com','www.beds24.com'}
    def __init__(self,seed,identity):
        if not identity.get('source') or not identity.get('id'):raise ValueError('Unterkunft ohne Quellenidentität')
        self.identity=identity['id'];self.urls=set();self.sites=set();self.objects={};self.rooms=set()
        self.seed=self.grant_seed(seed)

    def _add(self,url):
        url=normalize(url);p=urlsplit(url)
        self.urls.add(url);self.urls.add('https://'+p.netloc+'/robots.txt')
        return url

    def grant_seed(self,url):
        # A directory's legacy HTTP hint is tried at the same HTTPS origin.
        # No plaintext fallback, alternate host, TLS exception or credentials.
        if isinstance(url,str) and url.startswith('http://'):url='https://'+url[7:]
        url=normalize(url);p=urlsplit(url)
        if p.hostname in self.BOOKING_HOSTS:return self.booking_link(url)
        if p.query:raise ValueError('Website-Einstieg mit nicht unterstützten Parametern')
        self.sites.add(p.hostname)
        return self._add(url)

    def site_link(self,url):
        url=normalize(url);p=urlsplit(url)
        if p.hostname not in self.sites or p.query:raise ValueError('Unterseite außerhalb der belegten Website')
        if re.search(r'(?i)(logout|delete|cancel|checkout|payment|login|account|reservations?/)',p.path):
            raise ValueError('Keine Konto-/Transaktionsseite')
        return self._add(url)

    def operator_link(self,url,html,backend_url):
        from .LodgingWebsite import operator_links
        if urlsplit(self.seed).hostname not in self.BOOKING_HOSTS or self.validate_url(backend_url)!=normalize(backend_url):
            raise ValueError('Kein belegter Verzeichnis-Buchungseinstieg')
        if url not in operator_links(html,backend_url):raise ValueError('Kein beobachteter Betreiberlink')
        url=normalize(url);self.sites.add(urlsplit(url).hostname)
        return self.site_link(url)

    def availability_query(self,page,html,query):
        from .LodgingWebsite import availability_form
        self.validate_url(page)
        p=urlsplit(page)
        if p.hostname not in self.sites or p.query or not availability_form(html):raise ValueError('Kein unterstütztes öffentliches Suchformular')
        # Candidate room search, never a group-price interpretation. The final
        # backend selection must independently echo the entire real group.
        parameters=dict(checkin=query.start,checkout=query.end,numadult=max(query.occupancy),numchild=max(len(p.children_ages) for p in query.room_assignments))
        return self._add(urlunsplit((p.scheme,p.netloc,p.path,urlencode(parameters),'')))

    def booking_link(self,url):
        url=normalize(url);p=urlsplit(url)
        if p.hostname not in self.BOOKING_HOSTS or p.path not in ('/booking.php','/booking2.php'):
            raise ValueError('Nicht unterstütztes Buchungssystem')
        q=parse_qs(p.query,keep_blank_values=True)
        if any(len(q.get(k,[]))>1 for k in ('propid','ownerid','roomid')):raise ValueError('Mehrdeutige Objektkennung')
        ids={k:v[0] for k,v in q.items() if k in ('propid','ownerid','roomid') and len(v)==1 and re.fullmatch(r'[1-9]\d{0,11}',v[0])}
        if not ids:raise ValueError('Keine beobachtete Objektkennung')
        self.objects.update(ids)
        # Keep only identity, never a source's action, redirect, guest data or dates.
        return self._add(urlunsplit(('https',p.netloc,p.path,urlencode(ids),'')))

    def query(self,base,parameters,room_fields=()):
        base=normalize(base);p=urlsplit(base)
        if p.hostname not in self.BOOKING_HOSTS or p.path not in ('/booking.php','/booking2.php'):
            raise ValueError('Kein freigegebenes Gastformular')
        self.rooms.update(room_fields)
        allowed={'propid','ownerid','roomid','checkin','numnight','numadult','numchild','lang','multiroom',
                 'booking','width','page','limitstart','checkin_hide','fdate_date','fdate_monthyear'}|self.rooms
        if set(parameters)-allowed:raise ValueError('Nicht erlaubte Formularfelder')
        if not any(k in parameters for k in self.objects):raise ValueError('Objektbezug der Anfrage fehlt')
        for k in ('propid','ownerid','roomid'):
            if k in parameters and str(parameters[k])!=self.objects.get(k):raise ValueError('Unbelegte Objektkennung')
        if 'page' in parameters and parameters['page']!='dates':raise ValueError('Keine Buchungsabschlussaktion')
        for k,v in parameters.items():
            v=str(v)
            if len(v)>80 or any(ord(c)<32 for c in v):raise ValueError('Ungültiger Formularwert')
            if k in self.rooms:
                if k.startswith('br'):
                    if v not in ('Book','Buchen'):raise ValueError('Unbekannte Auswahlschaltfläche')
                elif not re.fullmatch(r'\d{1,2}',v):raise ValueError('Ungültige Zimmerbelegung')
        return self._add(urlunsplit(('https',p.netloc,p.path,urlencode(parameters),'')))

    def responsive_query(self,base,parameters,observed_fields,multi):
        """GET selection only, with field names actually delivered by formlook."""
        extra=set(observed_fields)
        if any(not re.fullmatch(r'(sr|br)\d{1,2}-\d{1,12}|(?:naa|ncc)\d{1,2}-\d{1,2}-\d{1,12}',k) for k in extra):
            raise ValueError('Unzulässige responsive Quellfelder')
        q=dict(parameters)
        if multi:
            if q.pop('page',None)!='book3' or q.pop('bookmult',None)!='':raise ValueError('Keine reine Auswahlaktion')
        # Reuse all existing identity/value checks. page=book is never allowed.
        url=self.query(base,q,extra)
        if multi:
            p=urlsplit(url);url=self._add(urlunsplit((p.scheme,p.netloc,p.path,p.query+'&page=book3&bookmult=','')))
        return url

    def validate_url(self,url):
        url=normalize(url)
        if url not in self.urls:raise ValueError('Quellenziel ohne auftragsgebundenen Herkunftsnachweis')
        return url

    def redirect(self,current,target):
        current=self.validate_url(current);target=normalize(target);a,b=urlsplit(current),urlsplit(target)
        if target in self.urls:return
        # Only a proven website's own/www canonicalization, no arbitrary domains.
        if a.hostname in self.sites and a.hostname.removeprefix('www.')==b.hostname.removeprefix('www.') and not b.query:
            self.sites.add(b.hostname);self.site_link(target);return
        if a.hostname in self.BOOKING_HOSTS and b.hostname in self.BOOKING_HOSTS and a.path==b.path and a.query==b.query:
            self._add(target);return
        raise ValueError('Weiterleitung außerhalb der belegten Quellenkette')

    @staticmethod
    def robots_redirect(a,b):
        x,y=urlsplit(a),urlsplit(b)
        return x.path==y.path=='/robots.txt' and not y.query and x.hostname.removeprefix('www.')==y.hostname.removeprefix('www.')


class LodgingDirectoryPolicy:
    """One code-generated geographic query, not arbitrary Overpass programs."""
    def __init__(self,url):
        p=urlsplit(url)
        if p.hostname not in ('overpass.private.coffee','ovp.dresel.systems') or p.path!='/api/interpreter':raise ValueError('Unbekannte Verzeichnisquelle')
        self.urls={normalize(url),'https://'+p.hostname+'/robots.txt'}
    def validate_url(self,url):
        url=normalize(url)
        if url not in self.urls:raise ValueError('Außerhalb der begrenzten Verzeichnisabfrage')
        return url
    def redirect(self,a,b):self.validate_url(b)
    @staticmethod
    def robots_redirect(a,b):return False
