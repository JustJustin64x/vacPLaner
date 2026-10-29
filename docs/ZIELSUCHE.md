# Breite lokale Reisezielsuche – Stand 29.10.2026

## Einrichtung und normaler Betrieb

`main.py` startet die bestehende Oberfläche. Unter **Reise → Zieldaten einrichten / aktualisieren**:

1. Länder als Codes wählen und **Länder herunterladen / aktualisieren** starten. Es werden vollständige GeoNames-Länderdateien verwendet, keine `cities5000`-/`cities15000`-Auswahl. Der Startvorschlag AT/SI/HR ist editierbar; 46 europäische Länder/Gebiete sind unterstützt.
2. Regionale Freizeitmerkmale separat aktualisieren. Die kleine Overpass-Abfrage ist auf höchstens 1 × 1 Grad beschränkt. Alternativ stehen geprüfte PBF-Regionalauszüge für Tirol, Slowenien und Kroatien bereit; die Oberfläche nennt vor dem Start etwa 116–299 MB. Vorhandene lokale PBF-Dateien lassen sich ebenfalls für den gewählten Ausschnitt verwenden.
3. Abbrechen ist jederzeit möglich. Abgeschlossene Länder bleiben erhalten. Noch nicht abgeschlossene Datenbank-Transaktionen werden zurückgerollt. Es werden keine gespeicherten Reisen ersetzt.

Die Dateien liegen neben `trips.sqlite3`: `destinations.sqlite3` und `destination-downloads/`. Die separate Geodatenbank verwendet räumliche RTree-Indizes. Die normale GUI **und** `--search-json` verwenden diesen Bestand tatsächlich. Beim Start erfolgen keine Länder-/PBF-Downloads. Ohne Import bleibt der bisherige Reiseführerbestand verfügbar, ausdrücklich mit begrenzter Abdeckung.

Unter **Details**: Kandidatenumfang standardmäßig 35 (10–100), vier gewünschte Ergebnisse (bestehende gespeicherte Einstellungen bleiben erhalten), zwei kleine regionale Zusatzabfragen (0–3). Normale Suchen dürfen fehlende Merkmale mit diesen wenigen gebündelten Abfragen ergänzen; keine Landesdownloads, keine Einzelabfrage pro Ort. Fehlgeschlagene regionale Quellen erhalten sechs Stunden Pause; manuelles Aktualisieren bleibt möglich.

## Nachgewiesene Ursachen und Korrekturen

Der bisherige Katalog enthielt 298 Ziele in 29 Ländern, davon 84 in Deutschland. 146 Einträge teilten dieselbe grobe Baden/Natur-Bewertung, weitere 94 dasselbe Berge/Natur/Wandern-Muster. Ein einzelner thematischer Aktivitätseintrag konnte stark aufwerten. Die Sortierung war deterministisch, aber viele gleich bewertete Orte blieben dadurch dauerhaft ähnlich. Die vollständige bisherige Vielfaltsauswahl wuchs quadratisch mit der Kandidatenzahl. Der Ortscache speicherte unveränderte Quellen, keine interessensabhängigen Endergebnisse; ein fehlender Interessenanteil im bisherigen Ortscache-Schlüssel war deshalb kein nachgewiesener Fehler.

Jetzt werden alle geografisch passenden Aufenthaltsorte zuerst lokal bewertet. Erst anschließend begrenzen räumliche Vertreter und eine kleine Vielfaltsauswahl die vertiefte Recherche. Dicht kartierte Teilregionen können den Pool nicht allein füllen. Vielfalt wirkt zwischen ähnlich passenden Zielen; schwache Passung wird nicht vor noch vorhandene starke Passung geschoben. Nachweislich ausgeschlossene oder nicht ausreichend belegte Ziele lassen weitere Kandidaten nachrücken. Nahe Alternativen desselben Landes unter zwölf Kilometern belegen nicht mehrere Ergebnisplätze.

