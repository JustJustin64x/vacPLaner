from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from urllib.parse import quote


INTEREST_ORDER = ('Kultur', 'Natur', 'Ruhe', 'Wandern', 'Baden', 'Berge', 'Restaurants', 'Feiern', 'Barhopping', 'Kostenlos')


def german_number(value, digits=1):
    if value is None:
        return 'offen'
    return f'{float(value):,.{digits}f}'.replace(',', 'X').replace('.', ',').replace('X', '.')


def euros(value):
    return german_number(Decimal(str(value)), 2) + ' €'


def german_date(value):
    try:
        return date.fromisoformat(value).strftime('%d.%m.%Y')
    except (TypeError, ValueError):
        return str(value or 'offen')


def duration(hours):
    if hours is None:
        return 'offen'
    minutes = max(0, round(float(hours) * 60))
    return f'{minutes // 60} Std. {minutes % 60:02d} Min.'


def map_url(latitude, longitude):
    if latitude is None or longitude is None:
        return ''
    return f'https://www.openstreetmap.org/?mlat={latitude}&mlon={longitude}#map=16/{latitude}/{longitude}'


@dataclass(frozen=True)
class Completeness:
    complete: bool
    issues: tuple[str, ...]


class PdfTripPresenter:
    """Builds a compact editorial model without changing stored snapshots."""

    @staticmethod
    def completeness(trip):
        import copy
        from ...core.planning.TravelOffers import expire_offers
        trip=expire_offers(copy.deepcopy(trip))
        issues = []
        lodgings = trip.get('lodgings') or []
        if not lodgings:
            issues.append('Keine Unterkunft vorhanden')
        else:
            selected = lodgings[min(trip.get('selected_lodging', 0), len(lodgings) - 1)]
            price = selected.get('price') or {}
            if price.get('low') is None or price.get('status')=='veraltet':
                issues.append('Unterkunftspreis ist nicht geprüft')
            occupancy = (selected.get('occupancy_status') or '').casefold()
            if not occupancy or any(word in occupancy for word in ('unbestätigt', 'unbekannt')):
                issues.append('Belegung und Verfügbarkeit sind nicht bestätigt')
        transports = trip.get('transports') or []
        if not transports:
            issues.append('Anreiseinformationen fehlen')
        else:
            selected = transports[min(trip.get('selected_transport', 0), len(transports) - 1)]
            if selected.get('hours_high') is None:
                issues.append('Reisezeit ist nicht belegt')
            if not any(c.get('low') is not None for c in selected.get('costs', [])):
                issues.append('Anreisekosten sind nicht beziffert')
        summary = trip.get('cost_summary') or {}
        if not summary.get('coverage') or summary.get('missing'):
            issues.append('Nur ein Teil der Reisekosten ist bekannt')
        from ...core.planning.TravelComparison import comparison
        if any(row['scenario']['missing'] for row in comparison(trip)):
            issues.append('Verkehrsmittelvergleich enthält offene oder veraltete Preise')
        return Completeness(not issues, tuple(dict.fromkeys(issues)))

    @classmethod
    def present(cls, trip):
        if trip.get('offer_searches'):
            import copy
            from ...core.planning.TravelOffers import expire_offers
            from ...core.planning.RankingService import RankingService
            trip=RankingService.recompute(expire_offers(copy.deepcopy(trip)))
        destination = trip.get('destination') or {}
        request = trip.get('request') or {}
        lodgings = trip.get('lodgings') or []
        transports = trip.get('transports') or []
        lodging_index = min(max(0, trip.get('selected_lodging', 0)), max(0, len(lodgings) - 1))
        transport_index = min(max(0, trip.get('selected_transport', 0)), max(0, len(transports) - 1))
        selected_lodging = lodgings[lodging_index] if lodgings else None
        selected_transport = transports[transport_index] if transports else None
        ordered_lodgings = ([selected_lodging] if selected_lodging else []) + sorted([x for i, x in enumerate(lodgings) if i != lodging_index],key=lambda x:(x.get('price',{}).get('status')!='aktuell abgerufen',x.get('price',{}).get('low') is None))
        from ...core.planning.TravelComparison import comparison
        comparisons=comparison(trip)
        completeness = cls.completeness(trip)
        activities = list(trip.get('activities') or [])[:8]
        topics = []
        for topic in INTEREST_ORDER:
            if request.get('interests', {}).get(topic, 0) and any(topic in a.get('topics', []) for a in activities):
                topics.append(topic)
        if not topics:
            topics = [x for x in INTEREST_ORDER if any(x in a.get('topics', []) for a in activities)][:4]
        points = [cls._point('Ziel', destination, 'destination')]
        for idx, item in enumerate(ordered_lodgings[:3], 1):
            points.append(cls._point(('Unterkunft' if idx == 1 else 'Alternative') + f' {idx}', item, 'lodging'))
        for idx, item in enumerate(activities, 1):
            points.append(cls._point(f'Aktivität {idx}', item, 'activity'))
        return {
            'id': str(trip.get('id') or destination.get('name') or 'reise'),
            'name': destination.get('name', 'Reiseziel'),
            'country': destination.get('country', ''),
            'period': f"{german_date(trip.get('start'))} bis {german_date(trip.get('end'))}",
            'nights': trip.get('nights'),
            'days': (trip.get('nights') + 1) if isinstance(trip.get('nights'), int) else None,
            'adults': request.get('adults'), 'rooms': request.get('rooms'),
            'origin': request.get('origin', 'offen'),
            'interests': topics,
            'interest_explanations':[topic+': '+proof['explanation'] for topic,proof in trip.get('interest_evidence',{}).items()],
            'lodging': cls._lodging(selected_lodging, request) if selected_lodging else None,
            'lodgings': [cls._lodging(x, request) for x in ordered_lodgings[:3]],
            'transport': cls._transport(selected_transport, request) if selected_transport else None,
            'transports': [cls._transport(x['option'], request) for x in comparisons],
            'comparisons': [cls._comparison(x,request) for x in comparisons],
            'activities': [cls._activity(x, destination) for x in activities],
            'cost': cls._cost(trip, request),
            'complete': completeness.complete,
            'issues': list(completeness.issues),
            'researched_at': cls._stamp(trip.get('researched_at')),
            'hero_image': cls._image(destination.get('image')),
            'map_points': [x for x in points if x],
            'sources': cls._sources(trip, ordered_lodgings[:3], activities),
            'offer_statuses': [{'category':{'lodging':'Unterkunft','rail':'Bahn','flight':'Flug','activities':'Aktivitäten'}.get(k,k),
                               'status':v['status'],'message':v.get('message',''),'provider':v['provider']}
                              for k,v in trip.get('offer_searches',{}).items()],
        }

    @staticmethod
    def _stamp(value):
        try:
            from zoneinfo import ZoneInfo
            return datetime.fromisoformat(value).astimezone(ZoneInfo('Europe/Berlin')).strftime('%d.%m.%Y %H:%M')
        except (TypeError, ValueError):
            return 'nicht dokumentiert'

    @staticmethod
    def _point(label, item, kind):
        if item.get('latitude') is None or item.get('longitude') is None:
            return None
        return {'label': label, 'name': item.get('name', label), 'kind': kind,
                'latitude': item['latitude'], 'longitude': item['longitude'],
                'url': map_url(item['latitude'], item['longitude'])}

    @classmethod
    def _lodging(cls, item, request):
        price = item.get('price') or {}
        return {'name': item.get('name', 'Unterkunft'), 'type': item.get('type', 'Unterkunft'),
                'address': item.get('address', 'Genaue Lage offen'),
                'distance': (german_number(item.get('distance_km')) + ' km Luftlinie zum Basisort') if item.get('distance_km') is not None else '',
                'occupancy': f"{request.get('adults', '?')} Erwachsene · {request.get('rooms', '?')} Zimmer · "+('Belegung zum Abrufzeitpunkt bestätigt' if item.get('offer_id') and price.get('status')=='aktuell abgerufen' else 'Verfügbarkeit bitte prüfen'),
                'price': cls._range(price), 'price_status': price.get('status', 'unbekannt'),
                'url': item.get('url') or item.get('source', ''), 'map_url': map_url(item.get('latitude'), item.get('longitude')),
                'image': cls._image(item.get('image')), 'open': list(item.get('open_criteria') or []),
                'amenities': [key for key, value in (item.get('amenities') or {}).items() if value is True],
                'retrieved_at':cls._stamp(item.get('retrieved_at')),
                'included':(item.get('offer') or {}).get('included',[])}

    @classmethod
    def _transport(cls, item, request):
        costs = item.get('costs') or []
        offer=item.get('offer') or {};details=offer.get('details') or {}
        notes=list(item.get('notes') or [])
        if details.get('comparison_role'):notes.insert(0,details['comparison_role']+'; kein vollständiger Marktvergleich.')
        if details.get('independent_tickets'):notes.append('Getrennte Hin- und Rückfahrkarten; keine garantierten Anschlüsse bei eigenständigen Umstiegen.')
        for index,leg in enumerate(item.get('connections',[])):
            terms=(leg.get('conditions') or {}).get('descriptions') or {}
            notes.append(('Hinfahrt' if index==0 else 'Rückfahrt')+' · Tarif: '+leg.get('seat_class','unbekannt')+' · Stornierung: '+str(terms.get('cancel') or 'nicht bekannt')+' · Umbuchung: '+str(terms.get('rebook') or 'nicht bekannt'))
        known = [x for x in costs if x.get('low') is not None]
        open_costs = [x.get('label', 'Kostenposition') for x in costs if x.get('low') is None]
        return {'mode': item.get('mode', 'Anreise'), 'time': duration(item.get('hours_high')),
                'scope': item.get('scope', ''), 'status': item.get('status', ''),
                'known_costs': [{'label': x.get('label', 'Kosten'), 'value': cls._range(x)+(' (gespeicherter Preis, veraltet)' if x.get('status')=='veraltet' else '')} for x in known],
                'open_costs': open_costs, 'notes': notes,
                'car_details': (f"{request.get('cars',1)} Fahrzeuge · Verbrauch {request.get('consumption','offen')} l/100 km · Spritpreisannahme {request.get('petrol','offen')} EUR/l · Hin- und Rückweg {german_number(item.get('kilometers'))} km" if item.get('mode')=='Auto' else ''),
                'route_legs':[{'distance':german_number(x.get('distance',0)/1000)+' km','time':duration(x.get('duration',0)/3600)} for x in item.get('route_legs',[])],
                'links': cls._dedupe_links(item.get('links') or []),
                'connections':[{**leg,'time':duration(leg.get('duration_hours'))} for leg in item.get('connections',[])],
                'retrieved_at':cls._stamp(item.get('retrieved_at'))}

    @classmethod
    def _comparison(cls,row,request):
        option=row['option'];cost=row['transport_cost'];scenario=row['scenario'];adults=request.get('adults') or 1
        def value(summary,person=False):
            if not summary['coverage']:return 'offen'
            factor=Decimal(adults if person else 1)
            return cls._range({'low':Decimal(summary['low'])/factor,'high':Decimal(summary['high'])/factor})+(' (Teilsumme)' if summary['missing'] else ' ('+summary['status']+')')
        return {'mode':option['mode'],'time':duration(option.get('hours_high')),
                'time_note': 'Fahrzeit mit geschätzten Pausen und Ortszugang; Unterkunftszufahrt offen' if option['mode']=='Auto' else 'Verbindungszeit; Zubringer-/Transferzeiten offen. Keine vollständige Tür-zu-Tür-Zeit.',
                'group':value(cost),'person':value(cost,True),'missing':cost['missing'],
                'status':cls._compact_status(option.get('status','Nicht geprüft')),'stamp':cls._stamp(option.get('retrieved_at')),
                'included':(option.get('offer') or {}).get('included',[]),
                'scenario_group':value(scenario),'scenario_person':value(scenario,True),'scenario_missing':scenario['missing'],
                'budget':('Nicht abschließend vergleichbar' if scenario['budget_ok'] is None else 'Im Hauptbudget' if scenario['budget_ok'] else 'Über Hauptbudget')}

    @staticmethod
    def _compact_status(status):
        if status.startswith('Zugang fehlt: Flugpreisabruf'):
            return 'Flugabruf offen: Anbieterzugriff blockiert (HTTP 403) bzw. automatisches Auslesen eingeschränkt. Manuelle Prüfung möglich.'
        return status if len(status)<=190 else status[:170].rsplit(' ',1)[0]+'; Details unten.'

    @classmethod
    def _cost(cls, trip, request):
        summary = trip.get('cost_summary') or {}
        missing = list(summary.get('missing') or [])
        if not summary.get('coverage'):
            title, group = 'Gesamtkosten noch offen', 'Noch kein belastbarer Gruppenbetrag'
            per_person = 'offen'
        else:
            title = 'Bekannte Kosten' if missing else ('Geschätzte Reisekosten' if summary.get('status') == 'Schätzspanne' else 'Reisekosten')
            low, high = summary.get('low'), summary.get('high')
            group = cls._range({'low': low, 'high': high})
            adults = request.get('adults') or 0
            per_person = cls._range({'low': Decimal(str(low)) / adults if low is not None and adults else None,
                                     'high': Decimal(str(high)) / adults if high is not None and adults else None})
        known = []
        for item in trip.get('costs') or []:
            if item.get('low') is not None and not item.get('optional'):
                known.append({'label': item.get('label', 'Kosten'), 'value': cls._range(item)})
        return {'title': title, 'group': group, 'per_person': per_person,
                'known': known, 'missing': missing, 'optional': 'Verpflegung und Aktivitäten sind optionale Ausgaben vor Ort.'}

    @staticmethod
    def _range(item):
        low, high = item.get('low'), item.get('high')
        if low is None:
            return 'offen'
        if high is not None and Decimal(str(high)) != Decimal(str(low)):
            return f'{euros(low)} bis {euros(high)}'
        return euros(low)

    @classmethod
    def _activity(cls, item, destination):
        topics = [x for x in INTEREST_ORDER if x in item.get('topics', [])]
        description = (item.get('description') or '').strip()
        generic = 'Reiseführer-Eintrag für' in description
        if generic:
            description = 'Konkreter Reiseführer-Eintrag; Öffnung, Zugang und mögliche Kosten vor dem Besuch prüfen.'
        offer=item.get('activity_price')
        if offer:
            from ...core.planning.ActivityPrices import activity_price_text
            price=activity_price_text(offer)
        else:price=item.get('price_status') or 'Preis nicht ermittelt; nicht als kostenlos bestätigt'
        return {'name': item.get('name', 'Aktivität'), 'topics': topics or ['Unternehmung'],
                'description': description, 'distance': (german_number(item.get('distance_km')) + ' km Luftlinie zum Basisort') if item.get('distance_km') is not None else '',
                'duration': item.get('duration', ''), 'price': price,
                'url': item.get('url') or item.get('source', ''), 'map_url': map_url(item.get('latitude'), item.get('longitude')),
                'image': cls._image(item.get('image'))}

    @staticmethod
    def _image(image):
        if not isinstance(image, dict) or not image.get('cache_path'):
            return None
        return {key: image.get(key, '') for key in ('cache_path', 'source_page', 'author', 'license', 'retrieved_at', 'title')}

    @classmethod
    def _sources(cls, trip, lodgings, activities):
        result = []
        destination = trip.get('destination') or {}
        for label, url in [('Reiseziel', destination.get('source', ''))]:
            if url: result.append({'label': label, 'url': url})
        result += [dict(x) for x in destination.get('attributions',[]) if x.get('url')]
        if destination.get('feature_profile'):
            result += [{'label':'© OpenStreetMap-Mitwirkende · ODbL','url':'https://www.openstreetmap.org/copyright'},
                       {'label':'Wikidata · CC0','url':'https://www.wikidata.org/wiki/Wikidata:Licensing'}]
        image = destination.get('image') or {}
        if image.get('source_page'):
            result.append({'label': 'Zielbild: ' + destination.get('name', ''), 'url': image['source_page'],
                           'credit': ' · '.join(x for x in (image.get('author'), image.get('license')) if x)})
        for item in list(lodgings) + list(activities):
            url = item.get('source') or item.get('url')
            if url: result.append({'label': item.get('name', 'Quelle'), 'url': url})
            image = item.get('image') or {}
            if image.get('source_page'):
                result.append({'label': 'Bild: ' + item.get('name', ''), 'url': image['source_page'],
                               'credit': ' · '.join(x for x in (image.get('author'), image.get('license')) if x)})
        for research in trip.get('offer_searches',{}).values():
            for offer in research.get('offers',[]):
                result.append({'label':offer.get('details',{}).get('property',{}).get('name') or offer['provider']+' · Preisstand '+cls._stamp(offer.get('retrieved_at')),'url':offer['source']})
        wiki_pages={item['url'].split('#',1)[0] for item in result if item.get('url','').startswith('https://de.wikivoyage.org/wiki/')}
        for page in sorted(wiki_pages):result.append({'label':'Wikivoyage: Autoren und Versionsgeschichte','url':page+'?action=history'})
        if wiki_pages:result.append({'label':'Wikivoyage: Lizenzhinweise','url':'https://de.wikivoyage.org/wiki/Wikivoyage:Lizenzbestimmungen'})
        return cls._dedupe_links(result)

    @staticmethod
    def _dedupe_links(links):
        result, seen = [], set()
        for item in links:
            url = item.get('url', '')
            if not url or url in seen or not url.startswith(('http://', 'https://')):
                continue
            seen.add(url); result.append(dict(item))
        return result
