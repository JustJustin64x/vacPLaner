# Lokale KI – Schritt 6: Prüfung der bestehenden Preisrecherche

Prüfbericht vom **02.11.2026**. Schritt 6 ist im unten abgegrenzten Umfang **technisch implementiert und abgenommen**. Die vorhandenen Preisprovider und die KI-Infrastruktur aus Schritten 1–5 werden weiterverwendet. **Ein messbarer Zuwachs verifizierter Preisbestandteile oder vollständiger Angebote durch KI ist in der öffentlichen Kampagne nicht nachgewiesen.**

[Strukturierter Prüfbericht](LOKALE_KI_SCHRITT6_2026-11-02.json) mit ursprünglichen Antworten, öffentlichen Testanfragen, Fehlversuchen, Herkunft und Messwerten. Die ältere unvollständige Kampagne bleibt getrennt erhalten. [Vorab dokumentierte Untersuchung und Grenzen](ANGEBOTSANALYSE_VERTRAG.md).

## Ausgangssituation und tatsächliche Architektur

Vor Beginn README, Projektprotokoll, Quellen-/Lizenzhinweise, Berichte der KI-Schritte 1–5, Produktionsprovider, Kosten/Ranking, HTTP/Identität, GUI, Persistenz/PDF und relevante Tests mit dem Code abgeglichen. Der Code ist maßgeblich; die historische Quellen-Dokumentation „kein Livepreisprovider“ war überholt.

Der bestehende Ablauf bleibt: `DiscoveryService → OpenTravelProvider.research_offers → OfferResearchService → vorhandene Provider → CostItem/CostService/RankingService → GUI/SQLite/PDF`. Der Core importiert keine Ollama-, HTTP- oder Tk-Komponenten. Der Aufgabenservice `OfferAnalysisService` verwendet den vorhandenen **LocalModelClient**, seine zentrale Config, Ausgabevalidierung, Timeout-/Abbruchmechanismen und das gemeinsame Endpunkt-Lock. Keine neue Clientklasse, Runtime-Verwaltung, Modellinstallation, Cloud oder globale Ollama-Konfiguration. Die kleine Änderung im bestehenden Client betrifft ausschließlich die Bereinigung bereits beendeter curl-Prozesse.

| Quelle | Bereits vorhandene Prüfung und Preisart | Aktueller Livebefund |
|---|---|---|
| Smoobu / geprüfte Innsbrucker Wohnungen | Eine Ferienwohnung, feste erlaubte Objektidentitäten, genaue Reise-/Personenparameter, Nächte, Verfügbarkeit und Summe aller Preisbestandteile. Reinigung enthalten. Kein allgemeines Hotel-/Mehrzimmerangebot. | Robots antwortet mit HTML; sicherer Abruf gesperrt. Historische Preise werden nicht als heute geprüft ausgegeben. |
| RegioJet | Datierte zweite Klasse, Erwachsene ohne Rabattkarten, tatsächliche Detailtarife/Plätze, Stadtidentitäten und getrennte Hin-/Rückfahrt. Gruppentarife einmal summiert. | Erneut echte datierte Angebote für Prag–Brünn; 33,60/42 EUR für zwei beziehungsweise 84/105 EUR für fünf Erwachsene zum Abrufzeitpunkt. Keine Reservierung. |
| Offizielle Eintrittstarife | Vier bestehende konkrete Einrichtungen; Eintritt optional außerhalb des Hauptbudgets, keine datierte Ticketverfügbarkeit. | In dieser Kampagne Goldenes Dachl und Burg Bled erfolgreich gelesen; keine neue aktuelle Liveabnahme aller vier Quellen behauptet. |
| Flug / Suchlinks / Reiseführerpreise | Flugzugang nur Diagnose; Links sind kein Abruf-/Angebotsnachweis. Allgemeine Preise kein passender Reisegesamtpreis. | Unverändert keine bestätigten Flug-/allgemeinen Hotelpreise. |

Die Ausgangslogik konnte bereits mit Decimal rechnen, Personen/Zimmer/Nächte berücksichtigen, Reinigung innerhalb eines Gesamtbetrags belassen, die beiden Richtungen getrennt prüfen und unbekannte Kosten aus der Budgetfreigabe ausschließen. Das wurde weiterverwendet statt erneut implementiert.

