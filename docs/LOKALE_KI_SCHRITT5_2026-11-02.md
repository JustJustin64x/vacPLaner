# Lokale KI – Schritt 5: Ortsentdeckung und kontrollierte Interessenbewertung

Prüfbericht vom **02.11.2026**. Schritt 5 ist im unten abgegrenzten Umfang implementiert und technisch abgenommen. Die optionale Ergänzung bringt unabhängig zugeordnete Aufenthaltsorte in dieselbe normale Reiseprüfung. **Eine allgemein bessere Suchqualität und ein tatsächlicher positiver Rankingbeitrag in den echten Vergleichssuchen sind nicht nachgewiesen.**

Die [Rohantworten, öffentlichen Prüfdaten, Messwerte und Fehlversuche](LOKALE_KI_SCHRITT5_2026-11-02.json) enthalten drei getrennte Kampagnen einschließlich des ersten Kleinorte-Zeitlimits. Modellfehler wurden nicht durch geänderte Erwartungen verdeckt. Öffentlich erzeugte Testreisen sind keine privaten gespeicherten Nutzerreisen.

## Bedienung und Ablauf

Unter **Details → Zusätzliche Zielideen mit lokaler KI prüfen** ausdrücklich **ja** wählen und die normale Suche starten. Standard **nein**. Normale Ergebnisse werden zuerst ausgegeben und bleiben während der Ergänzung nutzbar. Bis zu zwei zusätzliche Ergebnisse können über die normale gewünschte Trefferzahl hinaus erscheinen. Filtertreffer und offene Ideen bleiben getrennt.

Die breite normale Suche bewertet die räumlichen Vertreter aus dem bestehenden GeoNames-/OSM-Bestand. 852.761 Aufenthaltsorte und 202.509 Regionsobjekte blieben erhalten. Nach Entfernung der doppelten Reiseführeridentitäten enthält der kombinierte räumliche Katalog in diesem Lauf 34.494 Vertreter. Es gibt keinen zweiten KI-Kleinkatalog. Das Modell erhält bis zu zwölf weitere Vertreter außerhalb der gesamten normalen vertieften Liste. Es wählt aufrufgebundene kurze Referenzen oder nennt andere konkrete Orte. Programmcode löst freie Namen exakt gegen den vollständigen importierten Landesbestand auf; mehrdeutige Namen, falsche Regionen, Regionen statt Aufenthaltsorten und ungeprüfte Referenzen werden zurückgehalten. Kein unscharfer Abgleich. Unaufgelöste Landschaften werden nicht in erfundene Übernachtungsorte umgewandelt; bestehende konkrete Basisorte können ausgewählt werden.

Europa, Länder, Regionen, Ausschlüsse, Zieltyp und Radius werden unabhängig erneut geprüft, auch direkt vor der Integration in den Suchkern. Danach gelten dieselben Unterkunfts-, Verkehrs- und Zeitprüfungen wie zuvor. Fehlende Pflichtausstattung/Zugzeiten werden nicht zu erfüllten Bedingungen. Modellbekanntheit liefert keinen Bonus.

Eine bestehende Integrationslücke wurde an ihrer Ursache behoben: Der Reiseführerpunkt für Tallinn lag knapp außerhalb der bisherigen 800-m-Zusammenführung. Nun werden genau ein identischer normalisierter Name/Alias im selben Land und weniger als 3 km Abstand verlangt. Mehrere passende Identitäten werden nicht per erstem Treffer zusammengeführt. Doppelte identische Aliasse werden bei der Identitätszählung entfernt. GeoNames-Koordinaten und stabile IDs bleiben erhalten; die verknüpfte Reiseführerseite erhält dadurch noch keine unabhängig bestätigten Sachbehauptungen. Quellenbelege müssen weiterhin die strengere Wikidata-/GeoNames-Prüfung bestehen.

## Feste Grenzen und Quellen

