# Lokaler Überraschungsreise-Planer

Native deutsche Desktop-Anwendung für **ein europäisches Reiseziel**, ohne Zielvorgabe und ohne laufende API-/Hosting-/KI-Kosten. Sie findet reale Ziele, liest reale Unterkunfts-/Aktivitätseinträge, berechnet Straßenrouten, vergleicht transparente Teilsummen und speichert Reisen lokal mit PDF-Export.

**Stand 28.10.2026 (Suchverbesserung und begrenzte Liveprüfung vom 28.10.):** Der durchgängige Rechercheablauf funktioniert. Ein vollständiger Live-Preisvergleich für Hotels, Bahn und Flüge ist **nicht umgesetzt**: Die geprüften Null-Euro-Zugänge liefern dafür keinen geeigneten nachgewiesenen Zugang. Eine Geodaten-/Reiseführeridentität ist kein verfügbares Angebot. Die Anwendung zeigt diese Lücken ausdrücklich, bestätigt bei unvollständigen Preisen kein Budget und erfindet keine Angebote.

## Start auf diesem Mac

Die aktuelle Laufzeit ist bereits unter `.venv` eingerichtet (Python 3.13 / Tk 9.1).

```bash
cd /Users/justinzimmermann/Documents/vacPLaner
./Urlaubsplaner.command
```

Alternativ:

```bash
.venv/bin/python main.py
```

Doppelklick auf `Urlaubsplaner.command` startet ebenfalls den Planer. `python3 main.py` nutzt automatisch die vorhandene Projektumgebung, wenn es mit dem System-Python aufgerufen wird.

Für eine neue Installation:

```bash
bash scripts/setup-macos.sh
```

Das Skript benötigt Homebrew und installiert `python-tk@3.13` sowie die Python-Abhängigkeiten aus PyPI. Es überschreibt keine vorhandene inkompatible virtuelle Umgebung. Alternativ ein aktuelles Python mit Tk von python.org verwenden, `.venv` erstellen und `pip install -r requirements.txt` ausführen. Laufzeit: Python **3.10+**, Tk **8.6+**, `curl`; auf diesem Mac tatsächlich geprüft: Python 3.13.18/Tk 9.1. Apples Python 3.9/Tk 8.5 erzeugte bei der visuellen Prüfung ein leeres Fenster und wird für die neue GUI bewusst abgewiesen. Ein anderer ttk-Stil allein behebt diesen Laufzeitfehler nicht.

**API-Schlüssel:** keine erforderlich oder unterstützt. openrouteservice, DB- und Booking-Schlüssel sind nicht notwendig; dafür existieren in dieser Version keine aktivierten Adapter.

## Verbesserte Zielsuche

298 quellenbasierte Ziele in 29 Ländern, davon 252 außerhalb der Kategorie Großstadt. Kleine Orte, Seen-/Küstengebiete und Bergregionen sind über konkrete Basisorte vertreten. Interessen sind Wünsche auf **0–5**; alle null erlaubt eine offene Suche. Der neue Gebiets-Auswahldialog unterstützt Regionssuche, Länderkennungen und Aliasse, etwa „Schwarzwald“, „Black Forest“, „Österreich“ und „AT“.

Die Suche zieht bei Lücken weitere Kandidaten nach, bis die gewünschte Trefferzahl oder das vorhandene Zeit-/Abfragebudget erreicht ist. Unter **Details**: Umgebungssuche (Unterkünfte 15 km, Aktivitäten 30 km Luftlinie, abschaltbar) und optionale Anzeige **„Ideen mit unbelegten Pflichtangaben“**. Diese Ideen stehen getrennt von Filtertreffern; kein Filter wird automatisch gelockert.

Bei null Treffern erklärt die **Suchdiagnose** die Ursachen, zählt jede Stufe und bietet einen lokalen Export ohne genaue Adresse. Unterkünfte, Quellorte, Abstände, Interessenbelege und verbleibende Angaben stehen in den Details und der PDF. [Diagnose, Abdeckung, Tests und ehrliche Abnahmegrenzen](docs/SUCHVERBESSERUNG.md).

## Benutzung

