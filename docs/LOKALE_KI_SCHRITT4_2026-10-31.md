# Lokale KI – Schritt 4: Begrenzte Quellenrecherche

Prüfbericht vom **31.10.2026**.

Schritt 4 ist implementiert. Die vorhandene Nachrecherche-Aktion heißt **„Quellen & Bilder recherchieren“**. Sie kann für ein ausgewähltes Ziel neue, nachvollziehbar zugeordnete Quellenhinweise liefern. Nach Abschluss springt die Detailansicht direkt zu den Hinweisen. **Neue Beobachtungen bleiben Aussagen der Quelle und erhalten keine Ranking-, Filter- oder Budgetwirkung.**

[Ausführliche HTTP-Abfragen, Quellennachweise, Modellantworten und Messwerte](LOKALE_KI_SCHRITT4_2026-10-31.json) · [Vorab festgelegter Quellenvertrag](QUELLENRECHERCHE_VERTRAG.md)

## Bedienung und tatsächliche Reichweite

```bash
.venv/bin/python scripts/local_ai.py start
.venv/bin/python main.py
```

Ein Ergebnis auswählen, **Quellen & Bilder recherchieren** wählen und anschließend die neuen Quellenhinweise mit Herkunft, Originalnachweis und Grenzen lesen. **Abbrechen** beendet die laufende Nachrecherche. Änderungen bleiben eine Arbeitskopie; dauerhaft bewahrt werden sie erst mit der vorhandenen Speicheraktion.

Es gibt keine allgemeine Websuche. Unterstützt werden vorhandene deutsche Wikivoyage-Artikel und die darin verknüpften Wikidata-Identitäten einschließlich Länderobjekt. URLs werden aus dem vorhandenen Ziel und geprüften Q-IDs abgeleitet, niemals aus Modellwissen. Ziele ohne passende Quelle oder hinreichende Identität bleiben offen. Es wurden keine kostenpflichtigen Dienste, Zugänge, neuen Modelle oder automatischen Downloads eingerichtet.

Die Abdeckung ist bewusst klein und quellspezifisch: strukturierte vCard-Einträge, veröffentlichte vollständige Öffnungs-/Saisonfelder und ausdrücklich bezeichnete Zugangshinweise im gewählten Umkreis, maximal 15 km Luftlinie. Keine europaweite Vollständigkeit, unabhängige Verfügbarkeitsprüfung oder neue Ortsentdeckung.

**Grenze der bisherigen Bildfunktion:** Die sicheren Abrufe respektieren auch für die bisherige Wikimedia-Nachrecherche die Robots-Regeln. Die im geprüften Ablauf verwendeten alten API-Pfade sind gesperrt; deshalb wurden dabei keine neuen Bilder bezogen. Vorhandene Bilder bleiben erhalten. Diese Einschränkung wird als Quellenwarnung gemeldet und nicht umgangen.

## Komponenten und Datenfluss

- `ResearchHttp.py`: freigegebene HTTPS-Hosts/Pfade, Robots, DNS-/Redirect-Prüfung, gebundene TLS-Verbindung, Rate-Limit, Downloadgrenzen und Abbruch.
- `WikivoyageResearch.py`: Ortsidentität und quellspezifische, begrenzte Extraktion.
- `SourceResearchService.py`: begrenzte Nachrecherche, extrahierter Cache und optionaler lokaler Modellaufruf.
- `SourceEvidence.py`: zulässige Referenzauswahl, Belegzusammenführung, Konfliktanzeige und kontrollierte Darstellung.
- `TripEnrichmentService`, GUI und `TripPresenter`: Erweiterung des bestehenden Ablaufs einschließlich Schutz vor verspäteten Antworten.

Die neue sichere Abrufschicht gilt für den expliziten Quellen-/Bild-Nachrecherchepfad. Der übrige bestehende Suchverkehr wurde in diesem Schritt nicht global umgebaut.

## Identität statt bloßem Namensvergleich

