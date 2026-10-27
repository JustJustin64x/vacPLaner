from urllib.parse import urlsplit
import hashlib
import re
from bs4 import BeautifulSoup
from ...core.domain.value_objects.GeographicCoordinates import GeographicCoordinates


def safe_url(value):
    value = (value or '').strip()
    parsed = urlsplit(value)
    return value if parsed.scheme in ('https','http') and parsed.hostname and not parsed.username else ''


class WikivoyageParser:
    """Parse explicit German Wikivoyage vCard fields, never first-price text.

    Travel-guide prices lack travel dates, rooms, availability and fee scope.
    They deliberately remain outside the budget calculation.
    """
    TYPE_MAP = {'hotel':'Hotel','apartment':'Ferienwohnung','holiday_flat':'Ferienwohnung',
                'holiday_home':'Ferienwohnung','campsite':'Camping','camping':'Camping','camp_site':'Camping'}
    def parse(self, html, destination, stamp):
        soup = BeautifulSoup(html,'html.parser')
        lodging, activities, seen = [],[],set()
        for card in soup.select('.vcard[data-name]'):
            name = card.get('data-name','').strip()
            group, kind = card.get('data-group',''),card.get('data-type','')
            identity = card.get('data-wikidata')
            marker = card.select_one('[data-lat][data-lon]')
            lat,lon,distance = None,None,None
            if marker:
                try:
                    lat,lon = float(marker['data-lat']),float(marker['data-lon'])
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
                accommodation_type = self.TYPE_MAP.get(kind)
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
                if group=='drink': topics += ['Feiern']
                if group=='eat': topics += ['Restaurants']
                if group=='see': topics += ['Kultur']
                if group in ('nature','view'): topics += ['Natur']
                if kind in ('beach','swimming','swimming_pool','lake','bathing'): topics += ['Baden']
                if kind in ('hiking','hiking_trail','mountain','peak','viewpoint','waterfall','national_park'):
                    topics += ['Wandern','Natur']
                if kind == 'park': topics += ['Natur']
                if kind in ('mountain','peak'): topics += ['Berge']
                if kind in ('nightclub','bar','pub','disco'): topics += ['Feiern']
                # No undated events: these require a separately dated event provider.
                if kind in ('event','festival'):
                    continue
                price_element = card.select_one('.voy-listing-price')
                stated_price = price_element.get_text(' ',strip=True) if price_element else ''
                stated_price = re.sub(r'^Preis:\s*', '', stated_price, flags=re.I)
                free = bool(re.fullmatch(r'(?:Eintritt\s*:?\s*)?(?:frei|kostenlos|gratis)\.?', stated_price, flags=re.I))
                if free:
                    topics.append('Kostenlos')
                topics = sorted(set(topics))
                record.update(topics=topics,type=kind,
                              description=f"{name}: Reiseführer-Eintrag für {', '.join(topics) or 'Unternehmungen'}. Öffnung und Zugang bitte prüfen.",
                              price_status=('Reiseführer nennt kostenlosen Eintritt; aktuell nicht bestätigt' if free else 'Eintritt unbekannt; nicht automatisch kostenlos'),duration='Dauer unbekannt')
                activities.append(record)
        return dict(lodgings=lodging,activities=activities)
