# Unterkunftsquellen – Schritt 1: Machbarkeit und Auswahl

Abschluss: **10.11.2026**. Liveabrufe: **09.11.2026**, individuelle UTC-Zeiten im [JSON-Nachweis](UNTERKUNFTSQUELLEN_SCHRITT1_2026-11-10.json). Ausgangscode `95d1b35`, Arbeitsverzeichnis zu Beginn sauber.

## Ergebnis und Entscheidung

**Ein kostenloser, schlüsselloser Mehrzimmer-Preisabruf ist konkret nachgewiesen.** Die öffentliche Beds24-Gaststrecke des Hotels Palatino lieferte für fünf Erwachsene in drei ausgewählten Zimmern mit Belegung **2 + 2 + 1** einen gemeinsamen angezeigten Unterkunftspreis. Registrierung, Zahlungsdaten und KI waren dafür nicht nötig.

**Auswahl für Schritt 2:** zuerst den nachgewiesenen klassischen Beds24-Ablauf für Hotel Palatino als produktiven Pilot integrieren. Die responsive Variante anschließend anhand der ebenfalls abgefragten Quellen in Laa und Heidelberg ergänzen, sobald Preisbasis und komplette Auswahl unabhängig abgesichert sind. Das ist noch keine allgemeine Hotelmarktabdeckung.

Schritt 1 enthält Quellenprüfung, einen opt-in Prüf-CLI und Dokumentation. Keine neuen produktiven Provider, HTTP-Freigaben, GUI-Funktionen oder automatisch übernommenen Reisebeträge. Gespeicherte Reisen und lokale KI-Infrastruktur wurden nicht geöffnet oder verändert. Kein Commit, kein Push.

## Echte Preisbelege

| Quelle / Anfrage | Tatsächliche Antwort | Bewertung |
|---|---|---|
| Hotel Palatino, Sundern; 23.–25.11.2026, zwei Erwachsene | Standardzimmer: 168 EUR für den ausgewählten Aufenthalt; Preiszelle mit zwei Gästen | Einzeltarifhinweis, noch kein Nachweis aller Pflichtkosten |
| Palatino; 23.–25.11.2026, fünf Erwachsene, drei Zimmer | Zwei Standardzimmer zusammen 336 EUR und ein Economy-Zimmer 100 EUR; Gesamt **436 EUR** | Gemeinsame Auswahl mit passenden Daten, Stückzahlen und Belegung 2 + 2 + 1 bestätigt |
| Palatino; 05.–11.07.2027, fünf Erwachsene, drei Zimmer, sechs Nächte | Zwei Standardzimmer zusammen 1.008 EUR und ein Economy-Zimmer 420 EUR; Gesamt **1.428 EUR** | Zweiter echter Zeitraum mit derselben kontrollierten Belegung |
| Frühstückshaus Wunderland, Laa/Thaya; 23.–25.11.2026, zwei Erwachsene | Zimmer 163892, Tarif 1: 208 EUR; Tageswerte 104 + 104 EUR, Datum/Personen passen | Einzeltarifnachweis, kein vollständiger Gruppenpreis |
| Wunderland; zusätzlich drei Einheiten desselben Typs angefordert | 624 EUR; Antwortfeld `roomnum` bleibt 1 | **Nicht als Gruppenangebot angenommen.** Betrag beweist weder drei verfügbare Zimmer noch Belegung 2 + 2 + 1 |
| Hotel am Schloss, Heidelberg; Einzelzimmer 300523 mit zwei Erwachsenen | Belegungswarnung und Betrag 0 | **Verworfen.** Zimmerbeschreibung erlaubt eine Person; kein Gratisangebot |
| Hotel am Schloss; Comfort-Doppelzimmer 300521, zwei Erwachsene, 23.–25.11.2026 | `roomprice` 125, Anzeige ausdrücklich pro Nacht, beide Tageswerte jeweils 125 EUR | **125 EUR nicht als Aufenthaltstotal angenommen.** Rechnerische Tagessumme 250 EUR ist noch keine vollständige Auswahlquote |

Die Palatino-Auswahl besteht aus **zwei Standardzimmern mit eigenem Bad und einem Economy-Zimmer mit Gemeinschaftsbad**. Sie erfüllt keine Pflichtanforderung „jedes Zimmer mit eigenem Bad“. Frühstück ist optional und nicht ausgewählt. Weitere Pflichtkosten sind nicht unabhängig vollständig bestätigt; `subtotaltax=0` beweist keine generelle Gebührenfreiheit. Die Preise sind Quellenaussagen beim Abruf, keine Reservierungen oder Preisgarantien und kein vollständiger Reisepreis.

