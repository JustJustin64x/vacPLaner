"""Bounded deterministic identity/link extraction; HTML is data, never instructions."""
import re
import unicodedata
import json
import html as html_module
from urllib.parse import urljoin,urlsplit
from bs4 import BeautifulSoup


def normalized(value):
    return ' '.join(re.sub(r'[^\w]+',' ',unicodedata.normalize('NFKD',str(value)).casefold()).split())


def name_in_text(name,text):
    name=normalized(name)
    distinctive=' '.join(t for t in name.split() if t not in ('hotel','hostel','garni','gmbh'))
    branded=len(distinctive)>=8 or (len(distinctive)>=6 and any(c.isdigit() for c in distinctive))
    return len(name)>=5 and (name in text or (branded and distinctive in text))


def matches_name(item,html):
    soup=BeautifulSoup(html,'html.parser')
    for n in soup.select('script,style'):n.decompose()
    text=normalized(soup.get_text(' ',strip=True)+' '+' '.join(n.get('content','') for n in soup.select('meta[name="description"],meta[property="og:title"]')))
    return name_in_text(item['name'],text)


def operator_links(html,url):
    """Only actual backend anchors to an operator home/imprint; at most two."""
    soup=BeautifulSoup(html,'html.parser');links=[]
    for a in soup.select('a[href]'):
        link=urljoin(url,a['href']);p=urlsplit(link)
        if p.scheme=='https' and p.hostname not in ('beds24.com','www.beds24.com') and not p.query and (p.path in ('','/') or re.search(r'(?i)(impressum|imprint|contact|kontakt)',p.path)):
            if link not in links:links.append(link)
    return links[:2]


def availability_form(html):
    soup=BeautifulSoup(html,'html.parser')
    form=soup.select_one('form.acantic-beds24-search-form')
    if not form or form.get('method','get').lower()!='get' or form.get('action'):return False
    fields={n['name'] for n in form.select('input[name],select[name]')}
    return fields=={'checkin','checkout','numadult','numchild'}


def matches_identity(item,html):
    soup=BeautifulSoup(html,'html.parser')
    structured=[]
    for script in soup.select('script[type="application/ld+json"]')[:8]:
        try:data=json.loads(script.string or script.get_text())
        except (ValueError,TypeError):continue
        structured+=data if isinstance(data,list) else [data]
    structured=[x for x in structured if isinstance(x,dict)][:20]
    structured_text=' '.join(str(x.get('name',''))+' '+str(x.get('address','')) for x in structured)
    for n in soup.select('script,style'):n.decompose()
    metadata=' '.join(n.get('content','') for n in soup.select('meta[name="description"],meta[property="og:title"]'))
    metadata+=' '+' '.join(n.get('alt','') for n in soup.select('img[alt]'))
    text=normalized(soup.get_text(' ',strip=True)+' '+metadata+' '+structured_text);name=normalized(item['name'])
    if not name_in_text(item['name'],text):return False
    tags=item.get('identity_tags',{})
    postal=tags.get('addr:postcode','');street=normalized(tags.get('addr:street',''))
    phone=re.sub(r'\D','',tags.get('phone') or tags.get('contact:phone') or '')
    address=normalized(item.get('address',''))
    geo_match=False
    from ...core.planning.PlaceResearch import distance
    for data in structured:
        geo=data.get('geo')
        if isinstance(geo,dict) and item.get('latitude') is not None and item.get('longitude') is not None:
            try:
                lat,lon=float(geo['latitude']),float(geo['longitude'])
                if -90<=lat<=90 and -180<=lon<=180:
                    geo_match=geo_match or distance(item,{'latitude':lat,'longitude':lon})<.2
            except (KeyError,TypeError,ValueError):pass
    return bool((postal and re.search(r'(?<!\d)'+re.escape(postal)+r'(?!\d)',text)) or
                (len(street)>5 and street in text and str(tags.get('addr:housenumber','')) in text) or
                (len(phone)>=8 and phone[-8:] in re.sub(r'\D','',soup.get_text())) or
                (len(address)>15 and address not in ('genaue adresse unbekannt','anschrift unbekannt') and address in text) or geo_match)


def extract_links(html,url):
    soup=BeautifulSoup(html,'html.parser');booking=[];pages=[];systems=[];identity_pages=[]
    for n in soup.select('a[href],iframe[src],iframe[data-src],iframe[data-lazy-src],form[action]'):
        raw=n.get('href') or n.get('data-src') or n.get('data-lazy-src') or n.get('src') or n.get('action')
        if not raw:continue
        link=urljoin(url,raw);p=urlsplit(link)
        if p.scheme=='http' and (p.hostname in ('beds24.com','www.beds24.com') or p.hostname==urlsplit(url).hostname):
            link='https://'+link[7:];p=urlsplit(link)
        if p.scheme!='https':continue
        if p.hostname==urlsplit(url).hostname and re.search(r'(?i)(kontakt|contact|impressum|imprint)',p.path) and link not in identity_pages:
            identity_pages.append(link)
        known={'smoobu.com':'Smoobu','booking.com':'Booking.com','profitroom.com':'Profitroom',
               'cubilis.eu':'Cubilis','simplebooking.it':'SimpleBooking','onepagebooking.com':'OnePageBooking',
               'seekda.com':'Seekda','bookings.ihotelier.com':'iHotelier'}
        for host,label in known.items():
            if p.hostname==host or (p.hostname or '').endswith('.'+host):
                record={'system':label,'variant':'observed-link-only','url':link}
                if record not in systems:systems.append(record)
        if p.hostname in ('beds24.com','www.beds24.com') and p.path in ('/booking.php','/booking2.php'):
            if link not in booking:booking.append(link)
        elif p.hostname==urlsplit(url).hostname and re.search(r'(?i)(buch|book|r[eé]serv|rezerw|zimmer|rooms|disponibilit|chambres|prenota|availability)',n.get_text(' ',strip=True)+' '+p.path):
            if link not in pages:pages.append(link)
    # Explicit widget URLs in configuration/onclick attributes, without executing JS.
    raw=html_module.unescape(html).replace(r'\/', '/')
    for link in re.findall(r'https?://(?:www\.)?beds24\.com/booking(?:2)?\.php\?[^\s\x22\x27<>]+',raw):
        if link.startswith('http://'):link='https://'+link[7:]
        if link not in booking:booking.append(link)
    pages.sort(key=lambda link:0 if re.search(r'(?i)(buch|book|reserv|rezerw|disponibilit|prenota|availability)',urlsplit(link).path) else 1)
    # Tariff-specific links may repeat a property dozens of times. IDs are
    # observed, never enumerated; a property quote validates its own identity.
    from urllib.parse import parse_qs,urlencode,urlunsplit
    objects=[]
    for link in booking:
        p=urlsplit(link);q=parse_qs(p.query)
        key='propid' if 'propid' in q else 'ownerid' if 'ownerid' in q else 'roomid'
        if len(q.get(key,[]))!=1:continue
        ids={key:q[key][0]}
        if key=='propid' and len(q.get('roomid',[]))==1:ids['roomid']=q['roomid'][0]
        canonical=urlunsplit((p.scheme,p.netloc,p.path,urlencode(ids),''))
        if canonical not in objects:objects.append(canonical)
    return {'booking':objects[:4],'pages':pages[:2],'systems':systems[:8],'identity_pages':identity_pages[:1]}