| Teil | Grenze |
|---|---|
| Lokale Modellaufgaben pro Suche | ein zusätzlicher Versuch, maximal 20 s einschließlich gemeinsamer Warteschlange |
| Öffentlicher Modellkontext | höchstens zwölf weitere Ortsvertreter, öffentliche Gebiete/Zieltyp und gewählte Interessen |
| Ideen / lokale Namensauflösungen | höchstens vier / vier |
| Referenzwahl, Modell und lokale Auflösung zusammen | maximal 35 s, zusätzlich am Hauptrestbudget begrenzt |
| Zusätzliche regulär vertiefte Orte | höchstens zwei |
| Neue sichere Quellenprüfung | höchstens ein Ort, sechs HTTP-Transaktionen inklusive Robots/Redirects, 35 s |
| Gesamte neue Phase | innerhalb Zeit- und HTTP-Restbudget der normalen Suche |
| Modell-Parallelität | vorhandener gemeinsamer lokaler Client, eine Aufgabe je Endpunkt |

Quellen bleiben die vorhandenen GeoNames-/OSM-Identitäten und die Schritt-4-Schicht für deutsche Wikivoyage-Artikel mit verknüpfter Wikidata-Identität und Länder-ISO-Code. Bekannte Reiseführerlinks werden weiterverwendet; ansonsten leitet allein Programmcode einen möglichen Artikeltitel aus dem unabhängig aufgelösten Namen ab. Das ist ein gezielter Abrufversuch, keine allgemeine Websuche. 404 ist eine Datenlücke. Keine neuen Suchdienste oder Identitäts-APIs, Modelle oder flächigen Downloads.

Öffentliche HTTPS-Allowlist, DNS-/TLS-Bindung, Redirect-, Robots-, Größen- und Rate-Limit-Regeln aus Schritt 4 bleiben wirksam. Der normale Quellenadapter erhält eine neu erratene Seite nur nach erfolgreicher sicherer Identitätsprüfung aus demselben bereits abgerufenen HTML im vorhandenen Parser-Cache. Ein ausschließlich extrahierter Cacheeintrag löst keinen ungeschützten erneuten Abruf der geratenen URL aus. Rohseiten werden nicht dauerhaft archiviert.

Die bestehende separate Preisphase hat weiterhin ihr eigenes historisches Budget von 32 Abfragen. Sie wurde nicht erweitert und in sämtlichen Vergleichsprofilen mit `price_targets=0` deaktiviert; regionale Zusatzabfragen ebenfalls 0. Die neuen Teilbudgets werden nicht unbemerkt zusätzlich zum Hauptbudget vergeben.

## Beleg- und Bewertungsvertrag

Vorab festgelegt in [KI_ORTSENTDECKUNG_VERTRAG.md](KI_ORTSENTDECKUNG_VERTRAG.md). Nur vollständige strukturierte `museum`-/`gallery`-/`castle`-Einträge der Gruppen `see`/`do` dürfen ein Kultursignal beitragen. Ziel-, Quellen-, Objekt-, Länder- und Koordinatenzuordnung, Originalwerte, Konflikte und Quellenalter werden außerhalb des Modells geprüft. Maximale Nähe: 3 km Luftlinie, zusätzlich der kleinere eingestellte Aktivitätsradius beziehungsweise 2 km ohne Umgebungssuche. Sichtbare permanente Schließungen/Konflikte sperren das Objekt; uninterpretierbare Aussagen erhalten keine neue Wirkung.

Nur tatsächlich innerhalb der letzten 30 Tage beobachtete Quellenstände, keine Zukunftszeitpunkte oder umetikettierten Cacheabrufe. Das belegt keine aktuelle Öffnung und ersetzt kein unbekanntes Veröffentlichungsdatum. Öffnungszeiten/Zugang bleiben Quellenbehauptungen. Veranstaltungen, Preise, Baden, Wandereignung, Ruhe und Nachtleben erhalten über diesen neuen Pfad keinen Beitrag.