### Nachweisverfahren für die Gruppenpreise

1. Die [offizielle Hotelwebsite](https://hotelpalatino.de/) verlinkt Beds24 mit Objektkennung **6949**. Name, Anschrift und Telefonnummer passen zur Auswahlseite. Keine geratenen Objektkennungen.
2. Dokumentierte Parameter öffnen die Suche mit Datum, Nächten, Erwachsenen und Mehrzimmermodus. Die initiale Antwort enthält **Zimmerpreise**, keinen Gesamtpreis für fünf Personen.
3. Die tatsächliche GET-Auswahlform bietet bis zu acht Standardzimmer und zwei Economy-Zimmer an. Ihre vorhandenen Felder werden auf zwei Standardzimmer mit je zwei Erwachsenen und ein Economy-Zimmer mit einem Erwachsenen gesetzt.
4. Die folgende Preis-/Gästeformularseite bestätigt Menge, Belegung, Daten und Gesamtbetrag. **Keine Gästedaten ausgefüllt und keine Reservierung abgeschickt.** Das abschließende Buchungsformular wird nicht übertragen.
5. Die Auswertung kontrolliert Stückzahlen gegen die initialen Auswahlmöglichkeiten, berechnet fünf Erwachsene aus den bestätigten Mengen und prüft die Summen. Beide Termine bleiben getrennt.

Ein universeller KI-Browser war dafür nicht erforderlich. Der Ablauf ist technisch automatisierbar; der Produktadapter folgt erst in Schritt 2.

## Quellen, URL-Findung und Reichweite

| Kandidat | Nachgewiesener Zugang | Entscheidung |
|---|---|---|
| Beds24, klassisches Formular | Palatino-Website → Gastseite `propid=6949` → gelieferte Auswahlform | **Pilot gewählt:** eine Unterkunft, zwei Termine, eine konkrete gemischte Zimmerauswahl |
| Beds24, responsive Seite | [Gast in Laa](https://www.gastinlaa.at/buchen/) → Widget `ownerid=40690` → verlinktes Objekt 70716 → beschriebene Zimmer | Einzeltarif funktioniert. Betreiber verweist für mehrere Zimmer außerdem auf persönliche Nachfrage. Kein automatischer passender Drei-Zimmerpreis abgenommen |
| Beds24, responsive Seite | [Hotel am Schloss](https://www.hotels-in-heidelberg.de/hotel-am-schloss-hotels-in-heidelberg/) → eingebettete Objektkennung 134588 → beschriebene Zimmer | Einzeltarif und Belegungsfehler erreichbar. Andere Preisbasis; noch keine fertige Aufenthalt-/Mehrzimmernormalisierung |
| Bestehendes Smoobu, Innsbruck | Bereits integrierte offizielle Betreiberverknüpfung | Robots-Antwort erneut HTTP 200 mit HTML-Fehlerseite. Bestehender Client blockiert Folgeabruf. Zurückgestellt |

Responsive Seiten enthalten im ausgelieferten JavaScript den lesenden GET-Aufruf `api/ajax/getroomprice.php` und seine Parameter. Nur diese beobachtete Einzelabfrage wurde gezielt geprüft. Das ist **keine zugesicherte öffentliche Markt-API**. Zunächst wies der bestehende MIME-Vertrag die Antwort `text/plain` zurück. Ein enger Vertrag ausschließlich im Prüfskript erlaubt für genau diesen Pfad Text und parst danach JSON. Die Fehlschläge bleiben erhalten; die produktive HTTP-Schicht wurde nicht geändert.

Die Auswahl der Pilotobjekte nutzte externe Websuche. Daraus entsteht keine allgemeine Websuche in der Anwendung. Für die Integration werden vorhandene offizielle Unterkunfts-URLs beziehungsweise geprüfte Konfigurationen benötigt, deren explizite Beds24-Verknüpfungen erkannt werden. Keine ID-Aufzählung und keine Kennungen aus Modellwissen. Ein eigenes Beds24-Gastgeberkonto erschließt nicht das Inventar anderer Gastgeber.

## Kosten und Zugangsbedingungen

Die [Beds24-Dokumentation](https://wiki.beds24.com/index.php/Category:Developers) beschreibt Datums-, Nächte-, Gäste- und Mehrzimmerparameter. Mehrzimmerangebote hängen von der [Betreiberkonfiguration](https://wiki.beds24.com/index.php/Responsive_Booking_Page) ab. Die echten Gastabrufe benötigten kein Konto, keinen Schlüssel und keine Zahlungsdaten; das kostenpflichtige Gastgeberprodukt wurde nicht eingerichtet.

Die aktuelle [robots.txt](https://beds24.com/robots.txt) sperrt die geprüften Gastpfade für den Anwendungsagenten nicht und fordert fünf Sekunden Abstand. Das ist eine Abrufregel, **keine allgemeine Lizenz zur Weiterveröffentlichung fremder Hotelbestände**. Die [Beds24-SaaS-Bedingungen](https://www.beds24.com/en/company/eula-november) regeln Gastgeberkonten; daraus wurde keine pauschale Vergleichslizenz abgeleitet. Vorgeschlagen wird eine eng begrenzte lokale Quellenauswertung. Breiter Vertrieb oder Partnerschnittstellen benötigen eigene Klärung der dafür geltenden Bedingungen.

Bei Smoobu ist die Diagnose eine technisch nicht auswertbare Regelseite, **kein Nachweis einer Kontosperre**. Das bestehende Verhalten wird weder umgangen noch aufgeweicht. Eine zusätzliche Anmeldung wurde nicht als Lösung erfunden.

### Allgemeine APIs: Dokumentationsprüfung, kein Preis-Livetest

| API | Dokumentierte Zugangshürde | Entscheidung unter „kostenlos, keine Zahlungsdaten“ |
|---|---|---|
| [Booking.com Demand](https://developers.booking.com/demand/docs/getting-started/prerequisites) | Managed Affiliate Partner, Vertrag, Partnerbereich und Schlüssel | Kein allgemein frei registrierbarer Zugang nachgewiesen; nicht gewählt |
| [Expedia Rapid](https://developers.expediagroup.com/rapid/setup) | Partnerfreigabe; Entwicklungsschlüssel bis zur Prüfung eingeschränkt | Kein sofort nutzbarer kostenloser Produktionszugang nachgewiesen |
| [Hotelbeds](https://developer.hotelbeds.com/documentation/getting-started/) | Kostenloser Registrierungsschlüssel zunächst Evaluation, 50 Abfragen/Tag | Evaluation nicht als produktiver Preisbeleg verwendet; passender kostenfreier Produktionsvertrag ungeklärt |
| [LiteAPI / Nuitee Connect](https://docs.liteapi.travel/docs/getting-a-sandbox-key) | Einstieg ohne Karte für Sandbox; Anleitung verlangt Karte für Produktionsschlüssel | Nicht gewählt. [Preisregeln](https://docs.liteapi.travel/reference/api-pricing-usage-costs) enthalten Nutzungsvoraussetzungen für kostenlose Kernabläufe und kostenpflichtige weitere Endpunkte |

Keine Konten angelegt, Vertragsbedingungen angenommen oder kostenpflichtigen Abfragen ausgeführt. Ein Testschlüssel allein erfüllt die Anforderung produktiv nutzbarer Gruppenangebote nicht. Diese Auswahlprüfung beweist nicht, dass weltweit keine andere kostenlose API existiert.

## Begrenzter Prüfablauf

`scripts/probe_accommodation_access.py` ist ausschließlich ein opt-in Machbarkeitstest, kein produktiver Provider. Ohne `--live` keine Netzrecherche; die Anwendung importiert ihn nicht.

- Bestehende `SearchContext`, `TripStore`, `ResearchHttp` und `RobotsRules` weiterverwendet. Nur temporäre Datenbank; kein Zugriff auf gespeicherte Reisen.
- Separate enge Prüf-Allowlist: feste Betreiberseiten, drei identifizierte Objekte und beobachtete Gastpreisparameter. Produktive `OfferSourcePolicy` unverändert.
- Je Lauf maximal **32 HTTP-Transaktionen / 300 Sekunden / 2 MB je Antwort**, vorhandene DNS-/curl-Zeitlimits und begrenzte Weiterleitungen. Tatsächlich **24 protokollierte Transaktionen** in vier Läufen: 14 + 4 + 4 + 2.
- Öffentliche DNS-Adressen geprüft, Verbindung daran gebunden, HTTPS/TLS-Prüfung, keine Proxy-/curl-Konfigurationsübernahme. Weiterleitungen erneut an Allowlist geprüft.
- Mindestens 5,1 Sekunden Abstand zwischen Beds24-Abrufen; Betreiberseiten behalten ihre Robots-Abstände. Keine automatische Sperrumgehung.
- Nur GET, keine Login-, Zahlungs- oder Buchungsabschlussrouten. Der Auswahl-GET führt zum Preis-/Gästeformular; dessen abschließende POST-Felder sind ausgeschlossen.
- Keine Modellaufrufe, privaten Wunschtexte, Startadressen, Gästedaten oder Zahlungsdaten. Flüchtige Formularsitzungen werden aus Bericht-URLs entfernt.
- Im JSON begrenzte Preis-/Parameterbelege, Quell-URLs ohne Sitzung, UTC-Zeiten, HTTP-Status, MIME, Größe und SHA-256. Vollständige Voruntersuchungsseiten ausschließlich im ignorierten lokalen `tmp`, kein Reise-Snapshot oder Git-Artefakt.

Die manuelle Voruntersuchung umfasste separat 21 begrenzte Requests-Abrufe ohne vollständige Wire-Telemetrie. Ein früher Beds24-Seitenwechsel war noch nicht explizit auf fünf Sekunden gedrosselt. Die anschließenden reproduzierbaren Nachweise verwenden den zentral gedrosselten Prüftransport. Externe Websuch-/Dokumentationsabrufe sind ebenfalls keine Transaktionen des CLI-Budgets.

```bash
.venv/bin/python scripts/probe_accommodation_access.py --live
.venv/bin/python scripts/probe_accommodation_access.py --live --responsive-only \
  --output tmp/accommodation-responsive.json
.venv/bin/python scripts/probe_accommodation_access.py --live --responsive-only \
  --case heidelberg-double-two-adults --output tmp/heidelberg-double.json
```

Termine sind feste synthetische Prüfparameter, keine persönlichen Reisevorgaben. Vergangene Hauptfälle werden später übersprungen; erneute Ausführung bedeutet neue Abrufe mit möglicherweise anderen Preisen. Der abschließende responsive CLI unterstützt vier Fälle. Erste MIME-Kampagne und gezielte Wiederholung enthielten zunächst drei, der passende Doppelzimmerfall wurde separat geprüft. Keine Rohantwort auf erwartete Sachwerte geändert.

Gemessene Fallzeiten inklusive Drosselung: Palatino-Auswahl November 5,353 s, Juli 5,492 s; Laa-Einzeltarif 5,818 s; Heidelberg-Doppelzimmer 5,525 s. Die Kampagnen nutzten HTTP; Browser-Startzeiten und spätere GUI-Bedienbarkeit sind damit nicht gemessen.

## Verifikation und Anschluss an Schritt 2

Beide Gruppenquoten offline gegen bestätigte Formularfelder und Auswahlmöglichkeiten kontrolliert. Acht bestehende HTTP-/Angebotssicherheitstests bestanden; Prüfskript kompiliert und URL-/Buchungsabschlussgrenzen offline geprüft. Keine produktiven Codeänderungen. Die frühere 364-Test-Abnahme wurde nicht als erneut ausgeführt ausgegeben. Keine GUI-Abnahme, Login-/Browser-Fallbacks oder Modellprüfungen in diesem Quellenschritt.

Für Schritt 2 den klassischen Beds24-Pilot **innerhalb** von `OpenTravelProvider.research_offers → OfferResearchService` ergänzen. `OfferQuery` besitzt Zimmer/Belegung; `TravelOffer`, `OfferQuality`, Darstellung und Speicherung werden weiterverwendet. Produktions-Allowlist nur für tatsächlich benötigte Pfade/Parameter erweitern. Sitzungen ausschließlich in einer Prüfung führen, keine Abschlussroute, keine neue KI-Integration.

Jedes Gruppenangebot muss komplette Auswahl, Belegung, Verfügbarkeit, Preisbasis und Leistungen nachweisen. Gemeinschaftsbad darf keine entsprechende harte Pflicht erfüllen; unbekannte Gebühren bleiben unbekannt. Responsive Felder brauchen einen eigenen geprüften Vertrag: identische Feldnamen können Aufenthaltspreise, Nachtpreise oder bloße Multiplikationen enthalten.

Offen bleiben allgemeine Hotelabdeckung, freie Suche über alle Gastgeber, beliebige Zimmerverteilungen, vollständige Gebühren-/Stornonormalisierung und Flüge. Eine Anmeldung löst fehlende Mehrzimmerunterstützung oder ungeklärte Preisbasis nicht. Diese Ursachen müssen später getrennt angezeigt werden. Browser-/Nutzerübergaben bleiben der vereinbarten späteren Umsetzung vorbehalten.