## Nachgewiesene Schwachstellen und Änderungen

1. Preisadapter verwendeten den älteren PublicHttpClient mit automatischen Redirects, ohne die strengere öffentliche DNS-/TLS-Bindung und Robots-Allowlist. Standard-Preisabrufe verwenden jetzt die vorhandene ResearchHttp-Schicht. Einbettungen und Tests besitzen weiterhin ihre explizite Transportnaht, keinen produktiven Unsicher-Modus. Die bereits integrierten Quellen erhalten eng begrenzte Hosts/Pfade/GET-Parameter und öffentliche EUR-/Sprach-/Versionsheader. Weder neue Scraper noch zusätzliche Anbieter.
2. Gemeinsame fachliche Angebotsklassifikation und strukturierte Lücken fehlten. OfferQuality prüft Parameter, tatsächliche Preisbasis, Zeitraum/Nächte, Gruppe/Einheiten, Kapazität versus Verfügbarkeit, Währung, Gebühren, Frische und Widersprüche. Alte, allgemeine und unpassende Angebote werden nicht zu gültigen Gesamtsummen. Gleichzeitig beobachtete abweichende Preise derselben ID/Parameter/Tarif-/Quellenzeitidentität bleiben Konflikte; unterschiedliche Tarife oder spätere Preisstände sind kein automatischer Konflikt.
3. Gebühren konnten ohne gemeinsame Identitätsprüfung mehrfach angesetzt werden. Enthaltene, optionale, zusätzliche und unbekannte Bestandteile werden getrennt. Gleiche Gebühren-ID beziehungsweise normalisierte Bezeichnung zählt einmal; abweichende Werte sperren Bestätigung. Unklare Gebührenbasis oder Fremdwährung ohne bestehende verlässliche Umrechnung bleibt unbekannt. Keine neue FX-Funktion. Die bekannte enthaltene Reinigung wird nicht erneut addiert. Fehlende Pflichtkosten und ungeklärte Gebührenvollständigkeit bleiben sichtbar; kein Nullbetrag als Ersatz.
4. Das Veralten einer historischen Angebotsvariante konnte einen frischen Preis derselben ID ebenfalls entwerten. Nun wird jeder Preisstand anhand seiner eigenen Quellenzeit/Gültigkeit geprüft. Auch ohne Ablaufdatum bleibt ein normaler datierter Preis nach zehn Minuten nicht unbegrenzt frisch; fehlerhafte/fehlende Zeitangaben sind konservativ. Optionale veröffentlichte Eintrittstarife behalten ihre getrennte Tagesfrist und bleiben undatiert.
5. RegioJet-Stadtauflösung wählte den ersten Namens-/Aliastreffer. Mehrere unterschiedliche Anbieteridentitäten werden nun zurückgehalten. Sitzplatzzuordnung wird anhand tatsächlicher Verbindungsabschnitte bezeichnet; eine feste Zuordnung ist keine zusätzliche unbelegte Gebühren-/Buchungszusage. Ein ausdrücklich vorhandener, aber nicht interpretierbarer Zuschlag wird als Lücke geführt.
6. Bedingungen, Leistungsangaben und Preisstellen erhalten begrenzte Originalnachweise mit Angebots-/Quellen-ID und Fundstellenpointer. Das Modell kann diese aufrufgebunden auswählen; es setzt keine Reise-/Kostenwerte. Quellenbehauptungen bleiben von unabhängig geprüfter technischer Zuordnung getrennt.
7. Bei frühen Prozess-Abbruchpfaden werden auch schon beendete curl-Prozesse vollständig ausgelesen und ihre Pipes geschlossen; ein expliziter Race-Regressionstest prüft dies am vorhandenen Client. Warteschlange, Endpoint und Modell bleiben unverändert.

## Fundstellen- und Modellvertrag

Adapter erzeugen höchstens zwölf vollständige Felder je Angebot, höchstens 400 Zeichen pro Feld. Zu lange Felder werden ausgelassen, nicht vor einer entscheidenden Einschränkung abgeschnitten. Beispiele: Preis-/Gebührenfelder der tatsächlich zugeordneten JSON-Antwort, Kapazität, Nächte, konkrete Ausstattungsbezeichnungen sowie vollständige Storno-/Umbuchungsbedingungen. Die API-Fundstellen besitzen JSON-Pointer; offizielle Tariftexte einen bezeichneten Selektornachweis. Beide Richtungen behalten jeweils ihren ursprünglichen Abrufzeitpunkt.