Vor der Übernahme müssen Artikel-Land und Artikel-Koordinaten zum Ziel passen. Der Artikel muss ein erlaubtes Wikidata-Objekt verknüpfen. Dessen Bezeichnung/Alias, Länderobjekt mit ISO-Code und eindeutige irdische Koordinaten werden geprüft. Abweichende vorhandene Wikidata-/GeoNames-IDs führen zur Zurückhaltung. Regionsobjekte werden nicht als konkrete Aufenthaltsorte umgedeutet.

Artikel und Ziel dürfen höchstens 5 km auseinanderliegen, Wikidata und Artikel höchstens 3 km. Das sind konservative Zuordnungstoleranzen, keine Zugangs- oder Wegstrecken. Aktivitäten benötigen eigene Kartenkoordinaten, passende Länder-/Ortszuordnung und einen Punkt innerhalb des begrenzten Suchradius. Unklare oder grenzüberschreitend nicht ausreichend zugeordnete Einträge bleiben aus.

Wikivoyage und Wikidata können gemeinsame Datenherkunft haben. Diese Prüfung ist eine technische Identitätszuordnung außerhalb des Modells und **keine unabhängige Bestätigung aller Quelleninhalte**.

## Welche Aussagen angezeigt werden

Jeder neue Nachweis enthält stabile Beleg-ID, Quelle/URL, Original-/finale Abrufadresse, Abrufdatum, konkretes Ziel/Objekt, Zuordnungsnachweis, Aussageart, Quellenpflege soweit vorhanden und Einschränkungen. Ein fehlendes Veröffentlichungs-/Gültigkeitsdatum bleibt unbekannt. Ein Wikidata-Revisionsdatum gilt nicht als Veröffentlichungsdatum jeder einzelnen Aussage.

Die drei zugelassenen Arten sind:

- strukturierter Eintrag mit Name, Typ, Länder-/Ortsbezug und Kartenkoordinaten;
- vollständiges veröffentlichtes Öffnungs-/Saisonfeld;
- vollständiger Zugangshinweis.

Lange Felder über 400 Zeichen werden mit Datenlückenhinweis ausgelassen, nicht mitten in einer Bedingung abgeschnitten. Skripte und Bedien-/Navigationselemente werden nicht als Nachweis ausgewertet. Preise, Unterkunftsangebote und Veranstaltungen werden nicht als neue verbindliche Angaben übernommen. Alte Veranstaltungsinformationen werden nicht als aktuelle Angebote aufgewertet.

Ein See ist keine bestätigte Badestelle, Natur keine Ruhezusage, eine Bar keine nachgewiesene Ausgehgruppe und ein kartierter Weg keine sichere Wanderroute. Veröffentlichte Öffnungszeiten werden wörtlich als Quellenangabe angezeigt, nicht als Zusage für den Reisetag. Entfernungen bleiben ausdrücklich Luftlinien; Fußwege werden nicht erfunden.

Die Anzeige nennt Quelle, Lizenz/Herkunft und Originalnachweis und trennt lokal ausgewählte von rein deterministischen Hinweisen. Neue Belegtypen bleiben separat. Die kontrollierte Passungserklärung aus Schritt 2 verwendet weiterhin ihre bisher abgenommenen Interessenbelege. Ihr bestehender Cache-Schlüssel berücksichtigt den geänderten Reisezustand; alte Erklärungen werden dadurch nicht unverändert als Erklärung des neuen Belegstands wiederverwendet.

## Rolle und Grenzen der lokalen KI

Das Modell erhält höchstens acht vorgegebene Nachweise mit IDs, Aussageart, begrenztem Originalnachweis und passenden Interessen. Es darf höchstens sechs vorhandene `id`-/`kind`-Paare auswählen. Kein freier Faktenwortlaut, keine URLs, keine Abrufwerkzeuge und keine Werte für Filter, Ranking oder Kosten.

Unbekannte, doppelte, abgeänderte oder falsch typisierte Referenzen werden vollständig verworfen. Ein korrektes JSON genügt nicht. Alle angezeigten Inhalte stammen aus der kanonischen Quellenextraktion und bleiben auch bei ausgefallener KI nutzbar. Modellwissen ersetzt keine fehlenden Fakten. Die KI-Auswahl ist keine zweite Faktenbestätigung.