Stabile GeoNames-/OSM-/Wikidata-Kennungen, Namen, Aliasse, Koordinaten, Land, Verwaltungseinheiten, Objekttyp und Quellenstände werden gespeichert. Aktuelle Siedlungsklassen werden ohne Einwohner-Mindestgrenze importiert; historische/aufgegebene Orte und ungeeignete Objektklassen werden nicht als Aufenthaltsorte geführt. Seen, Bergregionen und Naturgebiete sind separate Regionsobjekte und werden mit nahen Aufenthaltsorten verbunden. Identitäten verschiedener Quellen werden nur mit expliziter Referenz oder zusätzlicher räumlicher und namensbezogener Übereinstimmung zusammengeführt. Gleiche Namen allein genügen nicht.

Merkmale: Wanderrelationen statt beliebiger Wege, Badeeinrichtungen/Strände statt beliebiger Gewässer, Museen/Sehenswürdigkeiten, Clubs, mehrere Bars/Kneipen und Natur-/Grünraumhinweise. Bewertungen sättigen; viele Einträge erzeugen keinen unbegrenzten Bonus. Ein einzelner Wanderweg, Club oder eine Bar bleibt ein schwacher Hinweis. Barhopping nutzt zwei Kilometer Luftlinie, Clubs/Kultur fünf Kilometer; Fußwege, Öffnung und Saison bleiben ungeprüft. „Ruhe“ ist ein begrenzter Grünraumindikator, keine Lärmmessung oder Ruhezusage. Schutz-/Wildruhezonen werden ohne belegten Besucherzugang nicht automatisch als Aktivitäten vorgeschlagen.

Fehlende Merkmale bleiben ausdrücklich unbekannt. Harte Länder-/Regions-/Unterkunfts-/Zeitvorgaben werden nicht automatisch gelockert. Unbelegte geografische Zuordnung von OSM-Unterkünften wird bei entsprechenden Vorgaben als offen geführt. Insbesondere beweist ein regionaler Dateiname oder rechteckiger Ausschnitt keine Länderzugehörigkeit einzelner grenznaher Objekte. Fehlende Länder-/Verwaltungsangaben in OSM können deshalb bei verbindlichen Gebietsfiltern zusätzliche Ergebnisse verhindern. Ohne Preis oder Fahrzeit entsteht kein Billigkeits- oder Schnelligkeitsbonus. Preisprovider, Speicherung, Nutzerwahlen und PDF-Vergleich bleiben erhalten. Booking-/Trivago-Zugänge und KI werden nicht vorausgesetzt.

## Quellen, Lizenzen und tatsächliche Integration