Gleiche Objekt-/Wikidata-IDs oder derselbe normalisierte Name im 100-m-Umkreis zählen einmal, einschließlich bestehender OSM-/Reiseführerbelege. Gemeinsame Herkunft ist keine unabhängige Mehrfachbestätigung. Höchstens drei neue Identitäten, Kultursignal höchstens 0,25; bestehende Signale werden nicht aufsummiert. Die gesamte Interessenpassung steigt um **höchstens absolut 0,05**. Mehrere Interessen werden über die vorhandene Gewichtung und Kombinationsprüfung bewertet. Textlänge, Stadtbekanntheit und Quellendubletten sind kein Qualitätsmaß.

Der Bewertungsnachweis speichert vorher/nachher, tatsächliche Änderung, angenommene Objektidentitäten und Ablehnungsgründe. Wiederholte Auswertung derselben Arbeitskopie kann den Bonus nicht akkumulieren. Ursprüngliche Quellenbelege aus Schritt 4 werden nicht nachträglich zu unabhängig bestätigten Tatsachen umetikettiert; der neue Beitrag steht separat. Preise, Pflichtkriterien, Reisezeit und Komfort bleiben unter dem bestehenden Programmcode.

## Echte Vergleichssuchen

Alle Arme: Startort Berlin, öffentliche synthetische Standardkriterien, zwei Erwachsene/ein Zimmer, Juli 2027, Zug, zehn normale vertiefte Kandidaten, drei gewünschte Filtertreffer, offene Ideen sichtbar, maximal **40 HTTP / 120 Sekunden**. Normal zuerst, KI danach, gemeinsamer warmer Cache je Profil, frischer temporärer Cache für jedes Profil. Tatsächliche Abfragen und Modell-/Rechercheumfang unterscheiden sich. Daher kein kausaler Geschwindigkeits- oder Qualitätsvergleich. Die normale Suche führt gegebenenfalls schon vorhandene modellierte Aktivitätszugänge aus; neue Quellenprüfungen bleiben in denselben 40 Abfragen.

Nur das frühere Estland-Kulturprofil diente der Entwicklung. Vier weitere Profile waren vor der Kampagne festgelegt und wurden nicht für eine Promptnachjustierung verwendet. Die Wiederholungen sind keine unabhängigen Qualitätsstichproben. Endgültige Messung nach der Tallinn-Korrektur:

| Profil | Sekunden normal / KI | HTTP normal / KI | Ideen / aufgelöst / verworfen | zusätzliche Ergebnisse |
|---|---:|---:|---:|---|
| culture_nightlife | 4.26 / 18.20 | 2 / 2 | 4 / 3 / 1 | Rakvere, Haapsalu |
| hiking_nature_held_out | 5.64 / 18.72 | 0 / 2 | 4 / 1 / 3 | Leskovec |
| bathing_held_out | 3.37 / 11.09 | 0 / 0 | 4 / 0 / 4 | keine |
| small_places_held_out | 3.36 / 13.46 | 1 / 2 | 4 / 3 / 1 | Viiratsi, Rapla |
| geographic_subregion_held_out | 14.41 / 23.05 | 3 / 0 | 4 / 0 / 4 | keine |

„Aufgelöst“ kann wegen der Zweierobergrenze höher als „vertieft“ sein. Die JSON-Diagnose nennt nicht vertiefte Ideen, tatsächliche Treffer und offene Ideen einzeln. Referenz-/Namenswidersprüche und ungeeignete Regionsvorschläge bleiben verworfen. Das erste Kleinorte-Profil lief beim Modell ins Zeitlimit; spätere Rohantworten und frühere Fehlschläge sind getrennt erhalten.

In früheren Kampagnen wurden Kuressaare (`geonames:590939`) und Rakvere (`geonames:589165`) zusätzlich zu Pärnu/Tallinn/Tartu regulär aufgenommen. Nach der Katalogkorrektur lieferte die endgültige Kampagne stattdessen Rakvere und Haapsalu (`geonames:592225`). Alle drei gehören nicht zum kleinen fest eingebauten Reiseführer-Beispielbestand. Insgesamt wurden im letzten Lauf fünf zusätzliche Filtertreffer aus drei Profilen aufgenommen; sieben der 20 Ideen waren unabhängig auflösbar, zwei davon wurden wegen der Vertiefungsobergrenze nicht weiter geprüft, 13 verworfen. Die vollständigen Kriterien, Quellenstände, weiteren aufgenommenen Orte und Scores stehen im JSON. „Filtertreffer“ bedeutet weiterhin keine bestätigte Buchbarkeit, Belegung oder Budgetvollständigkeit.

