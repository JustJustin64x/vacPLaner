# Echte Angebotsrecherche – Stand 29.10.2026

## Umgesetzt und nachgewiesen

Zwei schlüssellose Nur-Lese-Zugänge liefern jetzt echte datierte Preise. Flugpreisrecherche und eine allgemeine Hotel-/Mehrzimmerabdeckung sind **nicht vollständig umgesetzt**.

| Kategorie | Funktionierender Zugang | Tatsächlich geprüfter Umfang |
|---|---|---|
| Bahn | Öffentliche RegioJet-Websuche und anschließende Tarifdetails | Prag–Brünn, 12.–14.11.2026, zweite Klasse, keine Rabattkarten: 2 Erwachsene zusammen 33,60 EUR; unabhängig abgefragt 5 Erwachsene zusammen 84,00 EUR. Jeweils zwei konkrete Züge, getrennte Fahrkarten. |
| Unterkunft | Öffentliche Smoobu-Gastbuchungsstrecke, verlinkt von [Apartments Innsbruck](https://www.apartments-innsbruck.com/en/buchen/) | 23.–25.11.2026, 2 Erwachsene, 1 Ferienwohnung. Unter anderem Loft Lodge 43: 234 EUR = 164 EUR Aufenthalt + 70 EUR Reinigung; Cozy Shelter Lodge 22: 244 EUR = 174 EUR Aufenthalt + 70 EUR Reinigung. Weitere passend zugeordnete Einheiten mit 254 und 276 EUR. |
| Flug | Kein funktionierender Preisadapter | Konkrete Zugangshindernisse unten. Die Anwendung meldet diese als Zugangsdiagnose; es werden keine Flugpreise erzeugt. |

Dies sind zum Abrufzeitpunkt angezeigte Preise, keine Reservierungen oder Preisgarantien. Bereinigte Herkunfts- und Ergebnisnachweise mit UTC-Zeit, tatsächlichen Parametern, Angebotskennung, Leistungsumfang und Übernahme in die Anwendung: [ANGEBOTSPRUEFUNG_2026-10-29.json](ANGEBOTSPRUEFUNG_2026-10-29.json). Die beiden Unterkunftsangebote betreffen unterschiedliche Ferienwohnungen am selben Standort, keinen unabhängigen Hotelmarktvergleich.

## Datenfluss und Bedienung

`SearchRequest → DiscoveryService → OpenTravelProvider.research_offers → getrennte Angebotsprovider → OfferResearchService → CostItem/RankingService → GUI/TripStore/PdfTripPresenter`.

Nach der bestehenden Zielrecherche werden die Ergebnisse zunächst sortiert. Die besten drei werden automatisch auf Angebote geprüft; `price_targets` ist zwischen 0 und 12 einstellbar. Für Preise existiert ein eigenes Budget von höchstens 32 HTTP-Aufrufen innerhalb der verbleibenden Suchzeit. Es werden keine Bilder abgerufen. Statische Ortsabfragen behalten ihr eigenes Budget. Jede Kategorie kann unabhängig erfolgreich sein oder fehlschlagen. Erweiterter Stand mit Aktivitäten und PDF-Szenarien: [Preisvergleich](PREISVERGLEICH.md).

Im normalen Reisevergleich ergänzt **Angebote aktuell prüfen** eine gezielte Hintergrundprüfung. Die Auswahl **Alle Preise / Unterkunft / Bahn / Flug / Aktivitäten** begrenzt die Kategorien. Sie arbeitet bis zu zehn Minuten mit maximal 40 öffentlichen Abfragen, zeigt Anbieter und Reiseparameter an und lässt sich über **Abbrechen** stoppen. Änderungen werden als Arbeitskopie angezeigt und erst ausdrücklich gespeichert. Auswahlwechsel während einer Recherche bleiben erhalten.

**Weitere Terminproben prüfen** untersucht maximal drei vorhandene konkrete Terminpaare mit demselben begrenzten Budget. Alle Kategorien einer Probe verwenden dasselbe Paar. Ergebnisse erscheinen getrennt in den Reisedetails; die gewählte Reise wird nicht auf einen anderen Termin umgestellt. Alte datierte Angebotspreise werden nicht in eine neue Probe übernommen.

Der gemeinsame Vertrag in `TravelOffers.py` hält Suchstatus, Preisstatus, Originalbetrag, EUR-Betrag, Preisbezug, tatsächliche Parameter, Quelle, Abrufzeit, Gültigkeit, enthaltene Leistungen, zusätzliche Gebühren und offene Angaben getrennt. Anbieterfehler sind keine leeren Suchergebnisse. Ein `found`-Ergebnis benötigt tatsächlich mindestens ein Angebot.

Angebote werden pro Prüfung neu abgefragt und nicht aus einem Preis-Cache bedient. Der vollständige Suchschlüssel berücksichtigt Personen, Zimmer, Belegung, Daten, Währung, Richtung und Tarifparameter; er steht für eine spätere kurze Cache-Nutzung bereit. Nur das statische RegioJet-Ortsverzeichnis wird sieben Tage gecacht. Die Anwendung setzt die Preisgültigkeit konservativ auf zehn Minuten. Beim Öffnen eines gespeicherten Stands wird ohne Netz geprüft, ob Angebote inzwischen veraltet sind; dann fließen sie nicht mehr als aktuelle Preise in Budget und Ranking ein. Der damalige Betrag bleibt sichtbar.

## RegioJet: produktiver Adapter

Die Produktions-Webseite lieferte HTTP 200. In ihren öffentlich ausgelieferten JavaScript-Dateien sind die tatsächlich verwendeten GET-Routen `/restapi/consts/locations`, `/restapi/routes/search/simple` und `/restapi/routes/{id}/simple` sowie die Parameter und Versionsheader belegt. Es wurden keine Endpunkte geraten und keine Transaktions-/Reservierungsrouten verwendet. Die [robots.txt](https://regiojet.com/robots.txt) gestattet den Abruf. Keine Registrierung oder kostenpflichtige API.

- Bahnhofsauswahl anhand des aktuellen Ortsverzeichnisses, exakter Ortsnamen und Anbieter-Aliasse; nur Orte mit Bahnhöfen.
- Hin- und Rückfahrt einzeln mit einem `REGULAR`-Eintrag je Erwachsenem; keine Rabattkarte und kein kreditkontogebundener Rabattpreis.
- Zusammenfassende „ab“-Preise werden verworfen. Erst Tarifdetails mit passender Personenliste, Datum, Start/Ziel, zweiter Klasse, Buchbarkeit und ausreichenden Plätzen liefern einen auswertbaren Preis.
- Zweite Klasse ist im offiziellen `/restapi/consts/seatClasses`-Verzeichnis belegt. Bus- und gemischte Bus-/Zugangebote werden nicht als Bahnangebote übernommen.
- Beide direkt zurückgegebenen Gruppentarife werden addiert; keine nochmalige Multiplikation mit Personen oder Richtungen. Zeiten, Abschnitte, Umstiege, Tarifklasse und Bedingungen bleiben im Snapshot.
- Das ist eine anbieterspezifische Webschnittstelle, kein zugesicherter öffentlicher API-Vertrag. Änderungen können eine Anpassung nötig machen. Keine zugesicherte gesamteuropäische Abdeckung.

Für Berlin–Innsbruck liefert RegioJet keine eindeutig passende reine Bahnquelle. Das wird als `unsupported` gemeldet, nicht als „keine Bahnverbindung in Europa“. Für Prag–Brünn im Juli 2027 war die aktuelle Anbieterantwort leer. Da sie keine eindeutige Buchungshorizontmeldung enthielt, lautet der Status `no_offers` und nicht unbewiesen „noch nicht buchbar“.

## Unterkünfte: produktiver Adapter und Grenzen

Die offizielle Innsbrucker Anbieter-Webseite verlinkt einen öffentlichen Smoobu-Gastbuchungswidget. Die alte Widget-URL leitet strukturiert auf `https://booking.smoobu.com/perfect-lodgings` weiter. Eine begrenzte lokale Playwright-Prüfung führte eine echte Datums-/Personensuche aus und belegte die vom Browser verwendete **GET**-Route `checkAvailability` und die sichtbare Preisaufschlüsselung. Es wurden keine Gastdaten ausgefüllt, Bedingungen bestätigt oder Buchungsschaltflächen ausgelöst.

Der integrierte Adapter benötigt den Browser anschließend nicht: Er verwendet dieselbe beobachtete öffentliche Nur-Lese-Anfrage. `booking.smoobu.com/robots.txt` lieferte eine HTML-Fehlerseite statt Regeln; `login.smoobu.com/robots.txt` HTTP 404. Ein `noindex` auf Gastseiten wird nicht als öffentliche Indexierungsfreigabe interpretiert. Keine Suchindexierung, Massenabfrage oder Verwendung der kostenpflichtigen Gastgeber-API.

Die Antwort des Anbieters enthält auch Wohnungen in anderen Orten. Übernommen werden ausschließlich die auf der offiziellen Innsbrucker Webseite belegten Einheiten, mit passender öffentlicher Objekt-ID **und** Namens-/Adressprüfung. Das Antwortfeld `bookUrl` muss Ankunft, Abreise, Erwachsene, Kinderzahl und Objektkennung exakt bestätigen. Nächte, Kapazität, Verfügbarkeit, Gesamtbetrag und Summe aller Preisbestandteile müssen übereinstimmen. Reinigung wird einmalig innerhalb des Gesamttotals erfasst. Fremdwährungen ohne belegten Kurs werden nicht umgerechnet.

Der geprüfte Umfang ist **eine Ferienwohnung für die tatsächlich angefragten Erwachsenen**. Hotel-only-Anfragen, mehrere Zimmer oder unbelegte Pflichtausstattung werden nicht passend gerechnet. Für fünf Erwachsene in drei Zimmern existiert daher noch kein bestätigter Unterkunftsgruppenpreis. Die gewünschte Juli-2027-Konfiguration wurde separat geprüft und ausdrücklich als nicht unterstützt dokumentiert. Die Testpreise aus November werden ihr nicht untergeschoben.

Verpflegung, Stornierung und Zahlungskonditionen sind in der Preisantwort nicht ausgewiesen und bleiben sichtbar offen. Die verlinkte aktuelle Betreiber-AGB-Seite lieferte HTTP 404; die alte Innsbrucker AGB-Seite ist erreichbar, wird aber nicht ungeprüft als Bedingung eines aktuellen konkreten Tarifs übernommen. In der Antwort nicht belegte allgemeine Zuschläge werden nicht erfunden. Nicht unterstützte Pflichtausstattung und eine vorgegebene maximale Zentrumsentfernung verhindern die automatische Aufnahme einer neuen, dafür nicht hinreichend belegten Wohnung.

## Weitere konkret geprüfte Wege

Alle folgenden Zugangsprüfungen erfolgten am 29.10.2026. Ein erreichbares Dokument oder eine Startseite ist kein erfolgreicher Angebotsabruf.

| Quelle / URL | Dokumentation / Erreichbarkeit / tatsächliches Ergebnis | Integration |
|---|---|---|
| [DB Buchung](https://www.bahn.de/buchung/start), [robots.txt](https://www.bahn.de/robots.txt) | Beide HTTP 200. Die Webseite lädt dynamische Suche; `/.rest/` ist explizit ausgeschlossen. Keine entsprechende interne Tarif-API verwendet. Bahnhofstafeln wurden nicht als Preisquelle eingesetzt. | Kein DB-Preisadapter. RegioJet ist der funktionierende Bahnweg. |
| [Hotel Lovec](https://www.lovechotel.com/), [Hotel Kompas](https://www.kompashotel.com/) | Beide HTTP 200, direkte Upperbooking-Einbindung ermittelt. Das öffentlich verlinkte Booking-Skript antwortet tatsächlich `Booking temporarily disabled.` | Keine Preise gewonnen. |
| [Hotel Astoria](https://www.hotelastoria-bled.com/), [Profitroom robots](https://booking.profitroom.com/robots.txt) | Direkter Buchungslink auf Profitroom gefunden. `Disallow: /`; keine Preisextraktion integriert. | Offen. |
| [Bled Tourismus](https://www.bled.si/en/accommodation/book/) | HTTP 200, keine auswertbaren datierten Angebote in der öffentlichen Seite. | Kein Preisadapter. |
| [Sava Hotels Bled](https://www.sava-hotels-resorts.com/en/sava-hotels-bled/), [robots](https://www.sava-hotels-resorts.com/robots.txt) | HTTP 200, reale Hotelkennungen und Buchungsleiste. Der im ausgelieferten Skript enthaltene Buchungszugang liegt unter dem ausgeschlossenen `/umbraco/`; nicht als Preisquelle verwendet. | Offen. |
| [Beds24 robots](https://beds24.com/robots.txt), [öffentliche Widget-Dokumentation](https://wiki.beds24.com/index.php/Make_Your_Own_Booking_Widget) | Gastseiten erreichbar, fünf Sekunden Crawl-Abstand genannt. Ein reales Seminarhaus ließ im geprüften Zeitraum ausschließlich Anfragen registrierter Veranstaltungsteilnehmer zu, keine geeigneten frei verfügbaren Reiseangebote. Keine Demo-Unterkunft als echten Preis verwendet. | Kein fertiger Adapter. |
| [a&o robots](https://www.aohostels.com/robots.txt) | Öffentliche Buchungsseite HTTP 200, parametrierte Buchungsstrecken ausdrücklich ausgeschlossen. | Offen. |
| [Cubilis robots](https://booking.cubilis.eu/robots.txt) | HTTP 200, `Disallow: /`. | Offen. |
| [SimpleBooking robots](https://www.simplebooking.it/robots.txt) | HTTP 200, Buchungs- und Kalendersituationspfade ausgeschlossen. | Offen. |

## Flug: ausdrücklich nicht abgenommen

| Quelle | Konkrete Prüfung und Blockade |
|---|---|
| [Norwegian](https://www.norwegian.com/en/) | Tatsächlicher öffentlicher Abruf HTTP 403. Keine Umgehung oder Wechsel auf versteckte Endpunkte. |
| [Transavia](https://www.transavia.com/home/en-eu) | Tatsächlicher öffentlicher Abruf HTTP 403. Keine Preisantwort. |
| [Icelandair robots](https://www.icelandair.com/robots.txt) | Bereits die Regelnseite HTTP 403; keine nachfolgenden Angebotsabfragen. |
| [easyJet Acceptable Use Policy](https://www.easyjet.com/en/help-centre/policy-terms-and-conditions/acceptable-use-policy) | Startseite HTTP 200; die aktuelle offizielle Richtlinie untersagt automatisierte Extraktion und Darstellung in anderen Apps. Kein Flugpreis extrahiert. |
| [Ryanair robots](https://www.ryanair.com/robots.txt) und [Nutzungsbedingungen](https://www.ryanair.com/ie/en/lp/legal/terms-of-use) | Startseite und robots HTTP 200; Such-/API-Pfade ausgeschlossen. Private nichtkommerzielle Nutzung in den Bedingungen ist keine Freigabe dieser gesperrten Abrufwege. |
| [Wizz Air robots](https://www.wizzair.com/robots.txt) und [Website Terms](https://wizzair.com/cms/api/docs/default-source/downloadable-documents/website_terms_and_conditions_en_d150c153-9446-4acf-b707-5bd246326d18.pdf) | Startseite/robots HTTP 200; Buchungspfade ausgeschlossen. Offizielle Bedingungen verlangen vor automatisierter Extraktion schriftliche Zustimmung. |
| [Eurowings robots](https://www.eurowings.com/robots.txt) | HTTP 200; Flug-Suchpfade ausdrücklich ausgeschlossen. |
| [LOT robots](https://www.lot.com/robots.txt) | HTTP 200; API-, Preiskalender- und Suchpfade ausgeschlossen. |
| [Amadeus FAQ / Kosten](https://admin.developers.amadeus.com/self-service/apis-docs/guides/developer-guides/faq/) | Offizielle aktuelle Dokumentation: Produktion berechnet Überschreitungen automatisch, ohne Verbrauchsobergrenze. Testumgebung ist kein aktueller Produktionspreisbeleg. Unter striktem Null-Euro-Auftrag nicht integriert. |
| [Aviasales Search API Zugang](https://support.travelpayouts.com/hc/en-us/articles/210995808-How-to-get-access-to-the-Aviasales-Search-API), [Data API](https://support.travelpayouts.com/hc/en-us/articles/203956083-Requirements-for-Aviasales-data-API-access) | Aktuelle Such-API verlangt 50.000 aktive Nutzer pro Monat; der private Desktop erfüllt das nicht. Die frei registrierbare Data API enthält historische Suchpreise aus 2–7 Tagen und bestätigt keine aktuelle Gruppenverfügbarkeit. |

Es gibt derzeit keinen zusätzlich einzurichtenden kostenlosen Schlüssel, der die verbleibende Flugblockade nachweislich löst. Benötigt würde ein zulässiger produktiver Anbieterzugang mit verbindlich kostenfreier Nutzung und echten gruppenbezogenen Angeboten; hierfür wurde kein Konto oder Vertrag abgeschlossen. `FlightAccessDiagnostics` ist ausschließlich eine sichtbare Zugangsdiagnose, kein als fertig gemeldeter Flugpreisprovider.

## Reproduzierbare Prüfung

```bash
.venv/bin/python -m unittest discover -q
.venv/bin/python scripts/live_offers.py --live --output tmp/live-offers
# Optional nur eine Kategorie bzw. einen Buchungshorizont prüfen:
.venv/bin/python scripts/live_offers.py --live --case rail-group-five --case rail-july-horizon
```

Liveprüfungen benutzen den normalen Discovery-Produktionspfad und frische lokale Datenbanken. Keine Schlüssel, Cookies oder persönlichen Daten in Fixtures oder Protokollen. Testtermine sind in diesem Prüfskript ausdrücklich benannte technische Fälle; die Anwendung selbst verändert Nutzerdaten nicht. Die bereinigten echten Preisantworten unter `tests/fixtures/offers` dienen reproduzierbaren Parserregressionen. Zusätzliche synthetische Vertragstests prüfen unter anderem Flug-Roundtrip-Doppelzählung, behaupten aber keinen erfolgreichen Flug-Liveabruf.
