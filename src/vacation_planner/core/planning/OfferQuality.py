"""Offer checks and fee arithmetic. No HTTP, model or GUI dependencies."""
from datetime import date,datetime,timezone
import json
from .TravelOffers import amount
from .CostItem import CostItem

LABELS={'verified':'Anfragebezug geprüft; keine Buchungszusage','partial':'Teilweise geprüft; Angaben fehlen',
 'reference':'Nur Richtwert oder Preisbeispiel','conflict':'Widersprüchliche Angaben','outdated':'Veraltet oder abgelaufen',
 'mismatch':'Passt nicht zu den Reiseangaben','unknown':'Nicht ausreichend überprüfbar'}


def fee_costs(offer):
    """Amounts already supplied by adapters, never inferred from model prose."""
    costs=[];seen={};conflicts=[]
    for fee in offer.get('additional_fees',[]):
        key=str(fee.get('id') or ' '.join(fee.get('label','Gebühr').casefold().split()))
        signature=json.dumps({k:fee.get(k) for k in ('eur_amount','currency','included','optional')},sort_keys=True)
        if key in seen:
            if seen[key]!=signature:conflicts.append('Abweichende Beträge oder Leistungsumfänge derselben Gebühr')
            continue
        seen[key]=signature
        if fee.get('included') is True:continue
        value=fee.get('eur_amount');currency=fee.get('currency','EUR')
        if currency!='EUR':value=None
        # An explicit original amount in another currency is not an EUR amount.
        if value is not None:
            try:value=str(amount(value))
            except (ValueError,TypeError):value=None;conflicts.append('Ungültiger Betrag einer zusätzlichen Gebühr')
        if fee.get('basis') not in (None,'total','group'):value=None
        costs.append(CostItem(fee.get('label','Zusatzgebühr'),value,value,'aktuell abgerufen' if value is not None else 'unbekannt',
            offer.get('source',''),offer.get('retrieved_at',''),optional=fee.get('optional') is True).to_dict())
    if conflicts:costs.append(CostItem('Widersprüchliche Pflichtgebühren').to_dict())
    return costs,conflicts