Die Quellenversuche für zusätzliche Orte lieferten keine neuen auswertbaren Belege. Daraus resultiert in diesen Vergleichssuchen **kein neuer Quellen-Rankingbonus**. Angenommene Ortsidentität, vorhandene lokale Interessenmerkmale und neu geprüfte Webseitenbelege werden getrennt ausgewiesen.

## Getrennte tatsächliche Quellenkontrollen

Diese Komponentenprüfungen zählen nicht als zusätzliche Suchergebnisse und besitzen eigene ausdrücklich ausgewiesene Budgets (sechs sichere Quellenabfragen, anschließend höchstens sechs normale Planungsabfragen). Sie zeigen, dass Quellen weiterhin auswertbar sind und stärkere Identitätsprüfungen auch reale Seiten zurückhalten:

- Bled: 2 Quellenfelder, 5 sichere HTTP-Transaktionen. 1 neue Kulturidentitäten angenommen; Interessenänderung 0.000.
- Innsbruck: 0 Quellenfelder, 3 sichere HTTP-Transaktionen. GeoNames-Identität widerspricht der Recherche.
- Tallinn: 8 Quellenfelder, 3 sichere HTTP-Transaktionen. 3 neue Kulturidentitäten angenommen; Interessenänderung 0.000.
- Kuressaare: 0 Quellenfelder, 1 sichere HTTP-Transaktionen. Quelle HTTP 404; keine Sperrumgehung.
- Leskovec: 0 Quellenfelder, 1 sichere HTTP-Transaktionen. Quelle HTTP 404; keine Sperrumgehung.

Bled liefert einen technisch angenommenen Kulturbeleg, aber keinen Bewertungsanstieg bei bereits ausgeschöpfter Kulturpassung. Ein isolierter reproduzierbarer Fixture-Fall mit fehlender Kulturabdeckung erhöht die Interessenpassung um exakt 0,05 bei unveränderter Kostenberechnung. Dieser künstliche Nachweis wird nicht als positive Rankingwirkung einer tatsächlichen Vergleichssuche ausgegeben.

Separate Kontrollabrufe gegen den alten Reiseführerkatalog (ohne GeoNames-ID) für Bled/Innsbruck/Tallinn lieferten zwei/acht/acht Felder. Im kombinierten Bestand wird Innsbruck wegen widersprüchlicher GeoNames-Zuordnung strenger zurückgehalten. Die ID-Prüfung wurde deshalb ausdrücklich nicht gelockert. 404-Versuche und Ablehnungen stehen mit Herkunft im JSON; fehlende Belege bedeuten kein fehlendes Angebot.

## GUI, Speicherung und Fehlerverhalten

Echter normaler Tk-Suchworker mit KI: **17.347 s**, 682 Ereignis-Callbacks, längster Abstand **0.519 s**. Zusätzliches Ergebnis ausgewählt, Herkunft in den Details angezeigt und über ausdrückliches Speichern samt Quellenmetadaten wieder geladen.

Bei vollständig gestopptem eigenen KI-Dienst: normale Suche **4.838 s**, aktivierte optionale Suche **3.614 s**; beide beendet und mit regulären Ergebnissen. Echter Abbruch: **0.595 s** bis eigener Worker beendet. UI bleibt bedienbar, kann beim Bestandsladen/Verarbeiten jedoch kurz stocken; gemessene Callbackpausen werden nicht als völlig ruckelfrei beschrieben.

