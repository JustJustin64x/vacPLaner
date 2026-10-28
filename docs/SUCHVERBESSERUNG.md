# Suchverbesserung – Diagnose, Umsetzung und Prüfung vom 28.10.2026

## Verifizierte Ausgangslage

Vor den Änderungen war nur `CODEX_PROMPT_SUCHE_VERBESSERN.md` untracked. Die später hinzugekommene `nextPrompt.md` bleibt unverändert. Kein Commit oder Push im Rahmen dieses Auftrags.

Die kontrollierte Wiederholung mit dem alten FixtureProvider ergab: Wandern 6 Ergebnisse, Wandern/Baden/Feiern 6, Pool als Pflicht 0, nur Zug mit maximal 8 Stunden 0, Schwarzwald 0. Der alte Provider liefert Bled-Einträge für beliebige Orte und eignet sich **nicht** als geografischer Erfolgsnachweis. Die genaue ursprüngliche Nutzerkonfiguration ist nicht bekannt. Ein allgemeiner Fehler „Interessen allein schließen alle Ziele aus“ wurde nicht reproduziert.

Nachgewiesene Ursachen und Schwächen:

- Exakte Regionszeichenketten ohne Aliasauflösung entfernten unbekannte Regionen stillschweigend.
- Unbelegte Pflichtausstattung und fehlende Bahn-/Flugdauer wurden ohne getrennte offene Ideen verworfen.
- Nur `shortlist + 3` Kandidaten wurden untersucht; spätere geeignete Orte blieben unerreichbar.
- `InterruptedError` wurde durch breite `OSError`-Handler als Quellenfehler verschluckt.
- GUI-Fehler zeigten nur den Exception-Typ. Nach wiederholtem Laden partieller Interessendictionaries konnten frühere Interessen im Formular stehen bleiben; auch dies ist behoben und separat getestet.
- Termine hingen von der Listenposition ab. Die frühere Interessenskala erlaubte im Modell 100 trotz GUI-Hinweis 5.

## Neuer Ablauf

Gebiete validieren → Startort auflösen → alle geografisch passenden lokalen Kandidaten bewerten → vielfältige Warteschlange → pro Ziel begrenzte Orts-/Umgebungsrecherche → Unterkunftskriterien prüfen → sinnvolle Anreiseabfragen → Filtertreffer oder separat aktivierbare offene Ideen.

Interessen sind Wünsche auf 0–5, standardmäßig nicht ausgewählt. Alle null ist gültig. Preis/Reisezeit/Komfort/Interessen behalten Vergleichsgewichte 0–100. Redaktionelle Eignung (abgestufte Stärken), belegte Aktivitäten am Ort und belegte Einträge im Umfeld werden getrennt erklärt. Die angezeigte Datensicherheit ist ein grober Evidenzindikator, keine statistische Wahrscheinlichkeit oder Garantie aktueller Öffnung. Einzelne Bars belegen kein ausgeprägtes Nachtleben; Seen allein keine Badeerlaubnis; Gipfel allein keinen Wanderweg. „Kostenlos“ wird nur einem ausdrücklich so beschriebenen Eintrag zugeordnet.

Die Vorauswahl nutzt Interessen und Entfernung als Hinweis. Natur-/Badeinteressen geben passenden kleineren Landschaftszielen einen erklärten Präferenzzuschlag. Weiche Abschläge für bereits vertretene Länder, Zieltypen, Regionen und Orte unter 45 km Abstand schaffen Vielfalt. Es gibt keine starre Länderrotation und keinen Bonus allein für die Anzahl von POIs. Konkrete Aktivitätshinweise können die Interesseneignung gegenüber der redaktionellen Vorbewertung erhöhen; zwanzig gleichartige POIs erhalten keinen größeren Bonus als ein passender Hinweis. Die endgültige Vergleichsbewertung bleibt an die Nutzergewichte gebunden; fehlende Preise sind weiterhin kein Billigkeitsvorteil.

