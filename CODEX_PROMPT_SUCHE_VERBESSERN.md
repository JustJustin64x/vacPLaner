# Entwicklungsauftrag: Fehlersuche und grundlegende Verbesserung der Zielsuche

Arbeite im bestehenden Projekt `/Users/justinzimmermann/Documents/vacPLaner`. Untersuche und verbessere die automatische Überraschungsreise-Suche. Setze die Änderungen tatsächlich um, teste sie und aktualisiere die Dokumentation. Die aktuelle lokale Desktop-Anwendung, Speicherung und PDF-Funktionen sollen weiter nutzbar bleiben.

## Nutzerproblem und Ziel

Der Nutzer berichtet: Sobald Interessen angegeben werden, findet die Anwendung kein einziges Reiseziel. Reproduziere diesen Fehler und finde die konkrete Ursache. Vermute nicht einfach, dass zusätzliche Orte das Problem allein lösen.

Außerdem soll die Suche wesentlich vielfältiger werden: kleine Orte, Dörfer, Ferienorte, Seen, Küstenabschnitte, Inseln, Wandergebiete und Bergregionen müssen ebenso berücksichtigt werden wie Städte. Für Interessen wie Wandern und Baden sollen geeignete ländliche Urlaubsgebiete regelmäßig vorkommen. Groß- und Hauptstädte dürfen den Vergleich nicht allein wegen besserer Datenabdeckung dominieren.

Erwarteter Ablauf: Startort, Zeitraum, Dauer, Erwachsene, Zimmer, Budget und Interessen eingeben → passende Ziele selbstständig entdecken → echte Unterkunftsalternativen am Ziel oder in seiner Umgebung recherchieren → verfügbare Anreisemöglichkeiten und interessenbezogene Aktivitäten anzeigen. Das Budget bleibt eine weiche Grenze für die gesamte Gruppe; optionale Verpflegung und Aktivitäten bleiben außerhalb des Budgetvergleichs.

Alle bisherigen Grenzen gelten weiter: lokale Desktop-App, Deutsch/EUR/km, Europa, eine feste Urlaubsbasis pro Reise, strikt keine laufenden API-/KI-/Scrapingkosten, keine Buchungen, keine erfundenen Angebote. Bestehende uncommittete Änderungen bewahren. Kein Umbau zur Website und kein kostenpflichtiger Dienst.

## Ausgangspunkte aus der Codeprüfung am 28.10.2026

Prüfe diese Befunde erneut am aktuellen Stand:

- `core/planning/DiscoveryService.py` schneidet die Kandidatenliste früh auf `shortlist + 3` ab: standardmäßig höchstens neun Ziele. Danach findet keine adaptive Nachsuche im restlichen Katalog statt.
- `infrastructure/planning/DestinationCatalog.py` verwendet 65 kuratierte Orte. Länder und Regionen werden per exakter Zeichenkettenübereinstimmung gefiltert. Eine Eingabe wie „Schwarzwald“ kann damit ohne hilfreichen Hinweis alle Kandidaten entfernen, obwohl beispielsweise Freiburg enthalten ist.
- `RankingService.interest_match()` prüft nur, ob ein Interesse in einer redaktionellen Schlagwortliste des Ortes vorkommt. Es gibt keine abgestufte Stärke, räumliche Umgebung oder belastbare Begründung je Interesse.
- Aktivitäten werden separat gefiltert; fehlende passende Aktivitäten allein schließen ein Ziel derzeit nicht aus. Deshalb ist ein genereller „Interessenfilter entfernt alle Ziele“-Fehler noch nicht belegt.
- Der Wikivoyage-Parser liefert derzeit leere Ausstattungsinformationen. Ein Pflichtmerkmal wie Pool kann sämtliche Unterkünfte ausschließen. Fehlende Belege sind unbekannt, nicht automatisch falsch oder erfüllt.
- Bei gesetzter maximaler Reisezeit werden alle Bahn-/Flugoptionen ausgeschlossen, weil diese bisher keine bestätigte Dauer besitzen. Ohne verbleibende Autooption fällt das gesamte Ziel weg.
- Die Recherche beschränkt sich auf eine Ortsseite. Nahegelegene Unterkünfte und relevante regionale bzw. untergeordnete Seiten werden nicht systematisch berücksichtigt.
- Aktivitätstypen werden über eine kleine feste Zuordnung erkannt. Prüfe tatsächliche Quellenstrukturen, alternative Typbezeichnungen und Mehrfachtypen; leite daraus gezielte Parserverbesserungen ab.
- Es werden zwar Datumsstichproben berechnet, einem Ziel wird aber nur eine davon anhand seiner Position in der Liste zugeteilt. Das ist keine echte Terminoptimierung.
- Unerwartete Suchfehler werden in der GUI nur mit dem Exception-Typ angezeigt. Das erschwert die Ursachenanalyse.
- `InterruptedError` erbt von `OSError`: Prüfe alle breiten Exception-Handler in Provider und Suche, damit Abbruch, Zeitlimit und ausgeschöpftes Abfragebudget nicht als gewöhnlicher Quellenfehler verschluckt werden.