Neue Suche, Abbruch und Schließen invalidieren alte Antworten über die vorhandene Generation. Änderungen an Kriterien einer laufenden KI-erweiterten Suche brechen sie ebenfalls ab. Reproduzierbare Desktoptests prüfen verspätete Antworten und Anzeige-/Speicherverhalten. Bereits gespeicherte Reisen werden nicht automatisch geändert; alte Formate laden mit deaktivierter KI-Option. Arbeitskopie, extrahierter HTTP-Cache und dauerhaft gespeicherter Reise-Snapshot bleiben getrennt. Erklärungs-Cacheschlüssel reagieren auf geänderten Belegstand. Neue kanonische Kulturbelege können im bestehenden kontrollierten Erklärungsvertrag als Quellenzuordnung erscheinen, ohne Öffnungszusage.

Produktive Suchdiagnosen speichern keine Rohprompts oder ursprünglichen Wunschtexte. Die KI erhält keine genaue Startadresse, Preise, Datenbank oder Reisehistorie. Die realen Nutzerreisen wurden nur lesend fingerprinted; Anzahl und Hash blieben unverändert. Ein vorhandenes Modell, keine Downloads; eigener Dienst wiederhergestellt und Modell entladen.

Visuelle Grenze: Die normale Startansicht wurde über CUA gesehen. Tk-Inhalte waren nicht im Zugänglichkeitsbaum erreichbar; die Detailauswahl ließ sich auf diesem Weg nicht zuverlässig bestätigen. Ein weiterer Abruf scheiterte mit ScreenCaptureKit -3812/Server -10005. Deshalb **keine vollständige manuelle Klickabnahme**. Die echte automatisierte Tk-Abnahme und ihre Messwerte sind davon getrennt.

## Regression und Reproduzieren

**316 Tests bestanden**: 277 bisherige plus zehn Kandidaten-/Identitätstests, 14 Bewertungstests, acht normale Integrationstests, vier lokale HTTP-Vorbereitungstests und drei Desktoptests. Enthalten: erfundene/gleichnamige Orte, exakte Auflösung außerhalb kleiner Beispiele, Ausschlüsse/Europa/Typ/Radius, Pflichtverletzungen/offene Angaben, Referenzen, Dubletten/gemeinsame Herkunft, Sättigung und mehrere Interessen, Negationen/Zeiten, unbelegte Themen, unbekannte Preise, Abbruch, Restbudgets, Cache, Speicherung und Schritte 2–4. HTTP-Fixtures ersetzen ausschließlich den Testtransport, keine Produktionsschutzschalter. `compileall` und `git diff --check` bestanden.

```bash
.venv/bin/python -m unittest discover -s tests -p 'test_*.py'
.venv/bin/python scripts/verify_candidate_discovery.py --live
# Optional sichtbare funktionale Tk-Prüfung:
.venv/bin/python scripts/verify_candidate_discovery.py --live --visible
```

Der Live-Verifier verlangt einen bereits gestarteten nachweislich eigenen Dienst und installiert nichts. Er verwendet temporäre Reisen, zeichnet nur seine öffentlichen synthetischen Prüfeingaben auf und stellt den Dienst nach Offlineprüfungen wieder her. Reale Quellen-/Modellantworten dürfen bei Wiederholung anders ausfallen. Er prüft technische Sicherheits-/Integrationskriterien; ein erfolgreiches Gesamtergebnis bedeutet nicht, dass jede rohe Modellidee fachlich korrekt war.

## Verbleibende Grenzen

Die KI liefert häufig keine verwendbare Ergänzung, falsche Referenz-/Namenspaare oder ungeeignete Regionsangaben. Modell- und Quellenzeitlimits können Zusatzideen vollständig verhindern. Allgemeine Websuche, beliebige Webseiten und sichere Wander-/Bade-/Öffnungszusagen sind nicht implementiert. Die begrenzte Quellenabdeckung ist besonders für kleine Orte lückenhaft. Neue Bewertung bleibt auf konservative Kulturhinweise beschränkt; ein allgemeiner Qualitätsgewinn wurde nicht nachgewiesen. Bereits bekannte Grenzen bei Bildern, Freitext, datierten Preisen und vollständiger GUI-Sichtprüfung bleiben offen.
