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

    def __post_init__(self):
        if date.fromisoformat(self.end) <= date.fromisoformat(self.start): raise ValueError('Ungültige Reisedaten')
        if not 1 <= self.adults <= 40 or not 1 <= self.rooms <= self.adults: raise ValueError('Ungültige Reisegruppe')
        occupancy=self.occupancy or tuple(self.adults//self.rooms+(i<self.adults%self.rooms) for i in range(self.rooms))
        if len(occupancy)!=self.rooms or sum(occupancy)!=self.adults or min(occupancy)<1: raise ValueError('Zimmerbelegung passt nicht zur Reisegruppe')
        object.__setattr__(self,'occupancy',tuple(occupancy))

    @classmethod
    def from_trip(cls,trip,start=None,end=None):
        r=trip['request']
        return cls(r['origin'],trip['destination']['name'],start or trip['start'],end or trip['end'],r['adults'],r['rooms'],
                   accommodation_types=tuple(r.get('accommodation_types') or ('Hotel','Ferienwohnung')))

    def to_dict(self):
        return json.loads(json.dumps(asdict(self)))

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
    stale_ids=set()
    for result in trip.get('offer_searches',{}).values():
        for offer in result.get('offers',[])+result.get('previous_offers',[]):
            expiry=offer.get('valid_until')
            if expiry and datetime.fromisoformat(expiry) <= current:
                offer['price_status']='veraltet';stale_ids.add(offer['identifier'])
        if result.get('offers') and all(x.get('price_status')=='veraltet' for x in result['offers']):result['status']='stale'
    for item in trip.get('lodgings',[]):
        expiry=(item.get('offer') or {}).get('valid_until')
        if item.get('offer_id') in stale_ids or (expiry and datetime.fromisoformat(expiry)<=current):
            item['price']['status']='veraltet';item['booking_status']='Gespeichertes Angebot veraltet; erneut prüfen'
    for item in trip.get('transports',[]):
        expiry=(item.get('offer') or {}).get('valid_until')
        if item.get('offer_id') in stale_ids or (expiry and datetime.fromisoformat(expiry)<=current):
            item['status']='Gespeichertes Angebot veraltet; erneut prüfen'
            for cost in item.get('costs',[]):
                if cost.get('low') is not None:cost['status']='veraltet'
    for item in trip.get('activities',[]):
        offer=item.get('activity_price') or {}
        expiry=offer.get('valid_until')
        if expiry and datetime.fromisoformat(expiry)<=current:
            offer['price_status']='veraltet'
            if not item.get('price_status','').startswith('Gespeicherter Tarif veraltet'):
                item['price_status']='Gespeicherter Tarif veraltet; neu prüfen · '+item.get('price_status','')
    return trip