Ein kontrollierter Diagnoseversuch mit dem bestehenden `FixtureProvider` ergab:
- Nur Wandern: sechs Ergebnisse.
- Wandern + Baden + Feiern: sechs Ergebnisse.
- Pool als Pflichtmerkmal: null Ergebnisse.
- Nur Zug und maximal acht Stunden: null Ergebnisse.
- Regionsfilter Schwarzwald: null Ergebnisse ohne Ausschlusshinweis.

Das sind Tests mit kontrollierten Daten zur Eingrenzung der Suchlogik, keine Belege für aktuelle reale Ergebnisse oder die genaue Nutzerursache. Insbesondere liefert der alte FixtureProvider dieselben Bled-Einträge für unterschiedliche Ziele; verwende diesen vereinfachten Provider nicht als Nachweis korrekter geografischer Suche.

## 1. Fehler reproduzieren und diagnostizierbar machen

Verfolge den gesamten Ablauf von GUI-Eingabe über `SearchRequest`, Startortauflösung, Kandidatenfilter, Vorauswahl, Provider und Ranking bis zur Ergebnisanzeige. Prüfe leere Eingaben, Nullwerte, deutsche Dezimalkommas, Interessen allein und Interessen kombiniert mit weiteren Filtern. Unterscheide Validierungsfehler, echte fachliche Ausschlüsse, fehlende Belege, Netzwerkfehler und Programmfehler.

Implementiere eine strukturierte Suchdiagnose mit Such-ID und Zählern je Stufe:
- Kandidaten in der Datenbasis.
- Nach Gebiet und Ausschlüssen verbleibende Kandidaten.
- Lokal bewertete und tatsächlich online untersuchte Ziele.
- Ziele mit passenden Unterkünften, Aktivitäten und prüfbarer Anreise.
- Ausschlüsse mit konkretem Grund, etwa Region nicht erkannt, Reisezeit überschritten, Reisezeit unbekannt, Pflichtausstattung unbelegt, Quelle fehlgeschlagen oder Abfragelimit erreicht.

Diagnosen dürfen keine privaten Adressen oder Schlüssel unnötig protokollieren. Technische Fehler mit Stacktrace lokal nachvollziehbar machen; im Dashboard verständliche Hinweise statt ungefilterter Tracebacks anzeigen. Einen lokal exportierbaren Diagnosebericht mit Suchkriterien ohne genaue Adresse anbieten.

Bei null Ergebnissen eine konkrete Zusammenfassung mit wirksamen Änderungsvorschlägen zeigen. Beispiel: „24 Ziele geprüft. Bei 18 Zielen ist Pool nicht belegt; 6 überschreiten deine Reisezeit.“ Zähler eindeutig definieren, damit Mehrfachausschlüsse keine widersprüchlichen Summen erzeugen. Kein pauschales „Keine Reise gefunden“, wenn tatsächlich ein API-Ausfall oder unbekannter Regionsname vorliegt.

## 2. Interessen als Präferenzen modellieren

Interessen sind standardmäßig gewichtete Wünsche, keine implizite UND-Bedingung. Wandern, Baden und Feiern müssen nicht alle maximal erfüllt sein, damit ein Ziel berücksichtigt wird. Hohe Abdeckung mehrerer Interessen soll besser abschneiden als ein einseitiger Treffer, sofern die Nutzergewichte das stützen.