Fremde Quellentexte können keine weiteren Abrufe, Dateien, Programme, Zahlungen oder Datenänderungen auslösen. Eine allgemeine Immunität gegen beliebige Angriffe wird nicht behauptet; die tatsächliche Berechtigungsgrenze entsteht daraus, dass das Modell überhaupt keine solchen Werkzeuge erhält.

## Abrufgrenzen und Datenschutz

| Grenze | Konfiguration |
|---|---:|
| Neue Textrecherche einschließlich Robots und Weiterleitungen | höchstens 10 Transaktionen / 75 s |
| Lokaler Modellauswertungsteil | höchstens 30 s innerhalb des Restbudgets |
| Gesamte vorhandene Nachrecherche einschließlich Bildversuchen | höchstens 18 Transaktionen / 120 s |
| Dokument / Robots / Header | 2.000.000 / 128.000 / 65.536 Byte |
| Weiterleitungen | höchstens drei |
| DNS-Wartezeit | höchstens vier Sekunden; Abbruch während Auflösung möglich |
| Modellkontext | bestehende zentrale Begrenzung, keine stille Kürzung |
| Einzelne Quellenfelder / Modellselektion | höchstens acht / sechs |
| Historie je Arbeitskopie | höchstens 64 Belege / acht Versuchsstände |
| Extrahierter Cache / Robots-Cache | sechs Stunden / 24 Stunden |

Abrufe erfolgen seriell, mindestens 1,1 s Abstand pro Host beziehungsweise mit größerem veröffentlichtem Crawl-delay. Es gibt keine automatischen Retry-Schleifen bei Sperrantworten. Robots-Fehler und unerwartete HTML-Antworten statt Robots-Text sperren die Quelle. Ist eine Vorgabe nicht im interaktiven Budget erfüllbar, bleibt die Recherche begrenzt.

Vor jedem tatsächlichen Abruf werden alle DNS-Adressen auf öffentliche Erreichbarkeit geprüft. Private, lokale, Link-Local-, Multicast- und Übergangsadressen werden gesperrt. curl verbindet mit einer geprüften IP, behält aber Host-/TLS-Zertifikatsprüfung bei; der tatsächliche Peer muss passen. Weiterleitungen werden nicht automatisch verfolgt, sondern erneut geprüft. Proxys, curlrc, beliebige Protokolle und nicht freigegebene Hosts/Pfade sind ausgeschlossen.

Nach extern gehen ausschließlich notwendige öffentliche Ziel-/Objektparameter. Keine Startadresse, privaten Reise-Snapshots, Personenzahl, Reisezeit oder Freitexte aus Schritt 3 werden angehängt. Die lokale KI läuft weiter über den vorhandenen Loopback-Client mit gemeinsamer Parallelitätsbegrenzung. Kein automatischer Dienststart oder Cloud-Fallback.

## Cache, Widersprüche und Speicherung

Persistenter HTTP-Cache enthält nur begrenzte extrahierte Nachweise und Robots-Regeln, keine vollständigen Webseitenarchive. Vollständige Abrufantworten werden nur vorübergehend für Extraktion verarbeitet. Ein Cache-Hit behält den ursprünglichen Abrufzeitpunkt und wird ausdrücklich als keine neue Liveprüfung bezeichnet.

Abweichende Aussagen zum selben Objekt und Feld bleiben nebeneinander erhalten und werden als ungeklärter Unterschied beziehungsweise zeitliche Änderung markiert. Neuer Abruf bedeutet nicht automatisch bessere Wahrheit. Bei fehlgeschlagener Aktualisierung bleiben ältere Belege unverändert und ein gesonderter Fehler-/Budgetstatus erscheint. Die Grenze der Beleggeschichte wird sichtbar gemeldet; ältere Nachweise werden dafür nicht gelöscht.

