from __future__ import annotations
from datetime import date, datetime, timezone
from decimal import Decimal
from urllib.parse import urlencode
from uuid import uuid4
from .CostService import CostService
from .RankingService import RankingService
from .TravelProvider import TravelProvider
from ..domain.value_objects.GeographicCoordinates import GeographicCoordinates


class DiscoveryService:
    def __init__(self, catalog, provider: TravelProvider):
        self.catalog,self.provider = catalog,provider

    def search(self, request, context, emit):
        request.validate()
        emit('phase','Startort auflösen')
        origin = self.provider.origin(request.origin,request.address,context)
        candidates = self.catalog.candidates(request)
        origin_coords = GeographicCoordinates(origin['latitude'],origin['longitude'])
        def priority(d):
            distance = origin_coords.calculate_distance_in_kilometers_to(GeographicCoordinates(d['latitude'],d['longitude']))
            weights = request.normalized_weights()
            interest_weight = float(weights['Interessen'])
            time_weight = float(weights['Reisezeit'])
            # Price and comfort cannot be inferred from a city name. Use only the
            # two available signals, with distance explicitly a shortlist proxy.
            total = interest_weight+time_weight
            if not total:
                interest_weight=time_weight=.5
                total=1
            return (RankingService.interest_match(d,request)*interest_weight + max(0,1-distance/2000)*time_weight)/total
        candidates.sort(key=priority,reverse=True)
        # Geographic diversity before expensive retrieval: at most two per country first.
        ordered, deferred, counts = [],[],{}
        for d in candidates:
            if counts.get(d['country'],0) >= 2:
                deferred.append(d)
            else:
                ordered.append(d)
                counts[d['country']] = counts.get(d['country'],0)+1
        chosen = (ordered+deferred)[:request.shortlist+3]  # bounded reserves for missing lodging alternatives
        emit('phase',f'Bis zu {len(chosen)} von {len(candidates)} passenden Katalogzielen einschließlich Reserven; kein globales Preisoptimum.')
        results = []
        for index,destination in enumerate(chosen):
            if sum(len(t['lodgings']) >= 2 for t in results) >= request.shortlist:
                break
            context.check()
            emit('phase',f'Ziel {index+1}/{len(chosen)}: {destination["name"]} – Unterkünfte und Aktivitäten')
            places = self.provider.places(destination,context)
            context.check()
            for warning in places.get('warnings',[]):
                emit('warning',warning)
            lodgings=[]
            for raw in places['lodgings']:
                item = dict(raw)
                if item.get('latitude') is not None and item.get('longitude') is not None:
                    item['distance_km'] = GeographicCoordinates(item['latitude'],item['longitude']).calculate_distance_in_kilometers_to(GeographicCoordinates(destination['latitude'],destination['longitude']))
                if item['type'] not in request.accommodation_types:
                    continue
                if any(item.get('amenities',{}).get(k) is not True for k in request.required):
                    continue
                if request.max_center_km and (item['distance_km'] is None or item['distance_km'] > float(request.max_center_km)):
                    continue
                item['requested_occupancy'] = request.room_occupancy()
                item['occupancy_status'] = f'Anfrage: {request.adults} Erwachsene / {request.rooms} Zimmer, Aufteilung {request.room_occupancy()}; Belegung und freie Zimmer unbestätigt'
                if item['type']=='Camping':
                    item['occupancy_status'] += '; Stellplätze, eigene Ausrüstung und Belegung gesondert prüfen; Zimmer nicht in Stellplätze umgerechnet'
                lodgings.append(item)
            lodgings.sort(key=lambda x:(-sum(x.get('amenities',{}).get(k) is True for k in request.desired),x.get('distance_km') if x.get('distance_km') is not None else 9999))
            lodgings=lodgings[:8]
            start,end=request.dates()[index % len(request.dates())]
            for item in lodgings:
                item['search_url']='https://www.booking.com/searchresults.de.html?'+urlencode(dict(
                    ss=item['name']+' '+destination['name'],checkin=start,checkout=end,
                    group_adults=request.adults,no_rooms=request.rooms,group_children=0,selected_currency='EUR'))
                item['price']=dict(item['price'],scope=f'{request.adults} Erwachsene / {request.rooms} Zimmer / {(date.fromisoformat(end)-date.fromisoformat(start)).days} Nächte; Verfügbarkeit und Gesamtpreis unbekannt')
            if len(lodgings)<2:
                emit('warning',f'{destination["name"]}: nur {len(lodgings)} passende reale Unterkunftseinträge; nächstes Ziel wird ebenfalls geprüft.')
            emit('phase',f'{destination["name"]} – Hin- und Rückreise prüfen')
            transports = self.transports(request,context,origin,destination,start,end,emit)
            if not transports:
                emit('warning',destination['name']+': keine Option erfüllt die maximale Reisezeit mit ausreichenden Daten.')
                continue
            if not lodgings and (request.required or request.max_center_km):
                emit('warning',destination['name']+': Pflichtfilter nicht belegt; Ziel ausgeschlossen.')
                continue
            activities = [a for a in places['activities'] if any(request.interests.get(t,0)>0 for t in a['topics'])]
            activities.sort(key=lambda a:sum(request.interests.get(t,0) for t in a['topics']),reverse=True)
            notes = [places['cache_note'],
                     f'Begrenzte Suche: maximal {len(chosen)}/{len(candidates)} Katalogziele, {len(request.dates())} Datumsstichproben; keine Prüfung aller Termine.',
                     'Reiseführer-Einträge belegen Identität, keine Verfügbarkeit oder Belegung. Preise müssen beim Anbieter geprüft werden.',
                     'Optional: Verpflegung und Aktivitäten sind nicht im Budgetvergleich enthalten. Ohne belastbare Daten keine pauschalen Zusatzkosten.',
                     'Zug-/Flugpreise und Fahrpläne sowie datierte Veranstaltungen sind derzeit nicht angebunden.',
                     'Entfernungen von Unterkünften zum Zentrum sind Luftlinie. Unterkunftsanbindung und genaue Startadresse fehlen im Routing.']
            if len(lodgings)<2:
                notes.append('Unvollständig recherchiert: weniger als zwei Unterkunftsalternativen gefunden.')
            topics = [k for k in destination['interests'] if request.interests.get(k,0)>0]
            trip=dict(id=str(uuid4()),destination=destination,origin=origin,request=request.to_dict(),
                      start=start,end=end,nights=(date.fromisoformat(end)-date.fromisoformat(start)).days,
                      lodgings=lodgings,activities=activities[:12],transports=transports,
                      selected_lodging=0,selected_transport=0,interest_match=RankingService.interest_match(destination,request),
                      researched_at=datetime.now(timezone.utc).isoformat(timespec='seconds'),notes=notes,
                      explanation=f"{destination['name']} passt redaktionell zu {', '.join(topics) or 'einer offenen Zielsuche'}. "
                      f"{start} bis {end} liegt vollständig im gewünschten Zeitraum; keine Behauptung eines günstigsten Termins. "
                      'Die Unterkunftsauswahl berücksichtigt Typ, belegbare Pflichtmerkmale und Lage; unbekannte Wünsche bleiben offen.',
                      research_status='Identitäten recherchiert; Angebote und Belegung unbestätigt' if len(lodgings)>=2 else 'Teilergebnis')
            # Choose a recommendation using the same weights as later swaps.
            variants=[]
            for t in range(len(transports)):
                trip['selected_transport']=t
                RankingService.recompute(trip)
                variants.append(trip['score'])
            trip['selected_transport']=max(range(len(variants)),key=variants.__getitem__)
            RankingService.recompute(trip)
            context.check()
            results.append(trip)
            emit('result',trip)
        emit('phase',f'Abgeschlossen: {len(results)} Ziele, {context.calls} echte Abfragen. Datenlücken in den Ergebnissen beachten.')
        return sorted(results,key=lambda t:t['score'],reverse=True)

    def transports(self, request, context, origin, destination, start, end, emit):
        result=[]
        scope=f'{request.adults} Erwachsene, Hin- und Rückreise {start} bis {end}'
        for mode in request.modes:
            option=dict(mode=mode,costs=[],hours_high=None,hours_low=None,comfort=0,scope=scope,
                        notes=[],links=[],status='Nicht vollständig vergleichbar')
            if mode=='Auto':
                try:
                    route=self.provider.route(origin,destination,context)
                    km=sum(leg['distance'] for leg in route['legs'])/1000
                    hours=[leg['duration']/3600 for leg in route['legs']]
                    low=max(hours)+int(max(hours)/2)*.25+.5
                    high=low*1.2
                    option.update(hours_low=round(low,2),hours_high=round(high,2),kilometers=round(km,1),
                                  route_legs=route['legs'],retrieved_at=route['retrieved_at'],comfort=.5,
                                  status='Echte Straßenroute; Kosten und Zeiten teilweise geschätzt')
                    option['costs'].append(CostService.fuel(km,request,route['source'],route['retrieved_at'],start,end))
                    option['notes'] += [route['precision'],
                        f'Hinweg {hours[0]:.1f} h / Rückweg {hours[1]:.1f} h reine Fahrzeit. Zeitspanne je längerer Richtung: {low:.1f}–{high:.1f} h.',
                        'Zeitannahmen: 15 Minuten Pause je 2 Stunden, 30 Minuten Ortszugang, bis 20 % Zeitreserve; kein Live-Verkehr. Hotelzufahrt unbekannt.',
                        'Komfortannahme 0,5: eigenes Auto; kein gemessener Komfortwert.',
                        'Vignetten sind unbekannt. Kein automatischer Doppelansatz für Hin-/Rückfahrt. Fähren/Autoverlad nicht bepreist.']
                    option['links'].append(dict(label='Routingquelle',url=route['source'],kind='Routendaten'))
                    # Dates assume same-day arrival. Never invent a hotel night during overnight transit.
                    if high>16:
                        emit('warning',destination['name']+': Autofahrt benötigt eventuell eine Zwischenübernachtung; aus Ein-Ziel-Vergleich ausgeschlossen.')
                        continue
                except (OSError,ValueError,KeyError) as exc:
                    emit('warning',str(exc))
                    option['costs'].append(dict(label='Benzin Hin-/Rückfahrt',low=None,status='unbekannt',scope=scope))
                    option['notes'].append('Straßenroute nicht verfügbar; keine Luftlinie als Fahrstrecke ausgegeben.')
                for label in ('Maut und Vignetten für alle Fahrzeuge','Parken am Ziel und an der Unterkunft','Fähren/Autoverlad falls erforderlich'):
                    option['costs'].append(dict(label=label,low=None,status='unbekannt',scope=scope))
                option['notes'].append('Eigenes Auto wird auch auf der Rückfahrt benutzt; kein Wechsel auf Rückflug.')
            else:
                option['costs']=[dict(label=mode+' für gesamte Gruppe hin und zurück',low=None,status='unbekannt',scope=scope),
                                 dict(label='Zubringer und Unterkunftstransfers hin und zurück',low=None,status='unbekannt',scope=scope)]
                option['notes']=['Keine bestätigten datierten Verbindungen, Ticketpreise, Gepäck-/Tarifbedingungen oder Transferzeiten. Nicht als buchbare Verbindung zu verstehen.']
                if mode=='Zug':
                    option['links']=[dict(label='Deutsche Bahn',url='https://www.bahn.de/buchung/start',kind='Allgemeiner Anbieterlink')]
                else:
                    query=f'Flights from {request.origin} to {destination["name"]} {start} return {end} {request.adults} adults'
                    option['links']=[dict(label='Google Flights',url='https://www.google.com/travel/flights?'+urlencode({'q':query}),kind='Parametrierter Suchlink; Eingaben dort prüfen')]
            if request.max_hours and (option['hours_high'] is None or option['hours_high'] > float(request.max_hours)):
                continue
            result.append(option)
        return result
