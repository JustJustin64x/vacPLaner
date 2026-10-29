from decimal import Decimal
from .CostService import CostService


class RankingService:
    @staticmethod
    def interest_match(destination, request, activities=None):
        from .DestinationFeatures import evidence_score
        observed=evidence_score(destination,request)
        if observed is not None:return observed
        total = sum(request.interests.values())
        strengths=destination.get('interest_strengths',{k:3 for k in destination['interests'] if k not in ('Kostenlos','Veranstaltungen')})
        strengths={k:float(v)*.2 for k,v in strengths.items()}  # Weak editorial hints, no measured feature evidence.
        if activities is not None:
            for topic in request.interests:
                hits={str(a.get('id') or a.get('source') or a.get('name') or sorted(a.get('topics',[]))) for a in activities if topic in a['topics']}
                if hits:
                    value=.15 if len(hits)==1 and topic in ('Wandern','Feiern','Barhopping') else min(1,len(hits)/4)
                    strengths[topic]=max(strengths.get(topic,0),5*value)
        return sum(v*strengths.get(k,0)/5 for k,v in request.interests.items())/total if total else 0.5

    @staticmethod
    def interest_evidence(destination,activities,request):
        result={}
        for topic,weight in request.interests.items():
            if not weight:continue
            profile=destination.get('feature_profile')
            if profile is not None:
                proof=profile['evidence'].get(topic,[]);n=profile['counts'].get(topic,0)
                result[topic]=dict(editorial=False,local=n,vicinity=0,confidence=min(1,len(proof)/4),
                    explanation=(f'{n} erfasste Merkmale im untersuchten Umkreis; '+('mehrere Bars/Kneipen innerhalb 2 km Luftlinie; Fußwege und Öffnung ungeprüft' if topic=='Barhopping' and n>=3 else 'einzelner Eintrag belegt keine ausgeprägte Eignung' if n==1 else 'keine aktuelle Öffnungs-/Saisonzusage')) if n else 'Merkmale unbekannt; '+('regionale Daten vorhanden, Kartierung kann unvollständig sein' if profile['coverage']=='regional' else 'Zusatzdaten für diese Region fehlen'),
                    sources=[p['source'] for p in proof],evidence=proof,coverage=profile['coverage'])
                if topic=='Ruhe' and n:result[topic]['explanation']+='; Natur-/Grünraumhinweise, keine Lärmmessung oder Ruhezusage'
                if topic=='Städte' and n:result[topic]['explanation']='Geografischer Ortstyp: '+destination.get('type','Stadt')+'; keine pauschale Aussage über touristische Qualität'
                continue
            hits=[a for a in activities if topic in a['topics']]
            local=[a for a in hits if not a.get('vicinity')]
            editorial=topic in destination['interests'] and topic not in ('Kostenlos','Veranstaltungen')
            explanation=('belegte Einträge am Ort' if local else 'belegte Einträge im Umfeld (Erreichbarkeit offen)' if hits else
                         'redaktionelle Eignung; konkrete Aktivitäten unbelegt' if editorial else 'Eignung und konkrete Angebote unbekannt')
            if topic=='Feiern' and hits:explanation+='; einzelne Angebote belegen kein ausgeprägtes Nachtleben'
            result[topic]=dict(editorial=editorial,local=len(local),vicinity=len(hits)-len(local),
                               confidence=1 if local else .7 if hits else .2 if editorial else 0,
                               explanation=explanation,sources=list(dict.fromkeys(a['source'] for a in hits)))
        return result

    @staticmethod
    def recompute(trip):
        request = trip['request']
        selected = trip['transports'][trip['selected_transport']]
        lodging = trip['lodgings'][trip['selected_lodging']] if trip['lodgings'] else None
        costs = list(selected['costs'])+[lodging['price'] if lodging else dict(
            label='Unterkunft für Gruppe und Aufenthalt', low=None, status='unbekannt')]
        if lodging:costs.extend(lodging.get('mandatory_costs',[]))
        costs.append(dict(label='Verpflegung und Aktivitäten (optional)', low=None, status='unbekannt', optional=True))
        trip['costs'] = costs
        summary = CostService.summarize(costs, request['budget'])
        trip['cost_summary'] = summary
        weights = {k: Decimal(str(request['weights'].get(k,0))) for k in ('Preis','Reisezeit','Komfort','Interessen')}
        total = sum(weights.values())
        weights = {k: float(v/total) if total else .25 for k,v in weights.items()}
        # Missing prices get zero price utility, never a cheapness bonus.
        price = max(0, 1-float(Decimal(summary['high'])/Decimal(request['budget'])) ) if not summary['missing'] else 0
        hours = selected.get('hours_high')
        time_score = max(0, 1-hours/24) if hours is not None else 0
        comfort = selected.get('comfort',0)  # only explicit, described heuristic
        quality = .25*summary['coverage'] + (.15 if hours is not None else 0)
        desired = request.get('desired',[])
        amenity_match = sum(lodging.get('amenities',{}).get(k) is True for k in desired)/len(desired) if desired and lodging else 0
        score = weights['Preis']*price+weights['Reisezeit']*time_score+weights['Komfort']*(comfort+amenity_match)/2+weights['Interessen']*trip['interest_match']
        trip['score'] = round(100*(.7*score+.3*quality),1)
        trip['normalized_weights'] = weights
        trip['recommendation'] = (f"Vorläufige Orientierung: {selected['mode']}; Interessenpassung {trip['interest_match']:.0%}. "
                                  f"Bewertung {trip['score']}/100. Unbekannte Preise und Zeiten erhalten keinen Vorteil. "
                                  'Kein belegter Preis-/Zeit-Sieger bei unvollständigen Vergleichsdaten.')
        return trip