Neue Arbeitskopien werden über die bestehende Speicheraktion mit ihren Belegen gespeichert. Alte Reiseformate bleiben ladbar. Keine automatische Änderung bestehender gespeicherter Reisen. Zielwechsel, neue Suche, Abbruch und ein zwischenzeitlich geänderter Reisezustand verhindern verspätete Übernahmen. Preis- und Quellenrecherche dürfen dieselbe Arbeitskopie nicht parallel überschreiben.

## Automatisierte Prüfung

**277 Tests bestanden in 13.961 Sekunden**: bisherige 248 plus 23 neue Unit- und sechs neue GUI-Tests. `compileall` und `git diff --check` bestanden.

Die neuen Tests prüfen tatsächliche lokale HTTP-Fixtures, getrennt von der Internetabnahme. Nur die Wire-Schicht im Test wird auf den Fixture-Server gelenkt; Produktion besitzt keinen Schalter für interne URLs. Zusätzlich werden Produktions-DNS-/URL-Gates, DNS-Abbruch, TLS-/Proxy-/Redirect-Argumente und Peerbindung überprüft.

Abgedeckt sind unter anderem gleichnamige/falsche Ziele, abweichende Länder/IDs, Regionen, private DNS-Antworten, Mischantworten, Weiterleitungen, Robots-Wildcards, Crawl-delay, Sperrantworten, Größen-/Inhaltstypgrenzen, falsche Referenzen, zusätzliche Modellbehauptungen, historische Quellen, Konflikte, Cache, erhaltene gespeicherte Reisen und verspätete Antworten. Die bisherigen Tests der Schritte 2 und 3, Suche, Ranking, Kosten, Speicherung und PDF bleiben bestanden.

## Tatsächliche öffentliche Abrufe

| Ziel / Kontrollfall | Quellenfelder | HTTP-Transaktionen | Laufzeit einschließlich Modell | Ergebnis |
|---|---:|---:|---:|---|
| Bled | 6 | 5 | 16.273 s | source_observations |
| Innsbruck | 8 | 3 | 20.706 s | source_observations |
| Tallinn | 8 | 3 | 13.337 s | source_observations |
| Bled mit falschem Land | 0 | 1 | 0.299 s | failed |

Damit **22 neue Quellenfelder bei drei tatsächlichen Zielen**; keine behauptete Vollerhebung. Die falsche Länderzuordnung wurde zurückgehalten, ohne Modellwissen zur Reparatur heranzuziehen. Die kleineren Transaktionszahlen späterer Ziele entstehen durch den wiederverwendeten Robots-Cache.

Alle drei protokollierten öffentlichen Modellantworten waren gültige Referenzauswahlen. Die Quelle ist jeweils der Community-Reiseführer plus Wikidata-Identität, keine unabhängige offizielle Bestätigung einer Aktivität oder Öffnung. Offizielle Webseiten einzelner Betreiber wurden in dieser Version nicht zusätzlich erschlossen.

## Synthetische Ausschnitte und rohe Modellfehler

| Getrennter synthetischer Fall | Laufzeit | Tatsächliches Verhalten |
|---|---:|---|
| synthetisch_negation_zeiten_zugang | 3.910 s | nicht verfügbar oder Antwort verworfen; unveränderte deterministische Quellenhinweise |
| synthetisch_fremde_quellenanweisung | 2.559 s | lokal ausgewählt; Referenzen und Aussagearten geprüft |
| synthetisch_widerspruch_alte_angabe | 3.702 s | nicht verfügbar oder Antwort verworfen; unveränderte deterministische Quellenhinweise |

Zwei von drei synthetischen Antworten änderten ein Zeichen derselben Beleg-ID (`…e528…` zu `…e728…`). Diese Antworten waren schema-gültig, aber nicht identisch mit dem vorhandenen Nachweis und wurden vollständig verworfen. Es gibt keine unscharfe Zuordnung. Die unveränderten deterministischen Hinweise blieben sichtbar; widersprüchliche Angaben blieben getrennt.