Eine angenommene Information speichert stabile Angebotsidentität, Quellen-ID/URL, ursprüngliche Fundstelle und Quote, tatsächlichen Abruf, Wert, Einheit und deterministischen Validierungszustand. Veröffentlichungsdatum bleibt unbekannt, wenn die Quelle es nicht ausdrücklich strukturiert liefert. Abrufzeit ersetzt es nicht.

Das Modell sieht maximal vier Angebote und zwölf vorgeprüfte Ausschnitte insgesamt, dazu ausschließlich tatsächlich gewünschte/erforderliche Leistungen. Keine Privatadresse, Personennamen, Reisehistorie, vollständigen Snapshots oder Datenbankinhalte. Produktive Diagnosen speichern keine Rohprompts. Öffentliche Modell-Testnachrichten werden ausschließlich vom ausdrücklichen Abnahmeskript aufgezeichnet.

```json
{"selections":[{"offer_ref":"A1O1","source_ref":"A1S1","field":"condition"}]}
```

Die kurzen Referenzen gelten nur für den jeweiligen Aufruf. Zusätzliche Werte, Summen, URLs oder Textfelder sind verboten. Unbekannte, doppelte, fremde, veränderte und falsch kategorisierte Referenzen werden verworfen. Programmcode prüft Quellenhash, Angebotszuordnung, Quellenzeit, Originalwerte, Datentyp, Einheit und erlaubte Aussageart erneut. Preis-/Gebührenbeträge werden ausschließlich mit vorhandener Geldlogik normalisiert. Nacht-/Personen-/Zimmerbasis und „ab“ bleiben getrennte Angaben; die neue freie Quellenstellenanalyse rechnet daraus keine zusätzlichen verbindlichen Preise.

Eine Leistungsstelle „Frühstück optional“ wird niemals „enthalten“. „Pool nicht enthalten“ bleibt ausgeschlossen. Allgemeine Kapazität ist keine bestätigte Belegung. Unverstandene Storno-/Umbuchungstexte bleiben wörtliche **Quellenhinweise**, keine kostenlose Stornierungszusage. Widersprüche und fehlende Pflichtangaben werden vorrangig deterministisch geprüft; ein zusätzlicher Modellaufruf für einfache Lücken wäre kein unabhängiger Nachweis. Eingeschleuste Anweisungen können weder URLs, Rechte noch weitere Modell-/Werkzeugaufrufe erzeugen. Das ist ein kontrollierter Vertrag, keine allgemeine Garantie für beliebige fremde Texte.

## Qualitätszustände, Kosten und Ranking

Die Oberfläche zeigt verständliche deutsche Zustände: Anfragebezug geprüft, teilweise geprüft, Richtwert, widersprüchlich, veraltet, unpassend oder unbekannt. Selbst der beste Zustand ist keine Buchungszusage. Bezug, Geltung, Personen, Einheiten/Richtungen, Gebühren, Abruf und offene Bedingungen stehen bei den einzelnen Angeboten.

Aktuelle technisch passende Teilpreise dürfen weiterhin als Teilkosten erscheinen. Unbekannte Pflichtkosten, ungeklärte Belegung/Pflichtleistungen oder nicht zugeordnete Richtungen verhindern eine vollständige Budgetfreigabe. Optionale Verpflegung/Aktivitäten bleiben nach bestehender Produktlogik außerhalb des Hauptbudgets. Fremdwährungen werden ohne ausreichend geprüfte Umrechnung nicht addiert. Neue Quellenhinweise ändern keine bestehenden Preise oder Ausstattungsmerkmale automatisch. Es gibt **keinen KI-Bonus und keine neue Rankingformel**; nur begründet zusätzliche offene Kosten können die bestehende Abdeckung/Bewertung verändern.

Veröffentlichte Eintrittstarife werden weiterhin separat angewendet und als undatierte optionale Preise angezeigt. Sie dürfen nicht durch den neuen Prüfer versehentlich als datierte Gesamtangebote ausgefiltert oder im Hauptbudget aufgenommen werden.