def assess(offer,query,request=None,now=None):
    now=now or datetime.now(timezone.utc);gaps=[];conflicts=[];mismatches=[];d=offer.get('details',{});p=offer.get('parameters',{})
    def gap(field,message):gaps.append(dict(field=field,message=message))
    if p!=query.to_dict():mismatches.append('Anbieterparameter weichen von der Reiseanfrage ab')
    try:
        start,end=date.fromisoformat(p['start']),date.fromisoformat(p['end'])
        nights=(end-start).days
        if nights<=0:mismatches.append('Ungültiger Reisezeitraum')
        if d.get('nights') is not None and d['nights']!=nights:mismatches.append('Übernachtungsanzahl widerspricht dem Zeitraum')
    except (KeyError,TypeError,ValueError):gap('period','Gültiger Reisezeitraum nicht belegt');start=end=None
    outdated=False
    try:
        retrieved=datetime.fromisoformat(offer['retrieved_at']);age=(now-retrieved).total_seconds()
        if age>600 and offer.get('category')!='activities':outdated=True
        if age<0:gap('retrieved_at','Quellenabruf liegt in der Zukunft')
        expiry=offer.get('valid_until')
        if expiry:outdated=outdated or datetime.fromisoformat(expiry)<=now
        else:gap('freshness','Keine technische Preisgültigkeit dokumentiert')
    except (KeyError,TypeError,ValueError):gap('retrieved_at','Quellenzeit oder Gültigkeit nicht eindeutig dokumentiert')
    if end and end<now.date():outdated=True
    basis=offer.get('price_basis');reference=basis=='indicative' or offer.get('evidence',{}).get('price_qualifier')=='from'
    eligible=basis in ('group_stay','group_roundtrip') and not reference
    if reference or d.get('date_confirmed') is False:gap('period_validity','Preisgültigkeit für den gewählten Zeitraum nicht bestätigt')
    if basis not in ('group_stay','group_roundtrip'):gap('basis','Kein bestätigter Gruppenpreis für den gesamten Aufenthalt bzw. beide Fahrtrichtungen')
    if offer.get('availability')!='available_at_retrieval':gap('availability','Verfügbarkeit für die Anfrage nicht bestätigt');eligible=False
    if offer.get('eur_amount') is None or offer.get('original_currency')!='EUR':gap('currency','Kein belegter EUR-Betrag oder Wechselkurs');eligible=False
    try:
        if offer.get('eur_amount') is not None:
            value=amount(offer['eur_amount'])
            if offer.get('original_currency')=='EUR' and value!=amount(offer['original_amount']):conflicts.append('Originalbetrag und EUR-Betrag widersprechen sich')
            if offer.get('original_currency')!='EUR' and not offer.get('fx'):conflicts.append('Unbelegte Währungsumrechnung')
    except (KeyError,TypeError,ValueError):conflicts.append('Ungültige Betragsangabe')
    if offer.get('category')=='lodging':
        if d.get('units') is not None and d['units']!=query.rooms:mismatches.append('Anzahl angebotener Einheiten passt nicht zur Zimmeranfrage')
        if d.get('capacity') is not None and d['capacity']<query.adults:mismatches.append('Belegte Kapazität reicht nicht für die Gruppe')
        if not offer.get('evidence',{}).get('parameter_echo'):gap('occupancy','Zimmerbelegung nicht unabhängig durch Anbieterparameter bestätigt')
        if not offer.get('evidence',{}).get('fees_complete'):gap('fees','Vollständigkeit aller verpflichtenden Gebühren nicht ausdrücklich belegt')
    if offer.get('category') in ('rail','flight'):
        legs=d.get('legs',[])
        if legs and len(legs)!=2:mismatches.append('Hin- und Rückreise nicht gemeinsam belegt');eligible=False
        if not legs:gap('directions','Datierte Verbindungsabschnitte nicht vorhanden')
        elif len(legs)==2:
            try:
                if datetime.fromisoformat(legs[0]['departure']).date().isoformat()!=query.start or datetime.fromisoformat(legs[1]['departure']).date().isoformat()!=query.end:mismatches.append('Fahrtdaten passen nicht zu Hin- und Rückreise')
            except (KeyError,TypeError,ValueError):gap('directions','Abfahrtsdaten der beiden Richtungen nicht vollständig belegt')
        if d.get('surcharge_unknown'):gap('surcharge','Zusätzlicher Pflichtzuschlag: Betrag oder Einbezug nicht eindeutig belegt')
    costs,fee_conflicts=fee_costs(offer);conflicts+=fee_conflicts
    if any(c['low'] is None and not c['optional'] for c in costs):gap('fees','Mindestens eine zusätzliche Pflichtgebühr ist unbekannt')
    for text in offer.get('unresolved',[]):gap('provider',text)
    for name in (request or {}).get('required',[]):
        value=(d.get('property') or {}).get('amenities',{}).get(name)
        if offer.get('category')=='lodging':
            if value is False:mismatches.append('Pflichtleistung ausdrücklich ausgeschlossen: '+name)
            elif value is not True:gap('required','Pflichtleistung unbekannt: '+name)
    for name in (request or {}).get('desired',[]):
        if offer.get('category')=='lodging' and (d.get('property') or {}).get('amenities',{}).get(name) is not True:gap('desired','Gewünschte Leistung/deren Aufpreis unbekannt: '+name)
    state='conflict' if conflicts else 'mismatch' if mismatches else 'outdated' if outdated or offer.get('price_status')=='veraltet' else 'reference' if reference else 'unknown' if offer.get('eur_amount') is None else 'partial' if gaps else 'verified'
    if state in ('conflict','mismatch','outdated','reference') or any(g['field'] in ('period','retrieved_at','currency','availability') for g in gaps):eligible=False
    return dict(version=1,status=state,label=LABELS[state],price_eligible=eligible,gaps=gaps,conflicts=conflicts,mismatches=mismatches,
        fee_costs=costs,source_publication_at=offer.get('evidence',{}).get('publication_at'),checked_at=now.isoformat(),booking_guarantee=False)


def mark_conflicts(offers):
    """Only simultaneous same-offer/same-scope observations conflict, not new prices."""
    seen={}
    for o in offers:
        details=o.get('details',{})
        key=json.dumps([o.get('identifier'),o.get('parameters'),o.get('retrieved_at'),details.get('tariff_id'),details.get('board'),details.get('property',{}).get('id')],sort_keys=True)
        prior=seen.get(key)
        if prior and (prior.get('original_amount'),prior.get('original_currency'))!=(o.get('original_amount'),o.get('original_currency')):
            for item in (prior,o):item['quality'].update(status='conflict',label=LABELS['conflict'],price_eligible=False);item['quality']['conflicts'].append('Abweichende Preise derselben Angebots-/Tarif-/Zeitidentität')
        else:seen[key]=o