Gewünschte Filtertreffer (3–12), lokal bewertete Kandidaten und tatsächliche HTTP-Abfragen sind getrennte Größen. Standard: sechs Treffer, 24 HTTP-Aufrufe, 300 Sekunden; weiterhin maximal 40 Aufrufe und 600 Sekunden. Bei Lücken wird der restliche Katalog adaptiv durchlaufen. Cache-Hits verbrauchen keine HTTP-Abfragen. Kontrollabbrüche werden bis zum GUI-/CLI-Einstieg weitergereicht; bereits emittierte Ergebnisse bleiben erhalten. Unbelegte oder nachweislich verletzte Unterkunftspflichten lösen keine zusätzliche Routingabfrage aus.

Der früheste zulässige Termin wird stabil gewählt, unabhängig von der Position des Ziels. Bis zu drei plausible Datumsstichproben werden zusätzlich gezeigt. Statische Ortsseiten werden nicht je Datum erneut geladen. Keine Preis-/Terminoptimierung wird behauptet.

## Katalog und räumliche Grenzen

**298 eindeutige Kandidaten, 29 Länder; 252 außerhalb der Kategorie Großstadt (84,6 %).** Die Einordnung ist eine redaktionelle Orts-/Landschaftstypisierung, kein amtlicher Bevölkerungszensus. „Großstadt“ dient hier als grobe Kategorie größerer urbaner Reiseziele; kleinere Städte/Ferienorte sind gesondert auswählbar.

321 zusätzliche Ortsnamen wurden in neun gebündelten Wikivoyage-API-Abfragen geprüft: 240 eindeutig aufgelöste Seiten mit Primärkoordinaten, 81 nicht aufgenommene Namen. Sieben angenommene Orte waren bereits im Ausgangskatalog; netto kamen 233 hinzu. Fehlende, mehrdeutige oder nicht koordinierte Seiten wurden nicht durch erfundene Koordinaten ersetzt. Dokumentation: [Rohprüfbericht](KATALOGERWEITERUNG_2026-10-28.json), Seeds in `scripts/catalog_seeds.tsv`, explizite Korrekturen in `scripts/catalog_overrides.json`, Wartung über `scripts/expand_catalog.py`. Keine flächendeckenden Nominatim-Abfragen.

Stabile IDs, Quellen, Prüfzeiten, Koordinatenherkunft, Typen, Landschaften, mehrere Regionszugehörigkeiten und Basisorte sind im Katalog enthalten. Beispiele: Schwarzwald, Harz, Mecklenburgische Seenplatte, Sächsische/Böhmische Schweiz, Salzkammergut, Dolomiten und Julische Alpen. Bohinj ist als Region mit Basis Bohinjska Bistrica modelliert. Bei autofreien Berggebieten ist die Talkoordinate keine zugesagte Autozufahrt bis zur Unterkunft.

Normalisierung unterstützt Groß-/Kleinschreibung, Umlaute/Umschreibung, Länderkennung und benannte Aliasse wie Black Forest → Schwarzwald sowie Austria → Österreich. Der Gebiets-Auswahldialog durchsucht unterstützte Werte. Unbekannte Namen werden mit Vorschlägen gemeldet, niemals still in Europa umgedeutet. Es gibt keine Vollständigkeitszusage für alle Orts- und Regionsaliase.

Umgebungssuche: standardmäßig 15 km für Unterkünfte, 30 km für Aktivitäten, jeweils höchstens 50 km Luftlinie. Sie ist abschaltbar; dann wird nur die Basisortseite mit maximal 2 km für koordinierte Einträge berücksichtigt. Ohne Koordinaten bleiben lokale Einträge als Lage unbekannt sichtbar, sofern keine harten Gebietsfilter gesetzt sind. Zusätzliche Seiten benötigen koordinierte Einträge. Es werden höchstens zwei Zusatzseiten verwendet: nachgewiesene direkte Unterseiten des Basisartikels oder nächste erlaubte Katalogorte; kein rekursives Crawling. Ein großer regionaler Artikel wird nicht automatisch vollständig durchsucht.