## Sicherer Abruf, Nachrecherche und Budgets

- Vorhandene HTTPS-Allowlist, alle öffentlichen DNS-Adressen, TLS-Bindung/Peer-Prüfung, manuelle Redirects, Robots und Rate-Limits bleiben im bestehenden ResearchHttp. Keine Datei-/Loopback-/Privatziele, Proxys, Zugangsdaten, Buchungs-/Kontorouten oder fremde Anweisungen.
- Maximal 2 MB je Dokument, Robots 128 KB, höchstens drei Dokument-Redirects, kleinere bestehende Connect-/Abruflimits (4/18 s) und mindestens 1,1 s Hostabstand. Fehlende/nicht auswertbare Robots-Regeln führen zum Abbruch. Keine Umgehung mit dem älteren Client.
- Automatische Preisphase bleibt maximal 32 HTTP-Transaktionen im Suchrestbudget. Manuelle/Exportaktion bleibt gemeinsam maximal 40/600 s. Robots und zusätzliche Abrufe zählen mit.
- Neue Nachprüfung: höchstens eine unterstützte Kategorie nach einem tatsächlich technischen temporären Quellenfehler, maximal vier HTTP und 15 s innerhalb desselben Kontextes. Keine Wiederholung bei Robots/Sperrantwort, falscher Identität, ungültigen Werten, „nicht unterstützt“ oder bloß fehlenden Angeboten. Fehlende Informationen ohne vorhandenen zulässigen Zugriff bleiben offen. **In der Livekampagne gab es keinen geeigneten Anlass: null tatsächliche Nachprüfungen, null dadurch ergänzte Angaben.** Erfolgreicher, begrenzter und abgebrochener Nachprüfungsweg sind reproduzierbar mit Fixtures geprüft.
- Maximal ein Modellversuch/15 s je gemeinsamem Preis-Kontext, auch bei mehreren Zielen/Terminproben; die vorhandene Modellwarteschlange ist eingeschlossen. Kein automatischer Dienststart, kein Cloud-Fallback, keine Downloads.
- Sitzungscache höchstens 32 Analysen, Schlüssel über relevante Angebots-/Quelleninhalte, Zeit und Kriterien. Cache-Nutzung ist keine neue Anbieterprüfung. Keine vollständigen Webseitenarchive im Snapshot. Statische RegioJet-Orte sieben Tage, Robots 24 Stunden; aktuelle Preise werden je Aktion neu abgefragt, der begrenzte In-Memory-Transport hält seinen tatsächlichen Abrufstand.

Smoobu-Blockade ist eine bewusste Sicherheitsgrenze gegenüber dem historischen Zugang: `robots.txt` HTTP 200, Inhaltstyp HTML, kein anschließender Angebotsabruf. RegioJet-API-Robots HTTP 404 und erlaubte lesende GETs; offizielle RegioJet-Startseite/Robots und die verknüpfte Innsbrucker Anbieter-Webseite wurden begrenzt geprüft. Das Recherche-Webwerkzeug konnte diese offiziellen Seiten nicht öffnen; die genannten tatsächlichen Ergebnisse stammen aus dem bestehenden sicheren Produktions-Transport, nicht aus erfundenen Suchergebnissen.

## Öffentliche Vergleichskampagne

Sechs öffentliche synthetische Anfragen: Städtereise/Hotel und Bahn, längerer Aufenthalt, Mehrzimmeranfrage mit unvollständigen Unterkunftspreisen, mehrere Verkehrsmittel, Pflicht-/Wunschausstattung und unzureichende Quellenlage. Reale Anbieterantworten sind von aufgezeichneten/synthetischen Modellfällen getrennt. Keine privaten Nutzerreisen verändert.

Verglichen wurden **aktuelle sichere Adapter ohne/mit KI**, jeweils maximal 32 HTTP/120 s, normal zuerst. Kein Rückfall auf den früheren ungeschützten HTTP-Zugang für einen scheinbar besseren Vergleich. Kein Livepreis-Cache, statischer Orts-/Robots-Cache im zweiten Arm teilweise warm. Unterschiedliche tatsächliche Abrufe und Laufzeiten sind deshalb kein kausaler Geschwindigkeits-/Qualitätsvorteil der KI.

