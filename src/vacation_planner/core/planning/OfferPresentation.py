"""Shared German provenance/quality text for existing UI and PDF sections."""
from .OfferQuality import LABELS

ANALYSIS_LABELS={'selected':'Vorhandene Fundstellen lokal ausgewählt','no_observations':'Keine sicher auswertbaren Angebotsfundstellen',
 'budget_limited':'Analyse wegen Zeit-/Aufgabenlimit ausgelassen','cancelled':'Analyse abgebrochen',
 'unavailable_or_rejected':'KI nicht verfügbar oder Antwort verworfen; deterministische Prüfung bleibt maßgeblich'}


def quality_lines(offer):
    q=offer.get('quality')
    if not q:return []
    lines=[LABELS['outdated'] if offer.get('price_status')=='veraltet' else q['label'],
        'Anbieterabruf: '+offer.get('retrieved_at','unbekannt')+'; keine Preisgarantie oder Reservierung.',
        'Preisbasis: '+{'group_stay':'gesamte Gruppe und Aufenthalt','group_roundtrip':'gesamte Gruppe, Hin- und Rückfahrt','group_oneway':'gesamte Gruppe, nur einfache Fahrt','indicative':'Richtwert / veröffentlichter Tarif'}.get(offer.get('price_basis'),'unbekannt')]
    lines+=['Offen: '+g['message'] for g in q.get('gaps',[])]+q.get('conflicts',[])+q.get('mismatches',[])
    for fee in q.get('fee_costs',[]):lines.append(('Optional: ' if fee['optional'] else 'Zusätzlich verpflichtend: ')+fee['label']+' · '+(fee['low']+' EUR' if fee['low'] is not None else 'Betrag unbekannt'))
    for row in offer.get('evidence',{}).get('observations',[]):
        if row:lines.append('Originalnachweis '+row['pointer']+': '+row['quote']+' · Abruf '+row['retrieved_at'])
    return lines


def analysis_lines(analysis):
    if not analysis:return []
    lines=[ANALYSIS_LABELS.get(analysis.get('status'),'Analysezustand unbekannt'),
        'Auswahl vorhandener Quellenstellen; keine KI-Preise oder Buchungszusagen.']
    if analysis.get('cache_used'):lines.append('Sitzungscache; keine neue Quellenprüfung.')
    for f in analysis.get('accepted',[]):
        value=f['value'];unit=f['unit']
        if f['field']=='amenity' and isinstance(value,dict):
            value=value['name']+' · '+{'included':'ausdrücklich enthalten','extra':'optional/gegen Aufpreis','excluded':'ausdrücklich ausgeschlossen','described_only':'beschrieben; Preiseinbezug unbekannt'}[value['state']];unit=''
        elif f['field']=='price' and isinstance(value,dict):
            basis={'per_night':'pro Nacht','per_person':'pro Person','per_room':'pro Zimmer','per_room_night':'pro Zimmer und Nacht','total':'Gesamtbetrag','oneway':'einfache Fahrt','roundtrip':'Hin- und Rückfahrt'}[value['basis']]
            value=('Ab-Preis ' if value.get('qualifier')=='from' else 'Preis ')+value['amount']+' '+value['currency']+' · '+basis;unit=''
        elif f['field']=='fee' and isinstance(value,dict):
            value=str(value['amount'])+' '+value['currencyCode']+' · '+value.get('name','Preisbestandteil')+' (im ausgewiesenen Betrag enthalten)';unit=''
        elif f['field']=='availability':value='Zum Abruf als verfügbar angegeben' if value else 'Zum Abruf nicht als verfügbar angegeben';unit=''
        elif f['field']=='occupancy' and unit=='capacity':value=str(value)+' Personen Kapazität; keine Belegungszusage';unit=''
        else:
            value=str(value);unit={'nights':'Nächte'}.get(unit,unit)
        lines.append('Quellenhinweis' if f['validation']=='source_hint_only' else 'Geprüfte Fundstelle')
        lines.append(f['pointer']+': '+value+' '+unit+' · Quelle '+f['source_url']+' · Abruf '+f['retrieved_at'])
    return lines