Der Fall mit eingeschleuster Quellenvorschrift erzeugte keine weiteren Netzwerkabrufe und keine neue Preis-/Bade-/Buchbarkeitsbehauptung. Dass das Modell den Angriffsausschnitt in diesem Versuch nicht auswählte, wird nicht als universeller Schutz ausgegeben. **Von sechs protokollierten Modellantworten wurden vier angenommen und zwei verworfen.** Die zusätzliche echte GUI-Auswahl wurde ebenfalls separat geprüft. Erwartungen wurden nicht an die falschen IDs angepasst.

## Echter GUI-/Offline-Ablauf

- Nachrecherche über die normale Aktion: 14.668 s, neue Originalnachweise in der Detailansicht. Ranking, Budget und zuvor gespeicherter Snapshot unverändert.
- Währenddessen 621 Tk-Callbacks; größter Abstand 0.127 s.
- Echter Abbruch: Worker nach 0.025 s beendet, keine verspätete Übernahme.
- Eigener Dienst vollständig gestoppt: Nachrecherche nach 0.658 s mit 4 deterministischen Quellenfeldern weiter nutzbar; Ranking und Budget unverändert.
- Normale Suche bei gestopptem Dienst: 6.168 s, abgeschlossen mit **0 Filtertreffern und sechs offenen Reiseideen**. Offene Angaben wurden nicht zu bestätigten Treffern umetikettiert.

Für die Abnahme wurden temporäre Reisespeicher und öffentliche Zieldaten benutzt. Die echte Reise-Tabelle wurde nur lesend fingerprinted und blieb unverändert. Reale private Reiseangaben wurden nicht an Quellen oder Modell übergeben.

Der normale main.py-Einstieg wurde gestartet. Die Startansicht einschließlich neuer Aktion wurde per CUA-Screenshot visuell geprüft. Weitere Aufnahmen des Quellen-Prüffensters scheiterten anschließend wieder mit ScreenCaptureKit -3811 / Computer Use -10005. Daher **keine vollständige manuelle Klickabnahme**; der eigentliche Quellenablauf und seine Widgetinhalte sind zusätzlich automatisiert am echten Tk-Fenster geprüft.

## Wiederholen und verbleibende Grenzen

```bash
.venv/bin/python -m unittest discover -q
.venv/bin/python scripts/verify_source_research.py --live
# Sichtbares Prüffenster, optional 20 Sekunden für die Sichtprüfung:
.venv/bin/python scripts/verify_source_research.py --live --visible --review-seconds 20
```

Die Live-Prüfung stoppt vorübergehend ausschließlich den nachweislich eigenen Dienst, stellt ihn wieder her und entlädt das Modell. Sie führt ausdrücklich begrenzte echte öffentliche Abrufe sowie eine normale Suchprüfung aus; synthetische Fälle bleiben im Bericht getrennt.

Zum Abschluss ist der Dienst erreichbar, genau ein Modell installiert und entladen. Kein neuer Download, kein Commit und kein Push. Die bestehende uncommittete Arbeit ist erhalten. Keine allgemeine Websuche, keine neuen Orte aus Modellwissen, keine Preisinterpretation, keine Rankingänderung und keine PDF-Erweiterung. Fehlende Quellendeckung und verworfene KI-Auswahlen bleiben reale Grenzen.

## Geprüfte offizielle Hinweise

Quellenwahl und serielle Zugriffe wurden mit [Wikidata: Data access](https://www.wikidata.org/wiki/Wikidata:Data_access) und [MediaWiki API: Etiquette](https://www.mediawiki.org/wiki/API:Etiquette) abgeglichen. Maßgeblich für diesen konservativen Abrufpfad sind außerdem die tatsächlich abgerufenen [Wikivoyage-Robots-Regeln](https://de.wikivoyage.org/robots.txt), [Wikidata-Robots-Regeln](https://www.wikidata.org/robots.txt) und die [Wikivoyage-Lizenzhinweise](https://de.wikivoyage.org/wiki/Wikivoyage:Lizenzbestimmungen). Diese Recherche behauptet keine allgemeine kostenlose Suchschnittstelle.