| Fall | Sekunden normal / KI | HTTP normal / KI | Angebotsobjekte normal / KI | ausgewählte Fundstellen | KI-Ergebnis |
|---|---:|---:|---:|---:|---|
| city_rail | 11.16 / 24.32 | 9 / 7 | 2 / 2 | 0 | Zeitlimit/Antwort verworfen |
| long_stay | 3.39 / 2.10 | 5 / 2 | 1 / 1 | 1 | Fundstellen ausgewählt |
| incomplete_hotel | 3.03 / 1.85 | 4 / 1 | 1 / 1 | 1 | Fundstellen ausgewählt |
| multiple_modes | 11.82 / 24.90 | 9 / 7 | 2 / 2 | 0 | Zeitlimit/Antwort verworfen |
| amenity_requirements | 3.46 / 1.86 | 5 / 2 | 1 / 1 | 1 | Fundstellen ausgewählt |
| insufficient_sources | 1.54 / 0.00 | 2 / 0 | 0 / 0 | 0 | keine Fundstellen |

Die konkreten Reisezeiten, Daten, Gruppen und vollständigen Zustände stehen im JSON. Angebotssummen 33,60/42 bzw. 84/105 EUR wurden vom bestehenden RegioJet-Adapter aus zwei Gruppentarifen berechnet; nicht vom Modell und nicht nochmals mit Personen multipliziert. Insgesamt vier verschiedene passende datierte Tarifkombinationen, je Arm wiederholt beobachtet. Alle behalten offene Reisebestandteile, insbesondere Unterkunft/Zubringer; **null vollständig belegte Reisegesamtpreise**. Offizielle Eintrittstarife sind in der Tabelle als Angebotsobjekte gezählt, ausdrücklich keine datierten Buchungsangebote. Fehlende Kategorien sind weiterhin strukturierte Quellenstatus, nicht „keine Datenlücken“ bei null Angebotsobjekten.

Zwei von fünf tatsächlich ausgeführten öffentlichen Modellversuchen liefen in das 15-s-Limit. Die anderen drei wählten jeweils genau einen bereits bekannten offiziellen Tarifhinweis; der sechste Fall hatte keine Fundstellen und brauchte keinen Modellaufruf. **Neue verifizierte Geldbestandteile: 0. Neu vollständig passende Gesamtangebote durch KI: 0. Aufgelöste reale Widersprüche durch KI: 0.** Die vorhandenen Tarifbedingungen waren bereits in den Anbieterantworten vorhanden. Auswahl/Darstellung derselben Information ist kein neuer Preisbeleg. Rohfehler bleiben im Bericht.

Die endgültigen zusätzlichen Frische-/Darstellungsregeln wurden außerdem deterministisch gegen die gespeicherten tatsächlichen Angebote zur ursprünglichen Prüfzeit erneut ausgewertet. Diese getrennte Nachauswertung hat null HTTP-/Modellaufrufe und wird nicht als frische Internetprüfung ausgegeben; ursprüngliche Liveantworten bleiben unverändert. Sie ergänzt insbesondere die ausdrückliche unbekannte Datums-Gültigkeit veröffentlichter Tarife.

## Modellprüfungen und Ressourcen

Zwei echte lokale Modellaufrufe mit aufgezeichneten öffentlichen Smoobu-Antworten unter künstlicher Prüfuhr: zwölf beziehungsweise elf Fundstellen angenommen, etwa 14,880/14,540 s. Der zweite Fall enthielt eine **synthetische** Aufforderung zum privaten Abruf/erfundenen Preis. Keine Werkzeuge, Abrufe oder neuen Reise-/Geldwerte wurden dadurch erzeugt. Das sind Regressionen mit historischen Antworten, keine heutigen Smoobu-Angebote.

Ein separater zuvor nicht für Promptentwicklung verwendeter künstlicher Fall enthielt „Frühstück nicht enthalten“, eine eingeschränkte Stornobedingung und einen „ab“-Preis pro Person. Alle drei ausgewählten Fundstellen wurden unabhängig richtig klassifiziert; Negation und Ausgangspreisbasis blieben erhalten. Er wurde nicht in Reise-/Budgetpreise übernommen.