- Einheitliche Skala von 0 bis 5 für Interessen in GUI, Validierung, Suche und Tests; allgemeine Vergleichsgewichte können weiter 0 bis 100 verwenden.
- Nicht ausgewählte Interessen haben Gewicht null. Wenn alle Interessen null sind, eine gültige offene, vielfältige Suche ermöglichen.
- Interessenpassung und Datensicherheit getrennt berechnen und anzeigen. Wenig Daten beweisen keine mangelnde Eignung, dürfen aber auch keine bestätigte Eignung vortäuschen.
- Unterscheide redaktionelle Eignung, belegte Aktivitäten am Ort und belegte Aktivitäten im erreichbaren Umfeld.
- Keine falschen Schlüsse: Bergregion allein beweist keinen konkreten Wanderweg, Gewässer allein keine erlaubte Bademöglichkeit, eine beliebige Bar kein ausgeprägtes Nachtleben, Stadtstatus keine Festivalverfügbarkeit.
- „Kostenlos“ als Eigenschaft konkreter Aktivitäten behandeln und nicht als Versprechen, eine ganze Destination sei kostenlos.
- Ergebnisse kurz erklären: „Wandern: belegte Wege im Umfeld; Baden: ausgewiesener Badeplatz; Feiern: wenige belegte Angebote.“ Unbekannte Aspekte benennen.

## 3. Breitere und räumlich strukturierte Zielbasis

Erweitere das Datenmodell um stabile IDs, Zieltyp, Aliasse, Länder-/Regionszugehörigkeiten, Koordinaten, Quellen, Prüfdatum und ggf. zugehörige Orte bzw. räumliche Ausdehnung. Prüfe mehrere Regionszugehörigkeiten statt eines einzigen Labels wie „Mitteleuropa“.

Unterstütze mindestens Großstadt, Klein-/Mittelstadt, Dorf/Ferienort sowie regionale Ziele mit See, Küste, Insel oder Bergen/Naturgebiet. Region und Unterkunftsstandort sind unterschiedliche Dinge: Eine vorgeschlagene Region benötigt einen konkreten geeigneten Basisort für Unterkunft und Anreise. Das bleibt eine Ein-Ziel-Reise mit Ausflügen, keine Rundreise.

Baue eine deutlich breitere quellenbasierte Auswahl auf. Orientierungsziel: mindestens 250 eindeutige reale Zielkandidaten über mindestens 20 europäische Länder, davon mindestens 60 Prozent außerhalb von Groß- und Hauptstädten. Stelle Herkunft und sachgerechte Typisierung sicher; keine ungeprüften erfundenen Datensätze zum Erreichen einer Quote. Wenn die belegte Erweiterung eine Grenze hat, dokumentiere sie.

Prüfe beispielsweise geeignete Orte und Basisregionen im Schwarzwald, Harz, an der Mecklenburgischen Seenplatte, in der Sächsischen Schweiz, im Salzkammergut, in der Sächsisch-Böhmischen Schweiz, den Dolomiten, im Triglav-/Bohinj-Gebiet sowie an Seen und Küsten in weiteren europäischen Ländern. Das sind Recherchebeispiele, keine ungeprüften Eignungsbehauptungen oder festen Suchergebnisse.

Verwende offene, belegbare Daten und verantwortungsvolle gebündelte Recherche. Öffentliche Geocodingserver dürfen nicht zur flächendeckenden Ortsinventarisierung verwendet werden. Ein größerer lokaler Index soll viele Kandidaten offline bewerten, ohne pro Suchlauf Hunderte Internetaufrufe auszulösen. Baue Erweiterung und Aktualisierung nachvollziehbar, damit keine schwer wartbare riesige Liste ohne Quellen entsteht.

Länder-/Regionsauswahl im Dashboard aus der unterstützten Datenbasis anbieten, mit verständlicher Suche und Aliasbehandlung. „Österreich“/„AT“, Umlaute, Groß-/Kleinschreibung und gebräuchliche Alternativnamen korrekt normalisieren. Unbekannte Gebiete früh melden und passende Vorschläge machen. Keine stillschweigende Umdeutung eines Gebiets in ganz Europa.

## 4. Mehrstufige adaptive Suche

