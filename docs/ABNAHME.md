# Abnahmeprotokoll

Abschlussprüfung: **28.10.2026**. Letzter echter Quellen-/Suchlauf: **27.10.2026, 18:07 CET**. Die Wiederaufnahme am 28.10. enthält keine erneute Behauptung aktueller Livepreise.

## Ergebnis

Der lokale Desktop-Rechercheablauf ist implementiert und getestet. Die vollständige fachliche Abnahme eines buchbaren, belegungsgeprüften Reiseangebots mit Livepreisvergleich ist **nicht erreicht**. Die Anwendung bietet reale Identitäten und Straßenrouten sowie ausdrücklich unvollständige Kostenvergleiche. Die nachstehend getrennten Einschränkungen sind kein erfolgreicher Angebotsnachweis.

## Reproduzierbarer echter Suchlauf

Eingaben: Berlin, unterstützte Europaauswahl, fünf Erwachsene, drei Zimmer, 2.000 EUR Gruppenbudget, Wandern/Baden/Feiern jeweils Gewicht 5, Auto/Zug/Flug aktiviert, Juli **2027**, sieben Kalendertage/sechs Nächte. Ein Fahrzeug mit fünf Sitzen, 7 l/100 km und 1,80 EUR/l als sichtbare Nutzereingaben.

Manuell gestarteter Lauf über `scripts/live_check.py`: 14 tatsächliche HTTP-Abfragen; sieben Ziele, davon sechs mit mindestens zwei unterschiedlichen Unterkunftsidentitäten. Zell am See löste die Recherche eines Reserveziels aus. Vollständige öffentliche Testparameter und Ergebniszusammenfassung: [LIVE_TEST_2026-10-27.json](LIVE_TEST_2026-10-27.json).

| Ziel | Unterkunftsidentitäten | Passende Aktivitätseinträge | Ausgewiesene Benzin-Teilschätzung für die Gruppe |
|---|---:|---:|---|
| Rostock | 8 | 10 | 52,08–69,43 EUR |
| Kopenhagen | 8 | 3 | 169,56–226,08 EUR |
| Split | 8 | 0 | Keine ausgewählte Autooption wegen möglicher Zwischenübernachtung |
| Danzig | 8 | 1 | 116,93–155,91 EUR |
| Nizza | 4 | 3 | Keine ausgewählte Autooption wegen möglicher Zwischenübernachtung |
| Zell am See | 0 | 2 | 173,90–231,87 EUR; ausdrücklich Teilergebnis |
| Innsbruck | 8 | 4 | 170,42–227,23 EUR |

Diese Beträge sind **keine Gesamtpreise**. Unterkunft, Maut/Vignetten, Parken und gegebenenfalls Fähren sind unbekannt. Zug-/Flugpreise und Transfers ebenfalls. Kein Ergebnis wird als sicher budgetkonform bezeichnet. Die Aktivitätszahlen belegen nicht die vollständige Abdeckung aller drei Interessen an jedem Ort; Split liefert nach konservativer Klassifikation keine passenden Aktivitätseinträge. Ein Park allein wird nicht als nachgewiesene Wandermöglichkeit eingestuft.

Alle 65 Katalog-Ortsseiten und ihre Koordinaten wurden separat über gruppierte Wikimedia-Abfragen überprüft. Die Katalogauswahl umfasst 29 Länder, nicht sämtliche europäischen Reiseziele. Mehrdeutige Ortsseiten für Lagos und Bergen wurden auf eindeutige Seiten korrigiert.

## Getestete Funktionen

- **72 automatisierte Tests bestanden:** 32 vorhandene Tests unverändert beibehalten, 40 zusätzliche Tests. Befehl: `.venv/bin/python -W error::ResourceWarning -m unittest discover -s tests -p 'test_*.py'`.
- Fachtests: Kalendertage/Nächte, flexible Datumsstichproben, Fahrzeugkapazität und mehrere Fahrzeuge, Zimmerverteilung, Decimal-Kosten, Budget ohne optionale Extras, unbekannte/veraltete Preise, Nullgewichte, Ranking, Pflichtfilter, Vignetten-Gültigkeitslogik und Einheiten-Normalisierung mit Belegungsanforderung. Die Vignettenlogik ist getestet, konkrete Vignettenpreise werden mangels Quelle nicht behauptet.
- Parser-/Providertests: echte Bled-Fixtures, Identitäts-Deduplizierung, sichere Links, keine Übernahme undatierter Veranstaltungen oder unspezifischer Reiseführerpreise, kostenlose Aktivitäten nur mit ausdrücklichem unbedingtem Quellenhinweis, Quellen-Ausfall, historischer Snapshot-Fallback, Abfragebudget und Unterprozessfreigabe bei Abbruch.
- Datum/Zeit: UTC-Speicherung, Darstellung in Europe/Berlin, Tageswechsel und Sommer-/Winterzeit. Keine erfundenen Flug-/Bahnfahrpläne; entsprechende Fahrplanintegration ist nicht getestet.
- Desktop-Tests: Kriterien laden, Optionen wechseln, Neuberechnung, Speichern, Wiederöffnen, Ändern, PDF-Speicherdialog, Verwerfen verspäteter Ergebnisse und Bedienbarkeit bei langsamer Quelle. Netzwerkzugriffe laufen außerhalb des Tk-Threads.
- Persistenz zusätzlich außerhalb der Testsuite: echten Rostock-Vorschlag mit geänderter Unterkunft gespeichert, ersten Python-Prozess beendet, in neuem Prozess Auswahl, fünf Erwachsene, sechs Nächte und unbekannten Budgetstatus erfolgreich wiederhergestellt. Testdatenbank liegt getrennt unter `tmp/verification/`.
- Einstiegspunkt: `python3 main.py --help` funktioniert über die Projektumgebung; alte simulierte CLI ohne `--demo` wird mit Fehlerstatus 2 abgewiesen. Kein Commit, Push oder Deployment vorgenommen.