Laufzeit dieses Ressourcen-/Holdout-Probes: **7.663 s**. Modellallokation nach der Anfrage laut vorhandener Ollama-API: **3,181,631,242 Byte** (etwa 2.96 GiB), Kontext 4096, ein geladenes Modell. Das ist eine tatsächliche API-Speicheraufnahme, keine gemessene RSS-Spitze; Metal und RSS werden nicht addiert. Öffentliche Modellversuche: ungefähr 1,60–15,02 s. Kein zweites Modell oder neue Modellverwaltung.

## GUI, Speicherung und PDF

Unter **Details → Vorhandene Preisbelege mit lokaler KI prüfen** ausdrücklich **ja** wählen; Standard **nein**. Die vorhandene Preisaktion und automatische Preisphase verwenden dieselbe Option. Keine zusätzliche Oberfläche. Fortschritt und Abbruch laufen in vorhandenen Workern; Detailansicht zeigt Qualitätszustand, fehlende Angaben und Originalnachweise. Technische Statuscodes werden in verständliche deutsche Texte übersetzt.

Echte GUI-Preisprüfung mit laufendem Dienst: **27.031 s**, 1168 Ereignis-Callbacks, maximal **0.030 s** Abstand. Die KI lief ins Limit; die echten Tarife blieben erhalten. Bei vollständig gestopptem eigenen Dienst: **9.667 s**, dieselben erhaltenen Tarifbeträge und klare KI-Ausfallmeldung. Normale GUI-Suche bei gestopptem Dienst und aktivierter Preis-KI-Option: **4.520 s**, 9 reguläre beziehungsweise offene Ergebnisse. Diese Zahl bedeutet keine neun vollständig bepreisten Angebote.

Generationsschutz verwirft verspätete Preis-/Modellantworten nach neuer Suche/Abbruch/Schließen. Antworten für ein anderes Ziel ersetzen die aktive Auswahl nicht. Das Öffnen gespeicherter Reisen beendet auch eine laufende Preisprüfung. Nutzerwahl bleibt erhalten. Die vor Beginn ausdrücklich gespeicherte Testreise blieb während der echten GUI-Prüfungen unverändert; neue Metadaten werden ausschließlich mit der vorhandenen Speicheraktion dauerhaft. Alte Snapshotformate bleiben lesbar. Die reale Reise-Tabelle wurde nur lesend fingerprinted; Anzahl/Hash unverändert. Eigener Dienst wiederhergestellt, genau ein bestehendes Modell, zum Abschluss entladen.

PDF: Ein begrenzter Zusatzabschnitt übernimmt dieselben Qualitäts-/Lückentexte, vorhandene Preise/Basis und ausgewählte Hinweise; Originalnachweise bleiben ausführlich in der GUI. Bestehendes Layout und Quellenlinks bleiben erhalten. Ein echter öffentlicher Prüfsnapshot wurde zu sechs Seiten exportiert, mit Poppler gerendert und **alle sechs Seiten** visuell geprüft: keine beobachteten Überläufe/Überlappungen. Nach Ablauf der technischen Preisfrist bleiben Originalbeträge sichtbar als veraltet, werden in den Vergleichssummen aber nicht mehr als aktuelle Teilkosten berücksichtigt. Kein neuer PDF-Entwurf oder weiterer Exportablauf.

Die GUI-Abnahme ist eine echte automatisierte Tk-Funktionsprüfung mit Messwerten und zusätzlichen Desktoptests; eine vollständige manuelle Screenshot-/Klickabnahme von Schritt 6 wird nicht behauptet.

## Regression, Fehlerverlauf und Dateien

**364 Tests bestanden**, einschließlich aller 316 bisherigen Tests und 48 neuer Prüfungen: 36 Angebots-/Fundstellen-/Analyse-/Kosten-/Abbruchtests, acht HTTP-/Identitätsprüfungen und vier Desktoptests. Keine bisherigen erwarteten Sachpreise geändert oder Tests entfernt. Weiterhin Schritte 1–5, Suche, Ranking, Kosten, Speicherung und bestehende PDF-Tests bestanden. `compileall` und `git diff --check` bestanden.

Dokumentierter Fehlerverlauf:

