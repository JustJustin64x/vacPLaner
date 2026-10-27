from __future__ import annotations
from dataclasses import dataclass, asdict
from decimal import Decimal, ROUND_HALF_UP


def money(value):
    return Decimal(str(value)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


@dataclass
class CostItem:
    label: str
    low: str | None = None
    high: str | None = None
    status: str = 'unbekannt'
    source: str = ''
    retrieved_at: str = ''
    scope: str = ''
    method: str = ''
    optional: bool = False

    def __post_init__(self):
        if self.status not in ('aktuell abgerufen', 'geschätzt', 'veraltet', 'unbekannt'):
            raise ValueError('Unbekannter Preisstatus')
        if self.low is not None:
            lo, hi = Decimal(self.low), Decimal(self.high if self.high is not None else self.low)
            if not lo.is_finite() or not hi.is_finite() or lo < 0 or hi < lo:
                raise ValueError('Ungültiger Kostenbereich')
            self.low, self.high = str(money(lo)), str(money(hi))
            if self.status == 'unbekannt':
                raise ValueError('Ein unbekannter Preis darf keinen Betrag enthalten')
        elif self.high is not None:
            raise ValueError('Obere Grenze ohne untere Grenze')
        if self.status == 'geschätzt' and not self.method:
            raise ValueError('Schätzung benötigt eine Methode')

    def to_dict(self):
        return asdict(self)