Vor der Implementierung geprüft: [GeoNames-Dumpformat und CC BY 4.0](https://download.geonames.org/export/dump/readme.txt), [Objektklassen](https://www.geonames.org/export/codes.html), [Overpass-Nutzungsregeln](https://dev.overpass-api.de/overpass-doc/en/preface/commons.html), [Private.coffee-Zugang und Bedingungen](https://overpass.private.coffee/), [Wikidata-Datenzugang](https://www.wikidata.org/wiki/Wikidata:Data_access), [Pyosmium-Filter](https://docs.osmcode.org/pyosmium/latest/user_manual/04-Working-with-Filters/).

GeoNames liefert den Grundbestand. OSM wird gebündelt pro Ausschnitt oder lokal aus PBF gelesen; keine massenhafte Nominatim-Ortsentdeckung. [OSM France, Tirol](https://download.openstreetmap.fr/extracts/europe/austria/) und [Geofabrik, Slowenien](https://download.geofabrik.de/europe/slovenia.html)/[Kroatien](https://download.geofabrik.de/europe/croatia.html) lieferten tatsächlich lesbare Dateien. Öffentliche Overpass-Proben scheiterten praktisch an Zeitlimits; der Statusabruf von overpass-api.de antwortete 406. **Kein erfolgreicher Live-Overpass-Abruf wird behauptet.** Der funktionierende Liveweg war der regionale PBF-Import.

Wikidata ergänzt höchstens 20 bereits bekannte Q-Identitäten je Aufruf; keine flächige SPARQL-Abhängigkeit. Beziehungen und vorhandene GeoNames-/Wikivoyage-Verweise werden gespeichert. Ein Ausfall verwirft weder GeoNames noch OSM. Identitäten werden sieben Tage gecacht; regionale Merkmale 30 Tage, heruntergeladene PBF-Dateien sieben Tage. Der abgeleitete lokale Suchindex enthält alle Merkmale und wird anhand der Datenrevision erneuert. Interessen werden bei jeder Suche neu ausgewertet.

Quellen/Lizenzen: GeoNames CC BY 4.0, OSM-Mitwirkende/ODbL, Wikidata CC0; Hinweise reisen mit den Snapshots in GUI und PDF. Es gibt keine Registrierung, Schlüssel, Cloud, Buchung oder KI-Abfrage.

## Echte Prüfung und Grenzen

Der [maschinenlesbare Prüfbericht](ZIELSUCHE_PRUEFUNG_2026-10-29.json) enthält Parameter, Quellenstände, Dateigrößen/Prüfsummen, Zähler, Belege, Einschränkungen und Laufzeiten.

| Grundbestand | Aufenthaltsorte | Separat geführte Regionsobjekte |
|---|---:|---:|
| Österreich | 20.029 | 7.025 |
| Slowenien | 6.567 | 387 |
| Kroatien | 11.360 | 1.868 |
| Summe | 37.956 | 9.280 |

Regionale OSM-Ausschnitte: Inntal/Innsbruck 4.441 Merkmale, Bled/Bohinj 2.319, Split/Trogir 2.613. Zusammen 9.373 eindeutige Objekte; 60 Wikidata-Identitäten wurden gezielt tatsächlich abgefragt. Der normale Anwendungsbestand enthält nach Zusammenführung und verbliebenen Reiseführerzielen 38.221 Aufenthaltsorte.

Die kontrollierten Vergleichsläufe halten Gebiet, Reisende, Zeitraum und Suchbudget gleich und ändern die Interessen. Sie laufen durch die normale Anwendungsinitialisierung und vorhandene Unterkunfts-/Transportrecherche. Konkrete Resultate und Zeiten stehen im JSON. Die Zahlen belegen geografische/inhaltliche Recherche, keine bestätigte Öffnung, Zimmerbelegung oder Budgeteinhaltung. Geprüfte Arbeitskopien wurden nur in einer separaten Testdatenbank gespeichert; vorhandene gespeicherte Reisen blieben unverändert.

Bei demselben gesamten lokalen Bestand, Berlin als Start und Juli 2027: Wandern/Ruhe unter anderem Scharnitz und Log; Kultur/Nachtleben unter anderem Rum und Reith bei Seefeld; Baden/Wandern Eng und Dovje; Barhopping Absam und Jesenice. Die vier abschließenden Läufe dauerten 18,1–22,7 Sekunden und nutzten je drei HTTP-Aufrufe. Der Start mit vorhandenem Index dauerte 0,47 Sekunden. Diese Beispiele sind historische technische Suchläufe, keine persönlichen Vorgaben oder garantierten Empfehlungen.

Nur drei Länder haben bisher den breiten Grundbestand; die anderen unterstützten Länder sind noch einzurichten. Freizeitmerkmale liegen nur für die drei genannten Ausschnitte vor. Außerhalb fehlen oft Belege; auch innerhalb ist Kartierung keine Vollständigkeitsgarantie. Wege-/Flächenentfernung verwendet repräsentative Punkte, keine bestätigten Einstiege oder Fußwege. Größere Datenaufbauten laufen separat; der erste lokale Indexaufbau dauerte etwa 42 Sekunden, danach nutzte die Anwendung den lokalen Index in unter einer Sekunde. Normale Suchläufe bleiben zeit-/abfragebegrenzt.

Reproduzierbar nach Einrichtung:

```bash
.venv/bin/python -m unittest discover -q
.venv/bin/python scripts/live_destination_discovery.py --live --output tmp/discovery-check
```

Die automatisierten Tests prüfen unter anderem unterschiedliche Interessen bei demselben Kandidatenbestand, schwache Einzelbelege, dichte Städte gegenüber anderen passenden Regionen, harte Anforderungen, geografische Identitäten, wiederholte und abgebrochene Importe, Cache-Aktualisierung, Quellenausfall, Nachrücken, echten GUI-Einrichtungsworker und Erhalt gespeicherter Reisen. Eine PDF aus echten Recherche-Snapshots wurde zusätzlich gerendert und visuell kontrolliert.

Abschluss: 152 Tests erfolgreich; `compileall` und `git diff --check` erfolgreich. Vorhandene Änderungen an `nextPrompt.md` bleiben unangetastet.
