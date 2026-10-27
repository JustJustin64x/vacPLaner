from decimal import Decimal
from .CostItem import CostItem, money


class CostService:
    @staticmethod
    def summarize(items, budget):
        basis = [i for i in items if not i.get('optional')]
        known = [i for i in basis if i.get('low') is not None and i['status'] != 'veraltet']
        missing = [i['label'] for i in basis if i not in known]
        lo = money(sum((Decimal(i['low']) for i in known), Decimal(0)))
        hi = money(sum((Decimal(i.get('high') or i['low']) for i in known), Decimal(0)))
        estimated = any(i['status']=='geschätzt' for i in known)
        status = 'Teilsumme' if missing else ('Schätzspanne' if estimated or lo != hi else 'Gesamtpreis')
        delta = None if missing else str(money(hi-Decimal(budget)))
        return dict(low=str(lo), high=str(hi), status=status, missing=missing,
                    budget_delta=delta, budget_ok=None if missing else hi <= Decimal(budget),
                    coverage=len(known)/max(1,len(basis)))

    @staticmethod
    def fuel(distance_km, request, source, stamp, start, end):
        base = Decimal(str(distance_km))*Decimal(request.consumption)/100*Decimal(request.petrol)*request.cars
        return CostItem('Benzin für Hin- und Rückfahrt', str(money(base*Decimal('0.9'))),
                        str(money(base*Decimal('1.2'))), 'geschätzt', source, stamp,
                        f'{request.adults} Erwachsene, {request.cars} Fahrzeuge, {start} bis {end}',
                        f'{distance_km:.1f} Straßen-km × {request.consumption} l/100 km × '
                        f'{request.petrol} EUR/l × {request.cars} Fahrzeuge; -10/+20 % Verbrauch. '
                        'Verbrauch und Benzinpreis sind Nutzereingaben, kein aktueller Tankstellenpreis.').to_dict()

    @staticmethod
    def normalize(amount, unit, adults, rooms, nights, *, capacity=None, equipment_confirmed=False):
        """Only normalize known EUR prices with explicit units and occupancy evidence."""
        if capacity is None or capacity < adults:
            raise ValueError('Belegung ist nicht belegt')
        factors = {'Person/Nacht': adults*nights, 'Zimmer/Nacht': rooms*nights,
                   'Bett/Nacht': adults*nights, 'Aufenthalt': 1}
        if unit == 'Stellplatz/Nacht' and equipment_confirmed:
            factors[unit] = rooms*nights
        if unit not in factors:
            raise ValueError('Unbekannte Preiseinheit oder ungeklärte Campingausstattung')
        return money(Decimal(amount)*factors[unit])

    @staticmethod
    def vignette_count(outbound, inbound, valid_days):
        if valid_days < 1 or inbound < outbound:
            raise ValueError('Ungültiger Gültigkeitszeitraum')
        return 1 if (inbound-outbound).days < valid_days else 2
