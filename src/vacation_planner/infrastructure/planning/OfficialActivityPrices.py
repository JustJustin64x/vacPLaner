"""Small, audited tariff adapters. Published admission is not dated ticket inventory."""
import re
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

from ...core.planning.TravelOffers import OfferResult, TravelOffer, amount


class OfficialActivityPrices:
    name='Offizielle Aktivitätstarife';category='activities'
    SOURCES={
        'Innsbruck':('Museum Goldenes Dachl','https://www.innsbruck.gv.at/freizeit/kultur/museen-stadtarchiv/museum-goldenes-dachl','innsbruck'),
        'Bled':('Burg Bled','https://www.blejski-grad.si/sl/nacrtuj-obisk/cenik/','bled'),
        'London':('National Gallery','https://www.nationalgallery.org.uk/visiting/plan-your-visit','london'),
        'Berlin':('Futurium','https://futurium.de/de/besuch','berlin'),
    }

    def __init__(self,http):self.http=http

    @staticmethod
    def parse(body,adapter):
        soup=BeautifulSoup(body,'html.parser');text=soup.get_text(' ',strip=True)
        if adapter=='innsbruck':
            nodes=[x.get_text(' ',strip=True) for x in soup.select('li') if x.find('strong') and x.find('strong').get_text(strip=True)=='Standardeintritt']
            if len(nodes)!=1:raise ValueError('Standardeintritt nicht eindeutig ausgezeichnet')
            match=re.fullmatch(r'Standardeintritt\s*:\s*(\d+,\d{2})\s*Euro',nodes[0])
            if not match:raise ValueError('Unbekanntes Format des Standardeintritts')
            return str(amount(match[1])),nodes[0],'Öffnungszeiten, Schließtage und künftige Tarifgeltung prüfen; keine datierte Eintrittskarte.'
        if adapter=='bled':
            tables=soup.select('table')
            if not tables:raise ValueError('Offizielle Tariftabelle fehlt')
            rows=[r for r in tables[0].select('tr') if r.select('td') and r.select('td')[0].get_text(strip=True)=='Odrasli']
            if len(rows)!=1:raise ValueError('Erwachsenentarif nicht eindeutig')
            cells=rows[0].select('td');value=cells[1].get_text(' ',strip=True)
            match=re.fullmatch(r'(\d+,\d{2})\s*EUR',value)
            if not match:raise ValueError('Unbekanntes Format des Erwachsenentarifs')
            return str(amount(match[1])),'Odrasli '+value,'Veröffentlichter Tarif ab 01.01.2026; künftige Geltung und Besuchstermin prüfen. Sonderveranstaltungen nicht enthalten.'
        if adapter=='london' and any(p.get_text(' ',strip=True).startswith('General admission free.') for p in soup.select('p')):
            return '0.00','General admission free.','Kostenloser allgemeiner Eintritt; Sonderausstellungen teilweise kostenpflichtig. Öffnung und Gruppenanmeldung ab acht Personen prüfen.'
        headings=[h for h in soup.select('h2') if h.get_text(strip=True)=='Tickets']
        if adapter=='berlin' and len(headings)==1 and headings[0].find_next_sibling('p') and headings[0].find_next_sibling('p').get_text(' ',strip=True).startswith('Der Eintritt ist kostenfrei.'):
            return '0.00','Der Eintritt ist kostenfrei.','Allgemeiner Eintritt kostenlos; Workshops, Führungen und Veranstaltungen können kostenpflichtig sein. Öffnung prüfen; Gruppen ab 15 Personen anmelden. Schließfach-Münzpfand separat.'
        raise ValueError('Offizielle Preisangabe nicht gefunden; kein Nullpreis angenommen')

    def search(self,query,trip,context):
        spec=self.SOURCES.get(query.destination)
        if not spec:return OfferResult(self.name,self.category,'unsupported',query.to_dict(),message='Keine geprüfte offizielle Tarif-Anbindung für dieses Ziel; übrige Aktivitäten bleiben preislich offen.')
        name,url,adapter=spec
        topics=['Kultur']+(['Kostenlos'] if adapter in ('london','berlin') else [])
        interests=trip.get('request',{}).get('interests',{})
        if any(interests.values()) and not any(interests.get(topic,0) for topic in topics):
            return OfferResult(self.name,self.category,'unsupported',query.to_dict(),message='Keine geprüfte offizielle Tarif-Anbindung für die gewählten Interessen an diesem Ziel. Keine fremden Interessen ergänzt.')
        body,stamp=self.http.get(url,context)
        unit,evidence,note=self.parse(body,adapter);group=str(amount(unit)*query.adults)
        offer=TravelOffer(self.name,self.category,'activity:'+adapter,url,stamp,query.to_dict(),group,'EUR','indicative',group,
            availability='published_tariff_not_ticket_availability',valid_until=(datetime.fromisoformat(stamp)+timedelta(days=1)).isoformat(),
            included=['Allgemeiner Eintritt für '+str(query.adults)+' Erwachsene'],unresolved=[note],
            details={'activity_name':name,'unit_price':unit,'unit':'Erwachsene pro Eintritt','kind':'free_access' if amount(unit)==0 else 'published_tariff',
                     'date_confirmed':False,'period_note':note,'topics':topics,'currency_note':'Kostenloser Zugang ohne Währungsumrechnung' if amount(unit)==0 else 'Tarif in EUR'},
            evidence={'selector':{'innsbruck':'li > strong: Standardeintritt','bled':'table:first Odrasli','london':'General admission free.','berlin':'Der Eintritt ist kostenfrei.'}[adapter], 'normalization':'Veröffentlichter regulärer Erwachseneneintritt × Gruppengröße; keine Verfügbarkeitszusage'})
        return OfferResult(self.name,self.category,'found',query.to_dict(),[offer],'Offizieller Eintrittstarif gelesen; keine datierte Verfügbarkeit geprüft.',sources=[url])