Ersetze die feste Neun-Ziele-Grenze durch eine adaptive Suchwarteschlange:
1. Breite lokale Kandidatenmenge nach ausdrücklich harten Gebietskriterien filtern.
2. Interessen, Zieltyp, Entfernung als grobe Vorauswahl und Datenlage bewerten.
3. Eine abwechslungsreiche erste Gruppe tiefer recherchieren.
4. Bei Datenlücken oder fachlichen Ausschlüssen weitere geeignete Kandidaten nachziehen, solange Zeit- und Abfragebudget reichen.
5. Verwertbare Ergebnisse sofort anzeigen und bei weiteren Erkenntnissen aktualisieren.

Die gewünschte Ergebnisanzahl, lokal bewertete Kandidatenanzahl und Zahl der Netzabfragen sind getrennte Einstellungen/Begriffe. Bestehende Limits nicht einfach hochsetzen. Cache-Hits dürfen kein HTTP-Kontingent verbrauchen; echte Aufrufe müssen vollständig gezählt werden. Behalte maximal etwa zehn Minuten, Abbruch und providerkonforme Ratenbegrenzung bei.

Diversität umfasst Zieltyp, Landschaft, Region und Land, soweit die Nutzerfilter das zulassen. Verhindere nahezu identische Vorschläge aus benachbarten Orten derselben kleinen Urlaubsregion. Länderdiversität darf keine schlechter passenden Kandidaten starr vor allen geeigneten Kandidaten eines Landes priorisieren. Bei einem ausdrücklich ausgewählten Land ist länderübergreifende Vielfalt irrelevant.

Entfernung ist für die Vorauswahl ein Hinweis, kein Straßenrouting und keine behauptete Zug-/Flugzeit. Großstädte dürfen nicht automatisch wegen vieler POIs gewinnen. Relevante Vielfalt und Evidenz zählen stärker als bloße Anzahl von Einträgen.

Setze teure Abfragen gezielt ein: Ein Ziel ohne Unterkunft wegen sicher verletzter Pflichtfilter benötigt zunächst keine zusätzliche Routingabfrage. Quellenfehler eines Ziels dürfen nicht die gesamte Suche abbrechen. Kontrollabbrüche müssen dagegen sofort korrekt durchgereicht werden.

Entkopple statische Ortsrecherche von Datumsoptionen: denselben Ort nicht für jeden Termin neu abrufen. Wenn keine datierten Preise oder Veranstaltungen vorhanden sind, Terminoptionen als plausible Stichproben zeigen und keine optimale Reisezeit behaupten. Ergebnisse dürfen nicht nur deshalb einen anderen Termin erhalten, weil ihre Ranglistenposition wechselt.

## 5. Unterkünfte und Aktivitäten im Umfeld

Wenn eine kleine Ortsseite nicht genügend Informationen liefert, recherchiere begrenzt passende regionale Seiten, nachgewiesene Unterseiten und nahegelegene Basisorte. Stelle fachliche und geografische Zugehörigkeit sicher; kein beliebiges rekursives Crawling aller Links.

- Für Unterkünfte und Aktivitäten getrennte Suchradien anbieten, mit nachvollziehbaren, begrenzten Standardwerten und einem sichtbaren Opt-out für die Umgebungssuche.
- Suche innerhalb des gewählten Raums zunächst am Basisort und erweitere gezielt bis zum vom Nutzer erlaubten Radius.
- Harte Länder-/Gebietsausschlüsse und Entfernungsgrenzen bleiben wirksam. Grenzüberschreitende Ergänzungen nur, wenn sie zu den gewählten Gebietsregeln passen.
- Entfernungen explizit als Luftlinie oder belegte Wegstrecke kennzeichnen. Bei Seen, Bergen, Fähren und Tälern Luftliniennähe nicht als kurze Erreichbarkeit darstellen.
- Pro Unterkunft und Aktivität tatsächlichen Ort und Abstand zum Basisort anzeigen.
- Gleiche Unterkunft bzw. Aktivität auf mehreren Seiten deduplizieren, aber unterschiedliche Objekte mit ähnlichem Namen erhalten.
- Echte Identitäten und Quellen statt erfundener Ersatzangebote. Preis, Belegung und Verfügbarkeit bleiben ohne Nachweis unbekannt.
- Ein Ziel ohne zwei Unterkünfte nicht als vollständig recherchiert ausgeben; mit nächsten Kandidaten weitersuchen und am Ende ggf. getrennt als unvollständige Idee zeigen.