1. Reisezeitraum mit explizitem Jahr, Kalendertage, Erwachsene, Zimmer und Gruppenbudget eingeben. Kein Ziel nötig. Leere Länder-/Regionsfelder bedeuten die gesamte unterstützte Auswahl.
2. Interessen und Vergleichsgewichte anpassen. Nullgewichte werden sinnvoll behandelt. Auto, Zug und Flug einzeln aktivieren; Fahrzeugkapazität muss reichen. Ausstattung als Wunsch oder Pflicht wählen: unbekannte Pflichtausstattung wird nicht als erfüllt angenommen.
3. **Reiseziele entdecken** starten. Während der Recherche bleiben Fenster und Filter bedienbar. Phasen, bearbeitete Ziele, echte Abfragen, Laufzeit und Quellenprobleme werden angezeigt. Abbrechen bewahrt bereits angezeigte Ergebnisse.
4. Ziel auswählen; Unterkunft und Hin-/Rückreisemittel wechseln. Reisebasis, Bewertung und Hinweise aktualisieren sich. Beide Autofahrten bleiben gekoppelt.
5. **Reise speichern**, später im Reiter **Gespeicherte Reisen** öffnen, ändern, duplizieren oder löschen. Neue Filter werden bei einer neuen Suche verwendet; sie schreiben eine bestehende konkrete Reise nicht stillschweigend um.
6. **PDF exportieren** öffnet den lokalen Speichern-Dialog. Der Export ist ein eigener, redaktionell aufbereiteter Reiseführer mit Übersicht, Kosten, Anreise, Karte, bis zu drei Unterkünften, bis zu acht Aktivitäten und Quellen.
7. Im Reiter **Gespeicherte Reisen** lassen sich mehrere Reisen einer Exportliste hinzufügen, sortieren und gemeinsam mit Inhaltsverzeichnis und Vergleich exportieren. Unvollständige Angaben werden vorab geprüft. **Angaben & Bilder recherchieren** ergänzt die geöffnete Arbeitskopie gezielt und abbrechbar; gespeichert wird erst auf ausdrückliche Aktion. Details: [Reiseführer-PDF und Anreicherung](docs/PDF_EXPORT.md).

Links zu Anbietern öffnen sich nur auf Klick im Browser. Für die Recherche und Verwaltung ist kein separat zu bedienender Browser nötig. „Mehrere Ziele“ ist sichtbar, aber deaktiviert.

## Was die Zahlen bedeuten

- Sieben **Kalendertage** sind sechs **Übernachtungen**. Alle vorgeschlagenen Datumsoptionen passen in den Zeitraum. Drei Datumsstichproben bedeuten keine Suche nach dem global günstigsten Termin.
- Die Reisebasis umfasst Hin-/Rückreise, relevante Nebenkosten und Unterkunft für die ganze Gruppe. Verpflegung und Aktivitäten stehen separat und werden nicht im Gruppenbudget verrechnet.
- Benzin wird aus echten Hin-/Rückstraßenkilometern × Verbrauch × EUR/Liter × Fahrzeuganzahl berechnet. Die sichtbare Verbrauchsspanne beträgt −10/+20 %. Verbrauch und Benzinpreis sind editierbare Nutzereingaben, keine aktuellen Marktpreise.
- Maut/Vignetten, Parken, mögliche Fähren, Hotelpreis und Pflichtgebühren bleiben ohne Beleg **unbekannt**. Die sichtbare **Teilsumme** ist kein vollständiger Reisepreis. Alle Geldberechnungen verwenden `Decimal` und Cent-Rundung.
- Autozeiten sind Routingmodell plus ausgewiesene Pausen-/Zugangsannahmen und Zeitreserve. Keine Live-Verkehrsprognose. Die genaue Startadresse bleibt lokal; gerechnet wird ab Ortszentrum. Hotelzufahrt fehlt. Bei über 16 Stunden oberer Schätzung wird Auto wegen möglicher Zwischenübernachtung aus der Ein-Ziel-Auswahl genommen. Hin- und Rückreise per Zug/Flug sind derzeit ausschließlich unbestätigte Rechercheoptionen mit Links.
- „Belegung [2, 2, 1]“ ist bei fünf Erwachsenen/drei Zimmern die gewünschte Zimmerverteilung, **kein Nachweis**, dass eine genannte Unterkunft diese Zimmer frei hat. Auch Campingausrüstung, Stellplätze und Belegung werden nicht vorausgesetzt.
- Fehlende Preise/Zeitdaten erhalten im Ranking keinen Billigkeits-/Schnelligkeitsbonus. Gewichte werden normalisiert; alles null ergibt vier gleiche Gewichte. Interessen sind redaktionelle grobe Themenkennzeichen, Komfort eine ausdrücklich benannte Annahme. Keine Klimavorhersage oder KI.