Länder-/Regionsfilter und Ausschlüsse gelten auch für Zusatzseiten; bei POIs wird die nächste bekannte Katalogzuordnung zusätzlich überprüft. **Grenze:** Das ist eine quellen- und koordinatenbasierte Zuordnung, kein amtliches Polygon-Geofencing. Grenzverläufe innerhalb kleiner Gemeinden und nicht im Katalog repräsentierte Enklaven sind damit nicht exakt nachweisbar. Die Zuordnung und Luftlinienentfernung ersetzen keine Prüfung realer Erreichbarkeit über Berge, Wasser oder Fähren. Diese Einschränkung wird nicht als bestätigte kurze Anbindung ausgegeben.

## Diagnose und Datenschutz

Jede Suche erhält eine Such-ID und folgende klar getrennte Zähler:

- `catalog`: gesamte Datenbasis.
- `geographic`: nach Ländern, Regionen und Ausschlüssen verbleibend, vor Zieltyp-/Startortfilter.
- `locally_scored`: tatsächlich lokal bewertete Ziele nach allen lokalen Filtern und Entfernung vom Startort.
- `examined`: begonnene Tiefenrecherchen; schließt Cache-Recherche und die bei Abbruch angefangene Recherche ein.
- `online_examined`: davon Ziele, während deren Recherche tatsächlich HTTP-Aufrufe verbraucht wurden; ein technischer Verbindungsversuch zählt ebenfalls.
- `with_lodgings`, `with_activities`, `with_known_transport`: überlappende Merkmalszähler, keine Partition. Die Unterkunftszahl meint mindestens eine mit belegten Pflichtkriterien passende Identität; sie beweist keine Zimmerverfügbarkeit.
- `matches` und `ideas`: produzierte Filtertreffer beziehungsweise unvollständige Ideen, auch wenn die Ideenanzeige ausgeschaltet ist.

Jedes begonnene Ziel hat genau einen Endstatus; die Zusammenfassung zählt genau einen Hauptgrund je Ziel. Zusätzliche Gründe stehen beim Ziel. Globaler Stopgrund: gewünschte Anzahl, Katalog erschöpft, Zeit, Budget, Abbruch oder Fehler. Null Treffer bleiben erklärbar, auch bei ungültigem Gebiet oder Quellenproblemen.

Der Reiter **Suchdiagnose** bietet einen JSON-Export. Die genaue Startadresse wird aus Kriterien entfernt und in Fehlertexten redigiert; Stacktraces enthalten keine lokalen Variablen. Fertige Berichte werden lokal im Verzeichnis `diagnostics` neben der SQLite-Datenbank gespeichert, auch nach Abbruch. Kein externer Versand. Die automatische Diagnose enthält Startort, Reisezeitraum und übrige Kriterien; vor freiwilliger Weitergabe prüfen. Der gewöhnliche Ergebnisbereich enthält verständliche Hinweise statt Tracebacks.

## Tatsächliche Tests und echte Abfragen

**93 Tests bestanden:** die bisherigen 72 plus 21 neue. Bestehende Tests wurden nicht gelockert. Die Standardanzeige enthält weiterhin keine unbelegten Pflichttreffer; offene Ideen sind eine ausdrücklich aktivierte Ergänzung.

```bash
.venv/bin/python -W error::ResourceWarning -m unittest discover -s tests -p 'test_*.py'
```

Abgedeckt sind alle 16 geforderten Themen: einzelne/gemischte/Nullinteressen, Aliasfehler, Nachsuche jenseits des neunten Ziels, örtlich unterschiedliche Fixtures, Umkreis und Ausschlüsse, Deduplizierung, Pool/Zeit unbekannt, Quellenfehler und Stacktrace-Redaktion, Abbruch/Zeit/HTTP-Kontingent, Cacheversion, vorhandene Kostenregressionen, Vielfalt, Startortaliase und alte/neue Speicherstände mit PDF. Zusätzliche Desktop-Tests durchlaufen gemischte Interessen, nur Wandern, Baden/Natur, Schwarzwald, kleine Orte sowie Pool und Zuglimit durch Formular, Worker und Ergebnisansicht. Diese Szenarien verwenden ausdrücklich geografisch zugeordnete Testdaten, keine behaupteten Live-Angebote.

