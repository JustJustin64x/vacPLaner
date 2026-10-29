from __future__ import annotations
from datetime import date, datetime, timezone
from urllib.parse import urlencode
from uuid import uuid4
from .CostService import CostService
from .RankingService import RankingService
from .TravelProvider import TravelProvider
from .SearchDiagnostics import SearchDiagnostics
from .PlaceResearch import PlaceResearch, distance


class DiscoveryService:
    def __init__(self,catalog,provider: TravelProvider):
        self.catalog,self.provider=catalog,provider

    def search(self,request,context,emit):
        self.diagnostics=SearchDiagnostics(request)
        context.diagnostics=self.diagnostics.data
        reason='Kandidatenliste ausgeschöpft.'
        try:
            result=self._search(request,context,emit)
            reason=self.diagnostics.data.get('stop_reason') or reason
            return result
        except InterruptedError as exc:
            reason=str(exc)
            raise
        except Exception as exc:
            reason=str(exc) if isinstance(exc,ValueError) else 'Technischer Suchfehler; Details im Diagnosebericht.'
            self.diagnostics.error('Suche',exc,request.address)
            raise
        finally:
            report=self.diagnostics.finish(context,reason)
            emit('diagnostic',report)
            emit('phase',report['summary'])

    def _search(self,request,context,emit):
        context.check()
        request.validate()
        counts=self.diagnostics.data['counts']
        counts['catalog']=len(self.catalog.destinations)
        self.diagnostics.data['coverage']=self.catalog.coverage()
        coverage=self.catalog.coverage_status(request)
        if coverage:
            self.diagnostics.data['not_imported_countries']=coverage['not_imported']
            emit('phase',f"{coverage['imported_count']} Länder mit importiertem Grundbestand; {len(coverage['not_imported'])} weitere Länder noch nicht importiert. Außerhalb nur begrenzte Reiseführerziele.")
            for warning in coverage['warnings']:emit('warning',warning)
        candidates=self.catalog.candidates(request)
        counts['geographic']=sum(self.catalog.allowed(d,request) for d in self.catalog.destinations)
        emit('phase','Startort auflösen')
        origin=self.provider.origin(request.origin,request.address,context)
        if callable(getattr(self.provider,'enrich_candidates',None)):
            candidates=self.provider.enrich_candidates(candidates,request,origin,context,emit)
            self.diagnostics.data['coverage']=self.catalog.coverage()
            counts['catalog']=len(self.catalog.destinations)
        from .CandidateSelection import select_candidates
        chosen,selection=select_candidates(candidates,request,origin,context)
        counts['locally_scored']=selection['geographic_considered'];counts.update(selection)
        emit('phase',f"{counts['locally_scored']} Orte geografisch berücksichtigt; {selection['with_interest_evidence']} mit erfassten Interessenmerkmalen; {selection['features_unknown']} mit fehlenden regionalen Zusatzdaten.")
        emit('phase',f"{len(chosen)} Ziele lokal bewertet; adaptive Recherche bis {request.shortlist} Filtertreffer oder Quellen-/Zeitlimit.")
        results=[]
        price_context=None
        price_targets=0
        for destination in chosen:
            if sum(t['filter_status']=='passend' for t in results)>=request.shortlist:
                self.diagnostics.data['stop_reason']='Gewünschte Ergebnisanzahl erreicht.';break
            context.check()
            counts['examined']+=1
            emit('phase',f"{counts['examined']} Ziele näher geprüft: {destination['name']}")
            before_calls=context.calls
            try:
                trip=self.research(request,context,origin,destination,emit)
            except InterruptedError:
                self.diagnostics.outcome(destination,'unterbrochen',['Kontrollabbruch während Recherche'])
                raise
            except Exception as exc:
                self.diagnostics.error(destination['name'],exc,request.address)
                self.diagnostics.outcome(destination,'Fehler',['Quelle fehlgeschlagen' if isinstance(exc,(OSError,ValueError)) else 'Programmfehler'])
                emit('warning',destination['name']+': Recherche fehlgeschlagen; weitere Ziele werden geprüft. Diagnose enthält Details.')
                continue
            finally:
                if context.calls>before_calls:counts['online_examined']+=1
            if trip is None:continue
            if trip['filter_status']=='offen' and not request.show_ideas:continue
            if any(distance(trip['destination'],old['destination'])<12 and trip['destination']['code']==old['destination']['code'] for old in results):
                self.diagnostics.data.setdefault('grouped_alternatives',[]).append({'name':trip['destination']['name'],'reason':'Nahe Alternative derselben Urlaubsregion'});continue
            results.append(trip)
            counts['returned_results']=len(results)
            emit('result',trip)
        results.sort(key=lambda t:(t['filter_status']=='passend',t['score']),reverse=True)
        for index,trip in enumerate(results[:request.price_targets]):
            if callable(getattr(self.provider,'research_offers',None)):
                from .SearchContext import SearchContext
                import time
                if price_context is None:
                    price_context=SearchContext(cancel=context.cancel,seconds=max(.1,context.deadline-time.monotonic()),budget=32)
                    context.price_context=price_context
                if price_context.calls<price_context.budget and time.monotonic()<price_context.deadline:
                    trip=self.provider.research_offers(trip,price_context,emit)
                    results[index]=trip
                    price_targets+=1
                    self.diagnostics.data['price_research']={'targets':price_targets,'calls':price_context.calls,'budget':price_context.budget,
                        'statuses':{k:v['status'] for k,v in trip.get('offer_searches',{}).items()}}
                    emit('result',trip)
        return sorted(results,key=lambda t:(t['filter_status']=='passend',t['score']),reverse=True)

    def research(self,request,context,origin,destination,emit):
        counts=self.diagnostics.data['counts']
        places=PlaceResearch(self.catalog,self.provider).collect(destination,request,context,emit)
        for warning in places['warnings']:emit('warning',warning)
        lodgings=[];unverified=[];reasons=[];violations=[]
        for item in places['lodgings']:
            if item['type'] not in request.accommodation_types:continue
            amenities=item.get('amenities',{})
            if any(amenities.get(k) is False for k in request.required):
                violations.append('Pflichtausstattung nachweislich verletzt');continue
            if request.max_center_km and item.get('distance_km') is not None and item['distance_km']>float(request.max_center_km):
                violations.append('Zentrumsentfernung überschritten');continue
            unknown=list(item.get('open_geo_criteria',[]))
            if any(amenities.get(k) is not True for k in request.required):unknown.append('Pflichtausstattung unbelegt: '+', '.join(k for k in request.required if amenities.get(k) is not True))
            if request.max_center_km and item.get('distance_km') is None:unknown.append('Zentrumsentfernung unbekannt')
            item['open_criteria']=unknown
            (unverified if unknown else lodgings).append(item)
        if lodgings:counts['with_lodgings']+=1
        if not lodgings:
            if unverified:
                lodgings=unverified
                reasons+=list(dict.fromkeys(r for l in unverified for r in l['open_criteria']))
            elif violations:
                self.diagnostics.outcome(destination,'ausgeschlossen',violations);return None
            else:reasons.append('Quelle fehlgeschlagen' if places['warnings'] and not places['lodgings'] else 'Unterkunftsdaten fehlen')
        if len(lodgings)<2:reasons.append('Weniger als zwei Unterkunftsidentitäten')
        # Do not spend routing calls when mandatory lodging criteria are unresolved.
        transport_request=request
        if reasons and (request.required or not lodgings):
            from dataclasses import replace
            transport_request=replace(request,modes=[m for m in request.modes if m!='Auto'] or ['Auto'])
            if transport_request.modes==['Auto']:
                transports=[dict(mode='Auto',costs=[dict(label='Auto Hin-/Rückfahrt',low=None,status='unbekannt')],
                    hours_high=None,hours_low=None,comfort=0,scope='Gesamte Gruppe',notes=['Route wegen fehlender oder unbelegter Unterkunftsdaten nicht abgefragt.'],links=[],status='Nicht geprüft',filter_status='unbekannt')]
            else:transports=self.transports(transport_request,context,origin,destination,*request.dates()[0],emit)
        else:transports=self.transports(request,context,origin,destination,*request.dates()[0],emit)
        if not transports:
            self.diagnostics.outcome(destination,'ausgeschlossen',['Reisezeit überschritten']);return None
        valid=[t for t in transports if t.get('filter_status')!='unbekannt']
        if request.max_hours and not valid:reasons.append('Reisezeit unbekannt')
        if valid:transports=valid
        if any(t.get('hours_high') is not None for t in transports):counts['with_known_transport']+=1
        active=any(request.interests.values())
        activities=[a for a in places['activities'] if not active or any(request.interests.get(t,0)>0 for t in a['topics'])]
        def activity_priority(a):
            nature=max((request.interests.get(t,0) for t in a['topics'] if t in ('Natur','Ruhe','Berge')),default=0)
            independent=sum(request.interests.get(t,0) for t in a['topics'] if t not in ('Natur','Ruhe','Berge'))
            return (-(nature+independent),a.get('distance_km') if a.get('distance_km') is not None else float('inf'),a.get('id',''))
        activities.sort(key=activity_priority)
        if activities:counts['with_activities']+=1
        lodgings.sort(key=lambda x:(-sum(x.get('amenities',{}).get(k) is True for k in request.desired),x.get('distance_km') if x.get('distance_km') is not None else 9999))
        lodgings=lodgings[:8]
        start,end=request.dates()[0] # Stable, independent of ranking; no date-price provider.
        for item in lodgings:
            item['requested_occupancy']=request.room_occupancy()
            item['occupancy_status']=f'Anfrage: {request.adults} Erwachsene / {request.rooms} Zimmer, Aufteilung {request.room_occupancy()}; Belegung und freie Zimmer unbestätigt'
            if item['type']=='Camping':item['occupancy_status']+='; Stellplätze und eigene Ausrüstung gesondert prüfen'
            item['search_url']='https://www.booking.com/searchresults.de.html?'+urlencode(dict(ss=item['name']+' '+item.get('source_place',destination['name']),checkin=start,checkout=end,group_adults=request.adults,no_rooms=request.rooms,group_children=0,selected_currency='EUR'))
            item['price']=dict(item['price'],scope=f'{request.adults} Erwachsene / {request.rooms} Zimmer / {(date.fromisoformat(end)-date.fromisoformat(start)).days} Nächte; Gesamtpreis unbekannt')
        evidence=RankingService.interest_evidence(destination,activities,request)
        status='offen' if reasons else 'passend'
        counts['ideas' if reasons else 'matches']+=1
        self.diagnostics.outcome(destination,status,reasons)
        trip=dict(id=str(uuid4()),destination=destination,origin=origin,request=request.to_dict(),start=start,end=end,
            date_options=request.dates(),nights=(date.fromisoformat(end)-date.fromisoformat(start)).days,
            lodgings=lodgings,activities=activities[:12],transports=transports,selected_lodging=0,selected_transport=0,
            interest_match=RankingService.interest_match(destination,request,activities),interest_evidence=evidence,
            evidence_confidence=sum(v['confidence'] for v in evidence.values())/len(evidence) if evidence else 0,
            filter_status=status,open_criteria=reasons,search_id=self.diagnostics.data['search_id'],
            researched_at=datetime.now(timezone.utc).isoformat(timespec='seconds'),
            notes=[places['cache_note'],destination.get('coordinate_note','Routing ab Basisortkoordinate; Unterkunftszufahrt nicht belegt'),'Adaptive begrenzte Suche; kein vollständiger Marktvergleich. Natur-/Badeinteressen bevorzugen in der Vorauswahl passende kleinere Landschaftsziele; keine Aktivitätszusage.',
                   'Termine sind plausible Stichproben, keine Optimierung datierter Preise.',
                   'Reiseführer-Einträge belegen Identität, keine Verfügbarkeit oder Zimmerbelegung.',
                   'Lageabstände sind Luftlinie, keine belegte Erreichbarkeit. Hotelzufahrt fehlt.',
                   'Optionale Verpflegung und Aktivitäten liegen außerhalb des Budgets.',
                   'Zug-/Flugfahrpläne und Preise sowie datierte Veranstaltungen sind nicht angebunden.'],
            explanation='; '.join(k+': '+v['explanation'] for k,v in evidence.items()) or 'Offene Suche ohne Interessenfilter.',
            research_status='Passende Reiseidee – Angaben noch offen: '+'; '.join(reasons) if reasons else 'Filtertreffer: zwei Unterkunftsidentitäten; Preise, Verfügbarkeit und Belegung weiterhin unbestätigt')
        scores=[]
        for i in range(len(transports)):
            trip['selected_transport']=i;RankingService.recompute(trip);scores.append(trip['score'])
        trip['selected_transport']=max(range(len(scores)),key=scores.__getitem__)
        RankingService.recompute(trip)
        return trip

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
                except InterruptedError:
                    raise
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
            if request.max_hours:
                if option['hours_high'] is None:
                    option['filter_status']='unbekannt'
                    option['notes'].append('Reisezeit unbekannt: erfüllt das gesetzte Limit NICHT nachweislich.')
                elif option['hours_high'] > float(request.max_hours):
                    continue
            result.append(option)
        return result