## Geografische Abdeckung und Abfragegrenzen

298 quellenbasierte Kandidaten in 29 Ländern: Deutschland, Tschechien, Österreich, Slowenien, Kroatien, Ungarn, Polen, Slowakei, Niederlande, Belgien, Frankreich, Spanien, Portugal, Italien, Schweiz, Dänemark, Schweden, Norwegen, Finnland, Estland, Lettland, Litauen, Vereinigtes Königreich, Irland, Griechenland, Rumänien, Bulgarien, Bosnien und Herzegowina, Montenegro.

Das ist eine begrenzte Europaauswahl, keine vollständige Länder-/Regionsabdeckung. Alle Ortsseiten und Quellkoordinaten wurden live überprüft. Einzelne Reiseführer haben wenige oder keine maschinenlesbaren Unterkünfte. Nachgewiesene direkte Unterseiten oder nächste erlaubte Katalogorte werden bei Datenlücken begrenzt einbezogen; kein rekursives Crawling. Die vollständige Liste steht in [destinations.json](src/vacation_planner/infrastructure/planning/data/destinations.json) und in der Oberfläche unter „Unterstützte Länder und Regionen“.

Standard: sechs Filtertreffer, 24 HTTP-Aufrufe und fünf Minuten. Die ganze geografisch passende lokale Datenbasis wird vorbewertet; weitere Kandidaten werden adaptiv nachgezogen. Obergrenzen: zwölf gewünschte Treffer, 40 Aufrufe und zehn Minuten. Drei Datumsstichproben sind keine Terminoptimierung; der ausgewählte Termin hängt nicht von der Listenposition ab. Weiche Diversitätsabschläge berücksichtigen Land, Region, Typ und Nähe; Natur-/Badeinteressen bevorzugen passende kleinere Landschaftsziele. Entfernung dient nur als Vorauswahlhinweis, nie als behauptete Straßenroute. Ein Worker, mindestens 1,1 s je Host, 22 s pro Abruf, keine Sperrumgehung/automatischen Wiederholungen. Ortsdaten werden sieben Tage, Geocoding 30 Tage gecacht. Maximal zwei zusätzliche Orts-/Unterseiten pro Ziel, innerhalb der erlaubten Radien und Kataloggebiete. Die Gebietszuordnung ist kein exaktes Polygon-Geofencing.

[Quellenprüfung mit Zugang, Lizenz, Limits und tatsächlichen Integrationstests](docs/DATENQUELLEN.md) · [Datenlizenzen](docs/DATENLIZENZEN.md) · [Katalogprüfprotokoll](docs/KATALOGPRUEFUNG.json).

## Speicherung und Konfiguration

Standarddatenbank:

```text
~/Library/Application Support/Urlaubsplaner/trips.sqlite3
```

Versioniertes SQLite-Schema (`user_version=1`), versionierte JSON-Reise-Snapshots, getrennte Cache-Tabelle, kurze Verbindungen mit expliziter Freigabe. Gespeichert werden Suchkriterien, konkrete Daten, Auswahl, Alternativen, Kostenstatus und ursprüngliche Quellenzeitpunkte. Keine Cloud-Synchronisation. Keine Schlüssel in Datenbank, PDF, Logs oder Git.

Optionale Umgebungsvariablen:

| Variable | Zweck |
|---|---|
| `VACATION_PLANNER_DB` | Eigener lokaler Datenbankpfad, etwa für Tests |
| `VACATION_ROUTING_URL` | Austauschbarer kompatibler kostenloser OSRM-Endpunkt; Standard FOSSGIS |
| `VACATION_GEOCODING_URL` | Austauschbarer kompatibler kostenloser Nominatim-Endpunkt |

