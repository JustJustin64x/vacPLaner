"""Serializable offer contract, separate search and price status, no GUI dependencies."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import hashlib
import json
from typing import Protocol


STATUS_LABELS = {
    'not_checked': 'Noch nicht geprüft', 'running': 'Prüfung läuft',
    'found': 'Angebot gefunden', 'no_offers': 'Keine passenden Angebote',
    'not_bookable_yet': 'Zeitraum noch nicht buchbar', 'access_missing': 'Zugang fehlt',
    'blocked': 'Zugriff blockiert', 'error': 'Technischer Fehler',
    'cancelled': 'Prüfung abgebrochen', 'unsupported': 'Anfrage nicht unterstützt',
    'stale': 'Gespeichertes Angebot veraltet',
}


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def amount(value,allow_negative=False):
    """Parse explicit monetary fields, never arbitrary webpage text."""
    text=str(value).replace('\u00a0','').replace(' ','')
    if ',' in text:
        text=text.replace('.','').replace(',','.')
    try: result=Decimal(text)
    except InvalidOperation: raise ValueError('Ungültiger Angebotsbetrag') from None
    if not result.is_finite() or (result < 0 and not allow_negative): raise ValueError('Ungültiger Angebotsbetrag')
    return result.quantize(Decimal('.01'),rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class OfferQuery:
    origin: str
    destination: str
    start: str
    end: str
    adults: int
    rooms: int = 1
    occupancy: tuple = ()
    accommodation_types: tuple = ('Hotel','Ferienwohnung')
    currency: str = 'EUR'
    travel_class: str = '2'
    discount_cards: tuple = ()
    children_ages: tuple = ()
    room_assignments: tuple = ()
    required_amenities: tuple = ()

    def __post_init__(self):
        if date.fromisoformat(self.end) <= date.fromisoformat(self.start): raise ValueError('Ungültige Reisedaten')
        from .RoomParty import room_parties
        assignments=self.room_assignments
        if self.occupancy and not assignments:
            if self.children_ages:raise ValueError('Kinder benötigen eine eindeutige Zimmeraufteilung.')
            assignments=[{'adults':n,'children_ages':[]} for n in self.occupancy]
        parties=room_parties(self.adults,self.children_ages,self.rooms,assignments)
        occupancy=tuple(p.adults for p in parties)
        if self.occupancy and tuple(self.occupancy)!=occupancy:raise ValueError('Zimmerbelegung widerspricht der Aufteilung')
        object.__setattr__(self,'occupancy',occupancy)
        object.__setattr__(self,'children_ages',tuple(self.children_ages))
        object.__setattr__(self,'room_assignments',parties)

    @classmethod
    def from_trip(cls,trip,start=None,end=None):
        r=trip['request']
        return cls(r['origin'],trip['destination']['name'],start or trip['start'],end or trip['end'],r['adults'],r['rooms'],
                   accommodation_types=tuple(r.get('accommodation_types') or ('Hotel','Ferienwohnung')),
                   children_ages=tuple(r.get('children_ages',[])),room_assignments=r.get('room_assignments',[]),required_amenities=tuple(r.get('required',[])))

    def to_dict(self):
        data=json.loads(json.dumps(asdict(self)))
        # Keep historical adult-only offer/cache contracts readable. Explicit
        # adult allocations are already represented by occupancy.
        if not self.children_ages:
            data.pop('children_ages');data.pop('room_assignments')
        if not self.required_amenities:data.pop('required_amenities')
        return data

    @property
    def persons(self):return self.adults+len(self.children_ages)

    @property
    def group_label(self):
        return f'{self.adults} Erwachsene'+(f' und {len(self.children_ages)} Kinder' if self.children_ages else '')

    def cache_key(self,provider,category):
        payload={'provider':provider,'category':category,'parameters':self.to_dict(),'direction':'roundtrip','version':1}
        return 'offers:'+hashlib.sha256(json.dumps(payload,sort_keys=True,ensure_ascii=False).encode()).hexdigest()


@dataclass
class TravelOffer:
    provider: str
    category: str
    identifier: str
    source: str
    retrieved_at: str
    parameters: dict
    original_amount: str
    original_currency: str
    price_basis: str
    eur_amount: str | None
    price_status: str = 'aktuell abgerufen'
    availability: str = 'available_at_retrieval'
    valid_until: str = ''
    included: list = field(default_factory=list)
    additional_fees: list = field(default_factory=list)
    unresolved: list = field(default_factory=list)
    details: dict = field(default_factory=dict)
    evidence: dict = field(default_factory=dict)
    fx: dict | None = None

    def __post_init__(self):
        self.original_amount=str(amount(self.original_amount))
        if self.eur_amount is not None:
            self.eur_amount=str(amount(self.eur_amount))
            if self.original_currency=='EUR' and self.eur_amount!=self.original_amount:raise ValueError('Widersprüchlicher EUR-Originalbetrag')
            if self.original_currency!='EUR' and not self.fx: raise ValueError('EUR-Umrechnung ohne belegten Wechselkurs')
        if self.price_basis not in ('group_stay','group_roundtrip','group_oneway','indicative'):
            raise ValueError('Nicht normalisierter Preisbezug')
        if not self.source.startswith('https://'): raise ValueError('Angebot benötigt HTTPS-Quelle')

    def to_dict(self): return asdict(self)


@dataclass
class OfferResult:
    provider: str
    category: str
    status: str
    parameters: dict
    offers: list = field(default_factory=list)
    message: str = ''
    checked_at: str = field(default_factory=utc_now)
    sources: list = field(default_factory=list)

    def __post_init__(self):
        if self.status not in STATUS_LABELS: raise ValueError('Unbekannter Suchstatus')
        if self.status=='found' and not self.offers: raise ValueError('Erfolgsstatus ohne Angebot')

    def to_dict(self):
        value=asdict(self);value['offers']=[x.to_dict() if hasattr(x,'to_dict') else x for x in self.offers]
        return value


class OfferProvider(Protocol):
    name: str
    category: str
    def search(self,query: OfferQuery,trip: dict,context) -> OfferResult: ...


def expire_offers(trip,now=None):
    """No network and no mutation of original prices; expired prices lose budget eligibility."""
    current=now or datetime.now(timezone.utc)
    try:expected_parameters=OfferQuery.from_trip(trip).to_dict()
    except (KeyError,TypeError,ValueError):expected_parameters=None  # historical incomplete snapshots still load
    def expired(offer):
        if not offer:return False
        if expected_parameters is not None and offer.get('category')!='activities' and offer.get('parameters')!=expected_parameters:return True
        try:
            retrieved=datetime.fromisoformat(offer['retrieved_at'])
            if retrieved.tzinfo is None or retrieved>current:return True
            limits=[]
            if offer.get('valid_until'):limits.append(datetime.fromisoformat(offer['valid_until']))
            if offer.get('category')!='activities':limits.append(retrieved+timedelta(minutes=10))
            return not limits or min(limits)<=current
        except (KeyError,TypeError,ValueError):return True
    def mark(offer):
        offer['price_status']='veraltet'
        if offer.get('quality'):
            from .OfferQuality import LABELS
            offer['quality'].update(status='outdated',label=LABELS['outdated'],price_eligible=False)
    for result in trip.get('offer_searches',{}).values():
        for offer in result.get('offers',[])+result.get('previous_offers',[]):
            if expired(offer):mark(offer)
        if result.get('offers') and all(x.get('price_status')=='veraltet' for x in result['offers']):result['status']='stale'
    ledger=trip.get('lodging_research')
    if ledger:
        for entry in ledger.get('entries',[]):
            for offer in entry.get('offers',[])+entry.get('previous_offers',[]):
                if expired(offer):mark(offer)
            if entry['state']=='confirmed' and entry.get('offers') and all(expired(o) for o in entry['offers']):
                entry.update(state='partial',reason='Gespeicherte Preisquote veraltet; erneut prüfen')
        from .LodgingResearch import summarize
        summarize(ledger)
    for item in trip.get('lodgings',[]):
        if expired(item.get('offer')):
            mark(item['offer']);item['price']['status']='veraltet';item['booking_status']='Gespeichertes Angebot veraltet; erneut prüfen'
    for item in trip.get('transports',[]):
        if expired(item.get('offer')):
            mark(item['offer']);item['status']='Gespeichertes Angebot veraltet; erneut prüfen'
            for cost in item.get('costs',[]):
                if cost.get('low') is not None:cost['status']='veraltet'
    for item in trip.get('activities',[]):
        offer=item.get('activity_price') or {}
        if expired(offer):
            mark(offer)
            if not item.get('price_status','').startswith('Gespeicherter Tarif veraltet'):
                item['price_status']='Gespeicherter Tarif veraltet; neu prüfen · '+item.get('price_status','')
    return trip