Verbessere die Aktivitätserkennung anhand gespeicherter echter HTML-Beispiele. Typvarianten und Mehrfachklassifikationen robust normalisieren. Ergänzende Textsignale nur konservativ, mit Herkunft und Tests verwenden. Defekte einzelne Einträge dürfen nicht alle anderen Einträge vernichten. Quellen-Snapshots und Caches müssen bei Parser-/Schemaänderungen sinnvoll versioniert bzw. migriert werden.

## 6. Unbekannt ist weder erfüllt noch ausgeschlossen

Trenne im Ergebnis drei Sachverhalte:
- Kriterien erfüllt bzw. mit ausgewiesenen Annahmen prüfbar.
- Kriterium nachweislich verletzt.
- Kriterium wegen fehlender Daten nicht prüfbar.

Ein hartes Limit bleibt hart: Eine Reise mit unbekannter Bahndauer darf nicht als „unter acht Stunden“ erscheinen. Zeige bei fehlenden Daten auf Wunsch einen getrennten Bereich „Passende Reiseideen – Angaben noch offen“, außerhalb der bestätigten Filtertreffer. Das gilt ebenso für unbelegte Pflichtausstattung. Der Nutzer muss erkennen, warum die Idee separat erscheint.

Filter dürfen nicht stillschweigend gelockert werden. Biete gezielte Aktionen an, beispielsweise „Pool als Wunsch statt Pflicht“, „Umgebungssuche aktivieren“ oder „Reisezeitlimit entfernen“. Erst eine Nutzeraktion ändert die Kriterien. Interessengewichte allein sollen keine harten Filter aktivieren.

Unvollständige Kosten dürfen weiterhin keinen Billigkeitsbonus erzeugen. Behalte Preisstatus und Budgetstatus offen, wenn Kosten fehlen. Versuche bei diesem Auftrag nicht, fehlende Livepreise durch pauschale erfundene Hotel-/Flugpreise zu ersetzen.

## 7. Bedienbarkeit und Erklärungen

Verbessere das Suchformular gezielt: Interessen mit verständlichen Reglern oder Auswahlfeldern, geografische Auswahl mit unterstützten Werten, optionale Zieltypen „Stadt“, „kleiner Ort“, „See/Küste“, „Berge/Natur“ und „gemischt“. Gemischt ist Standard; wandern-/badeorientierte Suchen sollen passende nichtstädtische Ziele gut berücksichtigen, ohne Städte pauschal zu verbieten.

Während der Suche echte Fortschrittsinformationen anzeigen: „180 Ziele lokal bewertet“, „12 Ziele näher geprüft“, „5 Reiseideen gefunden“, „Unterkünfte im Umkreis werden gesucht“. Keine künstlichen Zahlen oder Prozentwerte. Bei Zeit-/Abfragelimit vorhandene Ergebnisse mit ehrlichem Abschlussgrund erhalten.

Zieltyp, Basisort, Interessenpassung, wichtigste Belege, Datenlücken und Umkreisbezug in Ergebnisliste/Details sichtbar machen. Verhindere, dass die einfache Nutzung in technischen Diagnosedetails untergeht; Diagnose separat aufklappbar halten. Suche muss abbrechbar bleiben, verspätete Ergebnisse dürfen keine neue Suche überschreiben.

## 8. Regressionstests und Abnahme

Ergänze aussagekräftige Tests mit geografisch passenden unterschiedlichen Fixtures statt demselben Hotelkatalog für jeden Ort. Netzwerkzugriffe von deterministischen Tests trennen.

