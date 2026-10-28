from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from zoneinfo import ZoneInfo
from datetime import datetime

INTERESTS = ('Wandern', 'Baden', 'Natur', 'Berge', 'Kultur', 'Städte', 'Feiern', 'Restaurants', 'Veranstaltungen', 'Kostenlos')
AMENITIES = ('Küche', 'Frühstück', 'Pool', 'Parkplatz', 'Haustiere', 'Kostenlose Stornierung')


def today():
    return datetime.now(ZoneInfo('Europe/Berlin')).date()


def next_july():
    now = today()
    year = now.year if now < date(now.year, 7, 1) else now.year + 1
    return date(year, 7, 1).isoformat(), date(year, 7, 31).isoformat()


@dataclass
class SearchRequest:
    origin: str = 'Berlin'
    address: str = ''
    earliest: str = field(default_factory=lambda: next_july()[0])
    latest: str = field(default_factory=lambda: next_july()[1])
    min_days: int = 7
    max_days: int = 7
    adults: int = 2
    rooms: int = 1
    budget: str = '2000'
    countries: list = field(default_factory=list)
    regions: list = field(default_factory=list)
    excluded: list = field(default_factory=list)
    interests: dict = field(default_factory=lambda: {k: 0 for k in INTERESTS})
    weights: dict = field(default_factory=lambda: {'Preis': 1, 'Reisezeit': 1, 'Komfort': 1, 'Interessen': 1})
    modes: list = field(default_factory=lambda: ['Auto', 'Zug', 'Flug'])
    max_hours: str = ''
    cars: int = 1
    seats: int = 5
    consumption: str = '7.0'
    petrol: str = '1.80'
    accommodation_types: list = field(default_factory=lambda: ['Hotel', 'Ferienwohnung'])
    required: list = field(default_factory=list)
    desired: list = field(default_factory=list)
    max_center_km: str = ''
    shortlist: int = 6
    request_budget: int = 24
    timeout_seconds: int = 300

    target_type: str = 'gemischt'
    surroundings: bool = True
    lodging_radius_km: str = '15'
    activity_radius_km: str = '30'
    show_ideas: bool = False

    def validate(self):
        for key in ('min_days','max_days','adults','rooms','cars','seats','shortlist','request_budget','timeout_seconds'):
            if isinstance(getattr(self,key),bool) or not isinstance(getattr(self,key),int):
                raise ValueError(key+': bitte eine ganze Zahl angeben.')
        if not isinstance(self.origin,str) or not isinstance(self.address,str):
            raise ValueError('Startort und Adresse müssen Text sein.')
        for key in ('countries','regions','excluded','modes','accommodation_types','required','desired'):
            value=getattr(self,key)
            if not isinstance(value,list) or any(not isinstance(v,str) or not v.strip() for v in value):
                raise ValueError(key+': bitte eine Liste nichtleerer Namen angeben.')
        if not isinstance(self.surroundings,bool) or not isinstance(self.show_ideas,bool):
            raise ValueError('Umgebungssuche und Ideenanzeige müssen ja/nein sein.')
        for group in (self.interests,self.weights):
            if not isinstance(group,dict):raise ValueError('Gewichte müssen als benannte Zahlen vorliegen.')
            for key,value in group.items():
                try:number=Decimal(str(value).replace(',','.'))
                except InvalidOperation:raise ValueError('Gewicht für '+key+' ist keine Zahl.') from None
                if not number.is_finite():raise ValueError('Gewichte müssen endliche Zahlen sein.')
                group[key]=int(number) if number==number.to_integral_value() else float(number)
        for key in ('budget','consumption','petrol','max_hours','max_center_km','lodging_radius_km','activity_radius_km'):
            value=str(getattr(self,key)).strip().replace(',','.')
            if not value and key not in ('max_hours','max_center_km'):
                raise ValueError(key+': bitte eine positive Zahl eingeben.')
            try:
                if value:Decimal(value)
            except InvalidOperation:raise ValueError(key+': bitte eine Zahl eingeben.') from None
            setattr(self,key,value)
        if self.target_type not in ('gemischt','Stadt','kleiner Ort','See/Küste','Berge/Natur'):
            raise ValueError('Unbekannter Zieltyp.')
        for key in ('lodging_radius_km','activity_radius_km'):
            value=Decimal(getattr(self,key))
            if not value.is_finite() or not 0 < value <= 50:
                raise ValueError('Umkreis muss zwischen 0 und 50 km liegen (größer als null).')
        try:
            first, last = date.fromisoformat(self.earliest), date.fromisoformat(self.latest)
        except (TypeError,ValueError):
            raise ValueError('Reisezeitraum bitte als JJJJ-MM-TT eingeben.') from None
        if first < today() or last < first:
            raise ValueError('Der Zeitraum muss in der Zukunft liegen und richtig geordnet sein.')
        if first.year != last.year:
            raise ValueError('Bitte einen Zeitraum innerhalb eines Reisejahres wählen.')
        if not self.origin.strip():
            raise ValueError('Bitte einen Startort eingeben.')
        if not 2 <= self.min_days <= self.max_days <= 60 or (last-first).days+1 < self.min_days:
            raise ValueError('Reisedauer: 2–60 Kalendertage; mindestens eine Reise muss in den Zeitraum passen.')
        if not 1 <= self.adults <= 40 or not 1 <= self.rooms <= self.adults:
            raise ValueError('1–40 Erwachsene und höchstens ein Zimmer pro Person angeben.')
        if not self.modes or any(m not in ('Auto', 'Zug', 'Flug') for m in self.modes):
            raise ValueError('Mindestens ein gültiges Verkehrsmittel wählen.')
        if 'Auto' in self.modes and (self.cars < 1 or self.seats < 1 or self.cars*self.seats < self.adults):
            raise ValueError('Die Gruppe passt nicht in die angegebenen Fahrzeuge.')
        if not self.accommodation_types or set(self.accommodation_types)-{'Hotel', 'Ferienwohnung', 'Camping'}:
            raise ValueError('Mindestens einen gültigen Unterkunftstyp wählen.')
        if set(self.required+self.desired)-set(AMENITIES):
            raise ValueError('Unbekanntes Ausstattungsmerkmal.')
        for name, value in [('Budget', self.budget), ('Verbrauch', self.consumption), ('Benzinpreis', self.petrol)]:
            number = Decimal(value)
            if not number.is_finite() or number <= 0:
                raise ValueError(name+' muss eine positive Zahl sein.')
        for value in (self.max_hours, self.max_center_km):
            if value and (not Decimal(value).is_finite() or Decimal(value) <= 0):
                raise ValueError('Reisezeit und Entfernung müssen positiv sein oder leer bleiben.')
        for group,limit in ((self.interests,5),(self.weights,100)):
            if any(not Decimal(str(v)).is_finite() or not 0 <= Decimal(str(v)) <= limit for v in group.values()):
                raise ValueError(f'Interessen: 0–5; Vergleichsgewichte: 0–100 (Grenze {limit}).')
        if set(self.interests)-set(INTERESTS) or set(self.weights)-{'Preis','Reisezeit','Komfort','Interessen'}:
            raise ValueError('Unbekannte Gewichtung.')
        if not 3 <= self.shortlist <= 12 or not 4 <= self.request_budget <= 40 or not 10 <= self.timeout_seconds <= 600:
            raise ValueError('Vorauswahl 3–12, Abfragebudget 4–40, Zeitlimit 10–600 Sekunden.')

    def normalized_weights(self):
        values = {k: Decimal(str(self.weights.get(k, 0))) for k in ('Preis','Reisezeit','Komfort','Interessen')}
        total = sum(values.values())
        return {k: (v/total if total else Decimal('0.25')) for k,v in values.items()}

    def dates(self, limit=3):
        """Bounded, deterministic samples, never a claim about cheapest dates."""
        first, last = date.fromisoformat(self.earliest), date.fromisoformat(self.latest)
        lengths = list(dict.fromkeys([self.min_days, (self.min_days+self.max_days)//2, self.max_days]))
        result = []
        for index in range(limit):
            days = lengths[index % len(lengths)]
            available = (last-first).days-(days-1)
            if available < 0:
                continue
            start = first+timedelta(days=available*index//max(1,limit-1))
            pair = (start.isoformat(), (start+timedelta(days=days-1)).isoformat())
            if pair not in result:
                result.append(pair)
        return result

    def room_occupancy(self):
        return [self.adults//self.rooms+(i < self.adults%self.rooms) for i in range(self.rooms)]

    def to_dict(self):
        return asdict(self)