Die echte Suchprüfung wurde als begrenzte Kampagne mit **24 HTTP-Aufrufen insgesamt** durchgeführt, getrennt von den neun Katalogwartungsabfragen:

1. **16 Aufrufe**, Start 28.10.2026 11:22 CET: Berlin, Juli 2027, fünf Erwachsene/drei Zimmer, 2.000 EUR, sieben Tage/sechs Nächte, Wandern/Baden/Feiern. Sieben Ziele recherchiert, sechs Filtertreffer (Rostock, Kopenhagen, Danzig, Hřensko, Split, Nizza), Zell am See unvollständig. Hřensko hatte lokal eine Unterkunft; Bad Schandau ergänzte reale Alternativen sowie den typisierten Wanderweg „Bequemer Weg nach Pfaffendorf“. [Protokoll](SUCHLAUF_2026-10-28.json).
2. Nach stärkerer Landschaftspräferenz **acht weitere Aufrufe**, Start 28.10.2026 16:28 CET: gleiche fachliche Kriterien, drei gewünschte Treffer. Rostock vollständig nach Identitätskriterien; Świnoujście nur eine Unterkunft trotz Umgebungssuche bei Międzyzdroje, Zell am See keine. Die Recherche von Děčín/Hřensko/Bad Schandau endete exakt am Budget. Ergebnis: ein Filtertreffer und zwei offene Ideen erhalten; kein künstliches Auffüllen. [Nachprüfprotokoll](SUCHLAUF_FINAL_2026-10-28.json).

Die kurze Nachprüfung belegt korrekten Abbruch und die stärkere Berücksichtigung kleinerer Landschaftsziele, **nicht** sechs vollständig recherchierte ländliche Angebote. Eine anschließend ausgeführte Wiederholung mit aufgezeichneten echten Antworten prüfte den finalen Parser, Speicherung und PDF ohne weitere Netzabfragen. Sie ist ausdrücklich kein weiterer Live-Erfolg. Keine Ergebnisse aus veralteten Snapshots wurden als erfolgreiche neue Liveabfragen gezählt.

## Visuelle Prüfung und verbleibende Grenzen

Ein sichtbares Desktopfenster mit aufgezeichneten echten Quellen wurde per Bildschirmaufnahme geprüft. Die anfänglich abgeschnittene rechte Seite wurde korrigiert; die Fenstergröße berücksichtigt den verfügbaren Bildschirm. Ergebnisliste, eigener Ideenbereich, Basisort/Region, Unterkunftsauswahl und Quellenhinweise sind lesbar. Native automatisierte Mausklicks auf Tk-Reiter lösten in dieser Prüfoberfläche keine nachweisbare Zustandsänderung aus; die vollständige manuelle Klick-Abnahme aller Szenarien ist daher **nicht bestätigt**. Formular-/Callback-/Worker-Flows sind durch die echten Tk-Integrationstests geprüft. Kein Schluss, dass alle nativen UI-Wege damit manuell abgenommen seien.

Die aus einem erneut geöffneten SQLite-Stand exportierte Hřensko-PDF umfasst acht Seiten und 38 Links. Alle acht Seiten wurden gerendert und visuell geprüft: Quellenalter, Umkreisabstände, lange Hinweise, Umlaute, Seitenzahlen und Absätze sind lesbar, ohne abgeschnittene Texte oder Überlagerungen. Ausgabe lokal unter `output/pdf/Suchverbesserung-Hrensko-2027.pdf` (nicht in Git).

Weiter offen: vollständige Livepreise, Belegung und Verfügbarkeit; datierte Bahn-/Flugverbindungen; konkrete Maut/Parken/Fährpreise; datierte Veranstaltungen; exaktes Gebiets-Polygonmodell und belegte Umgebungswege. Harte Ausstattungskriterien bleiben mangels Daten häufig unbelegt. Neue Zieltypen allein verbessern die Quellenabdeckung nicht automatisch. Suchlinks bleiben Recherchehilfen, keine geprüften Angebote. Laufende API-/KI-/Hostingkosten bleiben null; keine neuen Schlüssel erforderlich.