Pflichttests:
1. Ein einzelnes Interesse Wandern liefert aus geeigneten Testdaten Ergebnisse.
2. Wandern + Baden + Feiern wird gewichtet, nicht versehentlich als harte UND-Verknüpfung behandelt.
3. Alle Interessen null ergeben eine gültige offene Suche.
4. Ein unbekannter Regionsname erzeugt eine konkrete Meldung; unterstützte Regionsaliase finden die richtigen Kandidaten.
5. Die ersten neun Ziele scheitern an Datenlücken, ein späterer Kandidat ist geeignet: adaptive Suche findet ihn innerhalb ihres Budgets.
6. Kleiner Ferienort hat lokal nur eine Unterkunft, im erlaubten Umkreis eine weitere: beide werden mit korrekter Lage angezeigt.
7. Grenzen und ausgeschlossene Gebiete werden auch bei Umkreissuche nicht umgangen.
8. Doppelte Quelleneinträge werden dedupliziert; verschiedene ähnlich benannte Unterkünfte bleiben erhalten.
9. Pool als Pflicht ohne Beleg führt zu verständlicher Diagnose und ggf. separat gekennzeichneten Ideen, nicht zu einer falschen Bestätigung.
10. Nur Zug mit maximal acht Stunden und ohne Fahrplandaten: keine behaupteten passenden Verbindungen, aber klare Erklärung statt stiller Leere.
11. Providerfehler eines Ortes verhindert andere Ergebnisse nicht; Abbruch, Zeitlimit und Abfragebudget werden korrekt durchgereicht.
12. Cache und neue Parser-/Katalogversionen verhalten sich konsistent, Quellenalter bleibt sichtbar.
13. Fehlende Preise erhalten keinen Rankingvorteil; optionale Ausgaben bleiben außerhalb des Budgets.
14. Verbesserte Rankings werden nicht von Hauptstädten oder mehrfachen Varianten desselben Gebiets dominiert, sofern ausreichend passende Alternativen vorliegen.
15. Startort-Aliase können nicht versehentlich den eigenen Ort als Urlaubsziel vorschlagen.
16. Bestehende gespeicherte Reisen lassen sich weiterhin öffnen und als PDF exportieren. Neue Gebietsdaten und Ergebnisstatus werden korrekt gespeichert; ggf. Migration testen.

Manuelle Abnahme im Desktop:
- Start Berlin, fünf Erwachsene, drei Zimmer, 2.000 EUR Gruppenbudget, Juli 2027, sieben Tage/sechs Nächte, Wandern/Baden/Feiern, zunächst ohne harte Zusatzfilter.
- Weitere Suchen: nur Wandern; Baden + Natur; Region Schwarzwald; gezielt kleine Orte; Vergleich mit aktivierten Pflichtmerkmalen und Reisezeitlimit.
- Bei verfügbaren Quellen mehrere nachvollziehbare unterschiedliche Vorschläge, darunter geeignete nichtstädtische Ziele. Mindestens ein vollständig recherchierter Vorschlag mit zwei realen Unterkunftsidentitäten und belegten passenden Aktivitäten am Ort oder im zulässigen Umfeld. Keine Zusage aktueller Unterkunftsverfügbarkeit ohne entsprechenden Anbieterbeleg.
- Null Treffer werden immer fachlich oder technisch erklärt. Wenn die genaue ursprüngliche Nutzerkonfiguration nicht rekonstruierbar ist, benenne das; verwechsle eine plausible Ursache nicht mit einem reproduzierten Fehler.
- Prüfe echte externe Quellen einmal in einem begrenzten separaten Live-Lauf und dokumentiere Datum, Eingaben, untersuchte Ziele, Abfragen, Ergebnisse und Grenzen. Fallbacks/offline Fixtures nicht als Live-Erfolg darstellen.

## Arbeitsweise und Lieferung

Beginne mit einem kurzen Diagnoseplan, untersuche die Ursachen und implementiere anschließend die Verbesserungen. Ergänze keine Tests, die lediglich die neue Implementierung abschreiben. Bewahre funktionierende Kosten-, Speicher-, PDF- und Abbruchlogik. Nutze bestehende Module, teile sie bei Bedarf verständlich auf; keine unnötige zweite parallele Suchmaschine.

Aktualisiere README, Quellen-/Abdeckungsdokumentation und PROJECT_LOG. Dokumentiere besonders: verifizierte Fehlerursachen, neue Suchstufen, Zielkatalog-Abdeckung, Grenzen von Umkreissuche und Datenqualität, getestete Fälle sowie weiterhin offene Preis-/Verfügbarkeitsfunktionen.

Liefere eine nutzbare Verbesserung der Desktop-Suche, eine verständliche Start-/Testanleitung und einen ehrlichen Abschlussbericht. Die Lösung ist nicht allein durch einen größeren Katalog oder das Entfernen aller Filter erfüllt: Die Suche muss nachweislich bessere passende Ziele finden und erklären können, warum einzelne Suchen keine bestätigten Treffer ergeben.
