from decimal import Decimal
from .CostService import CostService


class RankingService:
    @staticmethod
    def interest_match(destination, request):
        total = sum(request.interests.values())
        return sum(v for k,v in request.interests.items() if k in destination['interests'])/total if total else 0.5

    @staticmethod
    def recompute(trip):
        request = trip['request']
        selected = trip['transports'][trip['selected_transport']]
        lodging = trip['lodgings'][trip['selected_lodging']] if trip['lodgings'] else None
        costs = list(selected['costs'])+[lodging['price'] if lodging else dict(
            label='Unterkunft für Gruppe und Aufenthalt', low=None, status='unbekannt')]
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
