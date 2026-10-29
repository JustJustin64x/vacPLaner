from datetime import datetime
from zoneinfo import ZoneInfo
from decimal import Decimal


def euros(value):
    return f'{Decimal(value):,.2f}'.replace(',','X').replace('.',',').replace('X','.')+' €'


def local_stamp(value):
    if not value:
        return 'unbekannt'
    return datetime.fromisoformat(value).astimezone(ZoneInfo('Europe/Berlin')).strftime('%d.%m.%Y %H:%M %Z')


def price_text(item):
    if item.get('low') is None:
        return 'unbekannt'
    value=euros(item['low'])
    if item.get('high') and item['high'] != item['low']:
        value += ' bis '+euros(item['high'])
    return value+' ('+item['status']+')'


class TripPresenter:
    @staticmethod
    def sections(trip):
        if trip.get('offer_searches'):
            import copy
            from ...core.planning.TravelOffers import expire_offers
            from ...core.planning.RankingService import RankingService
            trip=RankingService.recompute(expire_offers(copy.deepcopy(trip)))
        request=trip['request']
        selected=trip['transports'][trip['selected_transport']]
        summary=trip['cost_summary']
        lodging=trip['lodgings'][trip['selected_lodging']] if trip['lodgings'] else None
        delta=summary['budget_delta']
        budget_note='Budgetstatus offen: unvollständige Reisebasis.' if delta is None else (
            f"Budgetabweichung {euros(delta)} (positiv = darüber); {'geschätzte Obergrenze' if summary['status']=='Schätzspanne' else 'Gesamtpreis'}.")
        sections=[('Reiseübersicht',[
            f"{trip['destination']['name']}, {trip['destination']['country']} | {trip['start']} bis {trip['end']}",
            f"{trip['nights']+1} Kalendertage / {trip['nights']} Übernachtungen | {request['adults']} Erwachsene / {request['rooms']} Zimmer",
            f"Ab {request['origin']} | Anfrage: {request['earliest']} bis {request['latest']} | Gruppenbudget {euros(request['budget'])}",
            f"Recherche: {local_stamp(trip['researched_at'])}. Gespeicherte Angaben sind ein damaliger Stand, keine neue Preisabfrage.",
            'Region: '+trip['destination'].get('regional_name',trip['destination'].get('region',''))+' | Zieltyp: '+trip['destination'].get('type','nicht erfasst')+' | Basisort: '+trip['destination'].get('base_name',trip['destination']['name']),
            'Datensicherheit Interessen: '+(f"{trip['evidence_confidence']:.0%}" if 'evidence_confidence' in trip else 'nicht separat erfasst'),
            'Terminoptionen (Stichproben): '+', '.join(a+' bis '+b for a,b in trip.get('date_options',[(trip['start'],trip['end'])])),
            ('Aktuelle Angebotsprüfung vorhanden; Preisstand und Abdeckung stehen bei den einzelnen Kategorien.' if any(v.get('status')=='found' for v in trip.get('offer_searches',{}).values()) else trip['research_status']),trip['explanation'],trip['recommendation'],
            'Normalisierte Gewichte: '+', '.join(f'{k} {v:.0%}' for k,v in trip['normalized_weights'].items()),
            'Unterkunftswünsche: '+(', '.join(request['desired']) or 'keine')+' | Pflichtmerkmale: '+(', '.join(request['required']) or 'keine'),
            'Ausgewählt: '+selected['mode']+' / '+(lodging['name'] if lodging else 'Unterkunft fehlt')],
            [('Zielquelle: Wikivoyage',trip['destination']['source'])]),
            ('Reisebasis für die gesamte Gruppe',[
                f"{summary['status']}: {euros(summary['low'])} bis {euros(summary['high'])}" if summary['coverage'] else 'Keine bezifferbare Reisebasis verfügbar.',
                budget_note]+[f"{c['label']}: {price_text(c)}" for c in trip['costs'] if not c.get('optional')]+[
                'Fehlende Positionen: '+(', '.join(summary['missing']) or 'keine'),
                'Optionale Ausgaben vor Ort: Verpflegung und Aktivitäten separat; unbekannt und außerhalb des Budgetvergleichs.'],[])]
        for c in trip['costs']:
            if c.get('low') is not None:
                sections.append((c['label'],[c.get('scope',''),c.get('method',''),
                                  'Abruf: '+local_stamp(c.get('retrieved_at',''))],
                                  [('Kostenquelle',c['source'])] if c.get('source','').startswith('http') else []))
        for i,t in enumerate(trip['transports']):
            sections.append((('Ausgewählt: ' if i==trip['selected_transport'] else 'Alternative: ')+t['mode'],
                             [t['status'],t['scope']]+t['notes']+[f"{c['label']}: {price_text(c)}" for c in t['costs']],
                             [(link['label']+' – '+link['kind'],link['url']) for link in t['links']]))
        for i,l in enumerate(trip['lodgings']):
            amenities=', '.join(k+': '+('ja' if v is True else 'nein' if v is False else 'unbekannt') for k,v in l.get('amenities',{}).items())
            distance=f"{l['distance_km']:.1f} km Luftlinie zum Zentrum" if l.get('distance_km') is not None else 'Zentrumsentfernung unbekannt'
            sections.append((('Ausgewählte Unterkunft: ' if i==trip['selected_lodging'] else 'Unterkunftsalternative: ')+l['name'],
                             [f"{l['type']} | {l['address']} | {distance}",l['occupancy_status'], 'Quellort: '+l.get('source_place',trip['destination']['name'])+' | '+l.get('distance_kind','Luftlinie'),
                              'Offene Pflichtangaben: '+('; '.join(l.get('open_criteria',[])) or 'keine zusätzlich erfasst'),
                              l['booking_status'],l['price']['scope'],
                              'Gruppen-/Aufenthaltspreis: '+price_text(l['price']),
                              'Ausstattung: '+(amenities or 'unbekannt')+'. Storno- und Verpflegungsbedingungen unbekannt.',
                              l['data_status']+' | Abruf: '+local_stamp(l['retrieved_at']), l.get('source_updated','Letzte Quellenpflege unbekannt')],
                             [(l['link_kind'],l['url']),('Datierter Suchlink – kein geprüftes Angebot',l['search_url']),('Quelleneintrag',l['source'])]))
        sections.append(('Aktivitäten und optionale Ausgaben',[
            'Eintritt und Dauer sind nur genannt, soweit belegt. Keine automatisch bestätigten kostenlosen Unternehmungen.'
            if trip['activities'] else 'Keine zum Interessenfilter passenden Aktivitäten aus der Quelle verfügbar.'],[]))
        for a in trip['activities']:
            location=f"{a['latitude']}, {a['longitude']}" if a['latitude'] is not None else 'Lage unbekannt'
            sections.append((a['name'],[a['description'],f"Lage: {location}; {a['price_status']}; {a['duration']}",
                                       'Quellort: '+a.get('source_place',trip['destination']['name'])+' | '+(f"{a['distance_km']:.1f} km Luftlinie; Erreichbarkeit offen" if a.get('distance_km') is not None else 'Abstand unbekannt'),
                                       'Quelle abgerufen: '+local_stamp(a['retrieved_at'])],[(a['link_kind'],a['url']),('Quelleneintrag',a['source'])]))
        if trip.get('offer_searches'):
            from ...core.planning.TravelOffers import STATUS_LABELS
            for category,result in trip['offer_searches'].items():
                label={'lodging':'Unterkunft','rail':'Bahn','flight':'Flug'}.get(category,category)
                paragraphs=[STATUS_LABELS.get(result['status'],result['status'])+' · '+result['provider'],
                            result.get('message',''),'Geprüft: '+local_stamp(result.get('checked_at',''))]
                links=[]
                for offer in result.get('offers',[]):
                    paragraphs.append(f"{offer['provider']}: {offer['original_amount']} {offer['original_currency']} · {offer['parameters']['adults']} Erwachsene · {offer['parameters']['start']} bis {offer['parameters']['end']} · {offer['price_status']}")
                    paragraphs += offer.get('included',[])+offer.get('unresolved',[])
                    for leg in offer.get('details',{}).get('legs',[]):
                        paragraphs.append(f"{leg['from']} → {leg['to']} · {leg['departure']} bis {leg['arrival']} · {leg['transfers']} Umstiege · {leg.get('seat_class','Economy')}")
                    detail=offer.get('details',{})
                    paragraphs += [detail[key] for key in ('board','cancellation','payment') if detail.get(key)]
                    links.append(('Geprüftes Angebot',offer['source']))
                sections.append(('Angebotsprüfung · '+label,paragraphs,links))
        if trip.get('offer_date_samples'):
            from ...core.planning.TravelOffers import STATUS_LABELS
            sections.append(('Geprüfte Terminproben',[
                sample['start']+' bis '+sample['end']+': '+'; '.join(result['provider']+' · '+STATUS_LABELS[result['status']]+(' · '+', '.join(o['original_amount']+' '+o['original_currency'] for o in result.get('offers',[])) if result.get('offers') else '') for result in sample['offer_searches'].values())
                for sample in trip['offer_date_samples']],[]))
        notes=[n for n in trip['notes'] if not (trip.get('offer_searches',{}).get('rail',{}).get('status')=='found' and 'Zug-/Flugfahrpläne' in n)]
        sections.append(('Datenlücken und Quellen',notes,[
            ('Wikivoyage: Autoren und Versionsgeschichte',trip['destination']['source']+'?action=history'),
            ('Wikivoyage: Lizenz', 'https://de.wikivoyage.org/wiki/Wikivoyage:Lizenzbestimmungen'),
            ('© OpenStreetMap-Mitwirkende (ODbL)', 'https://www.openstreetmap.org/copyright'),
            ('Kartendaten korrigieren','https://www.openstreetmap.org/fixthemap'),
            ('Routing: OSRM / FOSSGIS','https://routing.openstreetmap.de/about.html'),
            ('CHECK24 – allgemeiner Anbieterlink','https://hotel.check24.de/'),
            ('Trivago – allgemeiner Anbieterlink','https://www.trivago.de/')] ))
        return sections