- Früher vollständiger Lauf mit fehlender PDF-Abschnittskennung: ein Fehler von 316. Korrigiert; ursprünglicher Output erhalten.
- Erste öffentliche Kampagne brach nach fünf Fällen wegen des nicht auflösbaren Prüforts London im kleinen Reiseführerkatalog ab. Kein ähnlich benannter Ort und keine Koordinate erfunden; ungeeigneten Prüffall ausdrücklich durch den vorhandenen Katalogort Kopenhagen ersetzt. Frühere Antworten/Abbruch protokolliert.
- Zweite Kampagne führte alle sechs Vergleiche und aufgezeichneten Modellfälle durch, danach GUI-Prüfhilfe mit falscher Treffertabelle (offene Idee statt Filtertreffer) fehlgeschlagen. Prüfhilfe korrigiert, bereits abgeschlossene Quellenvergleiche nicht wiederholt; echte GUI-/Offlineprüfung anschließend erfolgreich fortgesetzt.
- Zwei kurzzeitig beobachtete ResourceWarnings zu offenen Pipes; Diagnose-Lauf mit Tracemalloc: 363 Tests/117,550 s ohne erneute Warnung. Bereinigung des bereits beendeten Prozesses unabhängig abgesichert und mit reproduzierbarem Race-Test ergänzt. Abschließender normaler Lauf: 364 Tests ohne diese Warnungen.
- Modellzeitlimits/ablehnende Antworten und gesperrte Quellen sind keine erfolgreichen Extraktionen; Daten bleiben erhalten und Lücken sichtbar. Positive Fixturewerte sind nicht als Liveangebote bezeichnet.

Neue Verantwortungen: `core/planning/OfferQuality.py`, `OfferEvidence.py`, `OfferPresentation.py`; `infrastructure/local_ai/OfferAnalysisService.py`; enge vorhandene Preisquellenpolitik in `infrastructure/planning/OfferSourcePolicy.py`. Gezielte Anpassungen an vorhandenen OfferResearchService, TravelOffers, SearchRequest, drei Preisadaptern, OpenTravelProvider, ResearchHttp, bestehendem LocalModelClient, GUI/PDF-Presentern. Neue Unit-/Desktoptests und `scripts/verify_offer_analysis.py`. README, Quellen-/Lizenzhinweise, Preisberichte und PROJECT_LOG abgeglichen.

```bash
.venv/bin/python -m unittest discover -s tests -p 'test_*.py'
.venv/bin/python scripts/verify_offer_analysis.py --live
# Nach dokumentiertem Abbruch vollständige bestehende Fälle behalten:
.venv/bin/python scripts/verify_offer_analysis.py --live --resume
```

Der Live-Verifier verlangt einen bereits laufenden nachweislich eigenen Dienst. Er installiert nichts und verwendet temporäre Reisen. Resume ist eine Fortsetzung, keine neue unabhängige Vollkampagne. Öffentliche Preis-/Quellendaten können sich ändern; technische erfolgreiche Prüfungen sind kein Nachweis allgemeiner Modellqualität.

## Abschlussstatus und offene Aufgaben

- **Technisch implementiert:** Gemeinsame beleggebundene Auswahl/Qualitätsprüfung, sichere bestehende Preisprovider, begrenzte Nachprüfung, GUI, Persistenz und notwendige PDF-Darstellung.
- **Automatisiert geprüft:** 364 bestandene Tests und technische Abschlussprüfungen.
- **Öffentlich geprüft:** Sechs Vergleichsfälle, echte datierte Bahntarife, offizielle veröffentlichte Eintritte und Quellenblockaden, GUI mit/ohne Dienst.
- **Fachlich verbessert:** Deterministische Behandlung von Lücken/Gebühren/Veralterung, strengere Identitäts-/Abrufregeln; präzisere Anzeige. Kein nachgewiesener zusätzlicher Preisfakt oder wirtschaftlicher Qualitätsgewinn der KI.
- **Weiter eingeschränkt:** Smoobu aktuell gesperrt; allgemeine Hotel-/Mehrzimmer-/Flugangebote fehlen. Keine zuverlässige allgemeine Interpretation beliebiger Storno-/Gebührenprosa, keine allgemeine Websuche, keine neuen FX-Regeln, kein vollständig buchbares Paket. Neue Datenlücken ohne unterstützten zulässigen Abrufweg bleiben offen. Kein automatischer Commit oder Push für Schritt 6.
