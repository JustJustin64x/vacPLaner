from urllib.parse import urlsplit, urljoin, unquote
import copy
import math
import hashlib
import re
from bs4 import BeautifulSoup
from ...core.domain.value_objects.GeographicCoordinates import GeographicCoordinates


def safe_url(value):
    value = (value or '').strip()
    try:
        parsed = urlsplit(value)
        return value if parsed.scheme in ('https','http') and parsed.hostname and not parsed.username else ''
    except ValueError:
        return ''


class WikivoyageParser:
    """Parse explicit German Wikivoyage vCard fields, never first-price text.

    Travel-guide prices lack travel dates, rooms, availability and fee scope.
    They deliberately remain outside the budget calculation.
    """
    TYPE_MAP = {'hotel':'Hotel','hotel_garni':'Hotel','apartment':'Ferienwohnung','holiday_flat':'Ferienwohnung',
                'holiday_home':'Ferienwohnung','guest_house':'Hotel','guesthouse':'Hotel','pension':'Hotel','campsite':'Camping','camping':'Camping','camp_site':'Camping'}
    def parse(self, html, destination, stamp):
        soup = BeautifulSoup(html,'html.parser')
        lodging, activities, seen = [],[],set()
        for card in soup.select('.vcard[data-name]'):
            name = card.get('data-name','').strip()
            groups=set(re.split(r'[,;\s]+',card.get('data-group','').lower()))
            kinds=set(re.split(r'[,;\s]+',card.get('data-type','').lower()))
            group=next((g for g in ('sleep','do','see','drink','eat','nature','view') if g in groups),'')
            kind=next(iter(sorted(kinds)),'')
            identity = card.get('data-wikidata')
            marker = card.select_one('[data-lat][data-lon]')
            lat,lon,distance = None,None,None
            if marker:
                try:
                    lat,lon = float(marker['data-lat']),float(marker['data-lon'])
                    if not math.isfinite(lat) or not math.isfinite(lon) or not -90<=lat<=90 or not -180<=lon<=180:
                        raise ValueError('Ungültige Koordinaten')
                    distance = GeographicCoordinates(lat,lon).calculate_distance_in_kilometers_to(
                        GeographicCoordinates(destination['latitude'],destination['longitude']))
                except (ValueError,KeyError):
                    lat,lon = None,None
            # Same name alone is not sufficient; nearby matching identities are deduplicated.
            key = identity or (name.casefold(),round(lat,3) if lat is not None else None,
                              round(lon,3) if lon is not None else card.get('id',str(len(seen))))
            if not name or key in seen:
                continue
            seen.add(key)
            source = destination['source']+('#'+card['id'] if card.get('id') else '')
            record = dict(id=identity or hashlib.sha256(repr(key).encode()).hexdigest()[:20],name=name,
                          latitude=lat,longitude=lon,distance_km=distance,source=source,
                          retrieved_at=stamp,url=safe_url(card.get('data-url')) or source,
                          link_kind='Allgemeiner Anbieterlink' if safe_url(card.get('data-url')) else 'Quelleneintrag',
                          data_status='Reiseführer-Eintrag; kein Verfügbarkeitsnachweis')
            metadata = card.select_one('.voy-listing-lastedit')
            record['source_updated'] = metadata.get_text(' ',strip=True) if metadata else 'Letzte Quellenpflege unbekannt'
            address = card.select_one('.voy-listing-address')
            record['address'] = address.get_text(' ',strip=True) if address else 'Genaue Adresse unbekannt'
            if group == 'sleep':
                accommodation_type = next((self.TYPE_MAP[k] for k in sorted(kinds) if k in self.TYPE_MAP),None)
                # Known editorial mistagging: a named campsite must not become a hotel.
                if 'camping' in name.casefold():
                    accommodation_type = 'Camping'
                if not accommodation_type:
                    continue
                record.update(type=accommodation_type,amenities={},capacity=None,rooms=None,
                              booking_status='Preis, freie Zimmer und Belegung zum Reisedatum unbekannt',
                              price=dict(label='Unterkunft für Gruppe und Aufenthalt inkl. Pflichtgebühren',
                                         low=None,high=None,status='unbekannt',source=source,retrieved_at=stamp,
                                         scope='Keine datums- und belegungsbezogenen Angebotsdaten',method=''))
                lodging.append(record)
            elif group in ('do','see','drink','eat','nature','view'):
                topics = []
                if kinds & {'bar','pub','nightclub','disco','club','dance_club'}: topics += ['Feiern']
                if group=='eat': topics += ['Restaurants']
                if group=='see': topics += ['Kultur']
                if group in ('nature','view'): topics += ['Natur']
                if kinds & {'beach','swimming','swimming_pool','bathing','lido','open_air_bath','public_bath'}: topics += ['Baden']
                if kinds & {'hiking','hiking_trail','walking_trail','nature_trail'}: topics += ['Wandern','Natur']
                if kinds & {'lake','mountain','peak','viewpoint','waterfall','national_park','park','nature_reserve','forest'}: topics += ['Natur']
                if kinds & {'mountain','peak'}: topics += ['Berge']
                if kinds & {'nightclub','bar','pub','disco','dance_club'}: topics += ['Feiern']
                if kinds & {'event','festival'}: continue
                price_element = card.select_one('.voy-listing-price')
                stated_price = price_element.get_text(' ',strip=True) if price_element else ''
                stated_price = re.sub(r'^Preis:\s*', '', stated_price, flags=re.I)
                free = bool(re.fullmatch(r'(?:Eintritt\s*:?\s*)?(?:frei|kostenlos|gratis)\.?', stated_price, flags=re.I))
                if free:
                    topics.append('Kostenlos')
                topics = sorted(set(topics))
                record.update(topics=topics,type=','.join(sorted(kinds)),topic_basis='Explizite vCard-Gruppe/Typ; kostenlos nur aus unbedingtem Preisfeld',
                              description=f"{name}: Reiseführer-Eintrag für {', '.join(topics) or 'Unternehmungen'}. Öffnung und Zugang bitte prüfen.",
                              price_status=('Reiseführer nennt kostenlosen Eintritt; aktuell nicht bestätigt' if free else 'Eintritt unbekannt; nicht automatisch kostenlos'),duration='Dauer unbekannt')
                activities.append(record)
        related=[]
        prefix=unquote(destination['source']).rstrip('/')+'/'
        for link in soup.select('a[href]'):
            url=safe_url(urljoin(destination['source'],link['href'])).split('#')[0].split('?')[0]
            if unquote(url).startswith(prefix) and url not in [p['source'] for p in related]:
                related.append(dict(source=url,name=unquote(url.rsplit('/',1)[-1]),relation='Nachgewiesene Unterseite'))
        return dict(lodgings=lodging,activities=activities,related_pages=related[:2])

    def migrate_snapshot(self,data):
        """Historical identities remain usable; old broad inference is not evidence."""
        result=copy.deepcopy(data)
        for item in result.get('activities',[]):
            kinds=set(re.split(r'[,;\s]+',item.get('type','')))
            if not kinds & {'hiking','hiking_trail','walking_trail','nature_trail'}:
                item['topics']=[t for t in item['topics'] if t!='Wandern']
            if not kinds & {'beach','swimming','swimming_pool','bathing','lido','open_air_bath','public_bath'}:
                item['topics']=[t for t in item['topics'] if t!='Baden']
            item['data_status']=item.get('data_status','')+'; historischer Stand, Klassifikation v4'
        return result