Keine beliebigen kostenpflichtigen Dienste konfigurieren. Die öffentliche Nominatim-Instanz wird bewusst nur für einzelne benutzerausgelöste Startortsuchen genutzt: keine Adressenübertragung, kein Autocomplete oder Bulk, identifizierender User-Agent, Cache und max. eine Abfrage/Sekunde. [Verbindliche Nutzungsregeln](https://operations.osmfoundation.org/policies/nominatim/).

## Tests und reproduzierbare Abnahme

```bash
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m unittest discover -s tests -p 'test_*.py'
```

99 Tests prüfen Suche, Kosten, Gruppen/Fahrzeuge, Preisstatus, Tage/Nächte, Parser/Deduplizierung, Abbruch, SQLite, Desktop-Callbacks sowie Einzel-/Mehrfach-PDF, Reihenfolge, alte Snapshots, Kosten pro Person, Kartenpunkte, Offlinebilder und unveränderte Originaldaten. Livezugriffe sind **nicht** Bestandteil der deterministischen Tests. GUI-Tests benötigen modernes Tk und eine Desktop-Sitzung.

Separater echter Quellen-/Suchtest:

```bash
PYTHONPATH=. .venv/bin/python scripts/live_search_improvement.py --budget 24
```

Ergebnisse unter `tmp/search-improvement/live/<Zeitpunkt>/report.json`, öffentlicher Prüfbericht standardmäßig `docs/SUCHLAUF_2026-10-28.json`; keine periodische Überwachung. Dieser Befehl startet bewusst einen neuen Netzlauf, die Testsuite nicht. Die Beispielwerte stehen in [docs/beispielsuche.json](docs/beispielsuche.json): Berlin, Europa, fünf Erwachsene, drei Zimmer, 2.000 EUR, Wandern/Baden/Feiern, **Juli 2027**, sieben Kalendertage/sechs Nächte, Auto/Zug/Flug. Das Skript wählt bei späterer Ausführung den nächsten zukünftigen Juli. Die Standardoberfläche speichert diese Testwerte nicht als persönliche Vorgaben.

Echte JSON-Suche ohne GUI:

```bash
.venv/bin/python main.py --search-json docs/beispielsuche.json > ergebnisse.json
```

Fortschritt auf stderr, Ergebnis auf stdout. [Aktuelle Suchabnahme](docs/SUCHVERBESSERUNG.md) dokumentiert Diagnose, begrenzte echte Läufe und visuelle Prüfung. [Frühere Abnahme](docs/ABNAHME.md) hält den historischen Stand vor der Suchverbesserung fest.

## Architektur und früherer Democode

Der neue Produktionspfad liegt in `core/planning` (Modelle, Providervertrag, Suche, Kosten, Ranking), `infrastructure/planning` (HTTP, Katalog, quellspezifischer Parser, Routing, SQLite, PDF) und `entrypoints/gui/SurprisePlannerApplication.py` (Tkinter). Der Core importiert nur Standardbibliothek und vorhandene Domänenlogik, keine GUI oder externen Bibliotheken. Die bestehende Haversine-Domänenlogik wird weiterverwendet. Geld und Kalenderdaten werden ausdrücklich behandelt.

Die früheren Adapter erzeugen simulierte Flug-/Bahn-/Hotelangebote. Sie bleiben für historische Tests erhalten und sind über den normalen Start nicht erreichbar. Zum expliziten Demobetrieb:

```bash
.venv/bin/python main.py --demo
.venv/bin/python main.py --demo --cli
.venv/bin/python main.py --demo --serve
```

`--cli` und `--serve` ohne `--demo` werden abgewiesen. Im Demofenster steht ein deutlicher Titelhinweis. Die alten API-Tests belegen weiterhin ausschließlich den Demopfad, keinen Livezugang.

## Verbleibende Grenzen

Keine bestätigten Hotel-/Flug-/Bahnpreise oder Verfügbarkeiten, keine europäischen datierten Bahnverbindungen, keine bestätigte Zimmerbelegung, keine zuverlässigen datierten Veranstaltungen. Ausstattung bleibt bei der derzeitigen Quelle überwiegend unbekannt; harte Ausstattungsfilter können deshalb keine Ergebnisse liefern. Guide-Einträge können veraltet sein. Ein vollständig buchbares Gesamtpaket und ein belegter Preis-Sieger sind damit **nicht** abgenommen. Keine Kinder, Rundreise, Buchung/Zahlung, Wetterprognose oder Währungsumrechnung ohne belegte Fremdwährungsangebote.