## Visuelle Prüfung

Am 27.10.2026 wurde das Desktopfenster über eine tatsächliche Bildschirmaufnahme überprüft. Apples System-Python mit Tk 8.5 zeigte trotz Theme ein weitgehend leeres Fenster. Python 3.13.18 mit Tk 9.1 wurde eingerichtet; die erneute Aufnahme zeigte lesbare Filter, Ergebnisliste, Unterkunfts-/Transportauswahl und Reisedetails. Das frühere Projektlog behauptete eine vollständige Behebung allein durch das Theme; diese Behauptung wird durch die jetzige Prüfung korrigiert, ohne die historischen Einträge oder Nutzeränderungen zu löschen.

Die finale Beispiel-PDF `output/pdf/Beispielreise-Rostock-Juli-2027.pdf` wurde aus dem echten Lauf erzeugt: **neun Seiten, 56 klickbare Links**. Alle neun Seiten wurden als PNG gerendert und visuell geprüft. Umlaute, lange Hinweise, Quellenpflege-Daten, Seitenzahlen und Ränder sind lesbar; Unterkunftsabschnitte bleiben zusammen. Es wurden keine abgeschnittenen Texte oder Überlagerungen festgestellt. Die PDF ist ein damaliger Recherchestand und kein buchbares Angebot.

## Funktionierende Fallbacks

- Historische Ortsdaten aus lokalem Cache oder acht mitgelieferten, quellenbelegten Snapshots; sichtbar als möglicherweise veraltet.
- Booking-Suchlinks mit Ziel/Unterkunft, Daten, Personen, Zimmern und EUR; ausdrücklich keine geprüften Angebote.
- Google-Flights-Suchlink sowie allgemeine DB-/CHECK24-/Trivago-Anbieterlinks. Links sind kein Livepreisvergleich; Eingaben und Verfügbarkeit müssen beim Anbieter geprüft werden.
- Bei fehlender Straßenroute bleibt Benzin unbekannt. Keine Luftlinie wird als Straßenroute ausgegeben.
- Fehlende Ausstattung wird nicht bestätigt. Pflichtfilter können deshalb zu null Ergebnissen führen.

## Verbleibende Einschränkungen

1. Kein nachgewiesener kostenfreier Zugang für integrierte datums-/belegungsbezogene Hotel-, Bahn- und Flugpreise. Keine bestätigten freien Zimmer, Belegungen, Gepäck- oder Stornotarife. [Quellenprüfung](DATENQUELLEN.md) trennt geprüfte Dokumentation von tatsächlicher Integration.
2. Keine europäische Bahn-/Flugverbindungssuche und keine vollständige Tür-zu-Tür-Anbindung. Exakte Startadresse bleibt lokal; Auto ab Ortszentrum, Hotelzufahrt unbekannt. Zeitlimits beziehen sich auf die obere Modellschätzung.
3. Keine konkreten Maut-, Vignetten-, Park- oder Fährpreise. Benzinpreis ist Nutzereingabe, keine aktuelle Tankstellenabfrage. Keine Fremdwährungsangebote und deshalb kein FX-Adapter.
4. Unterkünfte/POIs aus Reiseführern können veraltet sein. Quellenpflege-Datum wird soweit vorhanden angezeigt; Abrufdatum beweist keine inhaltliche Aktualität. Untergeordnete Stadtteilartikel werden nicht rekursiv durchsucht.
5. Aktivitäten sind je nach Quelle lückenhaft. Keine zuverlässige datierte Veranstaltungsquelle, keine pauschal angenommenen kostenlosen Eintritte oder Aufenthaltskosten.
6. Keine Rundreise, Kinder-/Altersmodelle, Buchung, Zahlung, lokale KI oder Wettervorhersage. Mehrere Ziele bleiben sichtbar deaktiviert.

Für den implementierten Ablauf sind keine API-Schlüssel erforderlich. Es gibt keine zahlungspflichtigen Provider oder automatischen Upgrades. Die fehlende vollständige Livepreis-Abnahme bleibt ausdrücklich offen; sie wird nicht durch Demoangebote ersetzt.
