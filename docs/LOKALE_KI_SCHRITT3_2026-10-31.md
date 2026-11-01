# Lokale KI – Schritt 3: Reisewünsche und kontrollierte Formularübernahme

Prüfbericht vom **31.10.2026**, Umsetzung und Prüfungen am 30./31.10.2026.

Schritt 3 ist implementiert. Links im Reiseplaner gibt es den Reiter **Wünsche**, rechts die **Wunschvorschau**. Nach ausdrücklicher Auswertung entstehen einzeln auswählbare Vorschläge. Erst **„Ausgewählte Vorschläge übernehmen“** ändert das Formular. Es wird keine Suche automatisch gestartet.

Die Funktion ist bewusst begrenzt: **kein allgemeines, fehlerfreies Sprachverständnis**. Die KI erkennt Feld und vollständige Originaltextstelle. Zahlen, Einheiten, Datumsregeln und Änderungsoperationen berechnet und prüft der Programmcode. Nicht abgesicherte Vorschläge werden nicht übernehmbar angeboten. Fehlende oder ausgelassene Angaben bleiben zur manuellen Präzisierung sichtbar.

[Ausführliche Rohantworten, Fehlschläge und Messwerte](LOKALE_KI_SCHRITT3_2026-10-31.json) · [Feldvertrag und Zuordnung](REISEWUNSCH_FELDVERTRAG.md) · [Schritt 2](LOKALE_KI_SCHRITT2_2026-10-30.md)

## Bedienung

```bash
.venv/bin/python scripts/local_ai.py start
.venv/bin/python main.py
```

1. Links **Wünsche** öffnen und höchstens 2.500 Zeichen eingeben.
2. **Wünsche auswerten** wählen; die lokale Anfrage läuft im Hintergrund.
3. In der Wunschvorschau bisherige Werte, neue Werte/Operationen und Originaltextstellen prüfen. Anfangs ist nichts ausgewählt.
4. Gewünschte Zeilen über die Spalte „Übernehmen“ oder „Markierte Auswahl umschalten“ auswählen.
5. **Ausgewählte Vorschläge übernehmen** wählen. Alle ausgewählten Änderungen werden zusammen geprüft; bei Fehlern wird keine davon angewendet.
6. Die normale Suche anschließend selbst starten.

Beispiel für eindeutig unterstützte Formulierungen:

> Wir sind 4 Erwachsene; wir benötigen 2 Zimmer; 6 Nächte; Gruppenbudget: 2.400 Euro; nur mit dem Zug.

Interessen ohne Zahl erhalten kein erfundenes Gewicht. Für eine übernehmbare Gewichtung beispielsweise **„Kultur: 4 von 5“** schreiben. Wünsche/Pflichten beispielsweise **„Pool ist Pflicht“**, **„Küche ist Wunsch“**, **„Parkplatz egal“**.

Der Dienst startet nicht automatisch mit der App. Ohne Dienst bleibt die manuelle Eingabe und Suche nutzbar. Freitext und Formular werden bei Fehlern erhalten; es gibt keine übernommene Teilantwort. Abbruch, Textänderung, Formularänderung, neue Suche und Schließen entwerten laufende oder alte Vorschauen. Auch zwischenzeitlich geänderte und zurückgesetzte Formularwerte machen eine neue Auswertung erforderlich.

## Unterstützter Umfang

Der [vollständige Feldvertrag](REISEWUNSCH_FELDVERTRAG.md) wurde vor der Implementierung angelegt und nach dem echten Modellversuch auf Feld-/Textstellen-Erkennung präzisiert.

- Erwachsene und ausdrücklich genannte Zimmer, ganze Zahlen einschließlich ausgeschriebener Zahlen eins bis zwölf. Keine Zimmerableitung aus Personen.
- Exakte Kalendertage oder Nächte: Nächte + 1 wird sichtbar erläutert und setzt min_days/max_days gemeinsam.
- ISO-Zeitraum sowie Monat mit ausdrücklichem Jahr: früheste Abreise und späteste Rückkehr gemeinsam. Die vorhandene Zukunfts-/Zeitraumvalidierung bleibt maßgeblich.
- Zwei klar definierte relative Formulierungen: „im nächsten Juli“ bedeutet nächster noch nicht begonnener Juli; ab Juli also Folgejahr. „im Juli nächsten Jahres“ bedeutet Bezugsjahr + 1. Bezug ist das lokale Datum Europe/Berlin und steht im Vorschlag. Kein Jahr für „im Juli“ erfinden.
- Eindeutiges gesamtes Gruppenbudget in EUR, deutsche Dezimal-/Tausendernotation. Keine Umrechnung von Pro-Person-, Tages- oder Übernachtungsbudgets. „Günstig“ bleibt unbekannt.
- Expliziter Startort, maximale Stunden je Richtung, vorhandener ausdrücklich bezeichneter Zieltyp und einzeln bezeichnetes Land/Region/Ausschluss. Keine neue Geokodierung oder Recherche.
- Verkehrsmittel: „mit“ ergänzt, „nur mit“ ersetzt, „nicht mit“ entfernt. Bekannte Synonyme Bahn/Zug, PKW/Auto und Flugzeug/Flug sind kontrolliert zugeordnet. Leere Verkehrsmittelauswahl wird von der Gesamtvalidierung abgewiesen.
- Bezifferte einzelne Interessen erhalten 0–5; alle anderen Einträge bleiben bestehen. Beziffertes Nachtleben wird dem bestehenden Interesse Feiern zugeordnet. Natur ergibt kein Ruheinteresse; See ergibt weder Baden noch Wandern.
- Bekannte Ausstattung: einzelnes Merkmal zwischen Pflicht, Wunsch und egal umstellen. Keine Löschung anderer Merkmale und keine neue negative Ausstattungsbedingung.

Nicht unterstützte oder verlustbehaftete Angaben werden ausdrücklich zur manuellen Klärung angezeigt: Kinder, ungewichtete Interessen, „keine Großstadt“, negative Aktivitätsverbote, unbekannter Budgetumfang oder fehlendes Jahr. Technische Suchparameter und Rankinggewichte sind nicht vom Modell steuerbar.

Die unabhängige Grammatik akzeptiert vollständige, begrenzte Aussagen. Semikolon, Zeilenumbruch und klare Satzgrenzen trennen Aussagen; manche durch Komma getrennte vollständige Aussagen werden erkannt. Zusammengesetzte oder abweichende Formulierungen können zurückgehalten werden. Es gibt keine stillschweigende Kürzung überlanger Eingaben.

Fragen, hypothetische, bedingte, alternative oder erkennbare Korrekturformulierungen werden konservativ als Ganzes zur Klärung zurückgehalten. Für diesen schon unabhängig erkannten Fall ist im finalen Programm keine Modellanfrage erforderlich. Widersprüchliche Angaben zum selben Feld werden blockiert; klar unabhängige andere Angaben können weiterhin überprüfbare Vorschläge bilden.

## Modellvertrag und Prüfung

Der ursprüngliche Vier-Feld-Vertrag (Feld, Wert, Operation, Fundstelle) scheiterte praktisch: Zahlen wurden statt vollständiger Textstellen kopiert, fehlende Felder ergänzt und Werte interpretiert. Im ersten Lauf waren nur vier von zehn Fällen vollständig, sämtlich Fälle ohne notwendige Übernahme; der echte GUI-Übernahmetest scheiterte. Keine dieser falschen Angaben wurde freigegeben. Dieser Versuch ist im JSON erhalten.

Der finale Vertrag erlaubt nur **field + quote**. Das Modell klassifiziert die Textstelle; unabhängige Regeln liefern Wert, Operation und Erklärung. Zusätzliche Modellwerte sind nicht zugelassen. Die Antwort erhält keine vorgefertigten Kandidatenlösungen aus den Regeln und keine bestehenden Formularwerte.

Der Schema-Check prüft Form und Feldfreigabe. Anschließend muss ein Paar eine vollständige unabhängig erkannte Aussage genau treffen. „wandern“ innerhalb von „nicht wandern“, „4“ statt „4 Erwachsene“, Pro-Person-Budgets oder falsch zugeordnete Felder werden nicht freigegeben. Datum, Fundstelle und Inhalt werden nicht durch Modell-Konfidenz oder eine zweite Modellantwort bestätigt.

Regelhaft erkannte, vom Modell aber ausgelassene Angaben erscheinen als ausgelassen – sie werden nicht still ergänzt. Es gibt höchstens acht Modellvorschläge pro Auswertung. Eine vorhandene Fundstelle alleine kann keine beliebige Wertinterpretation freischalten.

Auch diese Beschränkung ist kein allgemeiner Beweis über die Bedeutung beliebiger deutscher Texte. Die Vorschau und ausdrückliche Auswahl bleiben notwendig. Nicht abgedeckte Semantik wird manuell behandelt; es wurden keine größeren Modelle heruntergeladen.

## Atomare Übernahme und Bestandsschutz

Die Auswahl wird auf einer Kopie des aktuellen gültigen SearchRequest angewendet und vollständig mit der vorhandenen Validierung geprüft. Beispielsweise verhindern zu viele Zimmer oder zu wenig Autositzplätze die gesamte ausgewählte Übernahme. Fehlende Fahrzeugwerte werden nicht passend ergänzt.

Listenoperationen sind ausdrücklich getrennt; einzelne Interessen und Merkmale bleiben lokal begrenzte Änderungen. Nicht ausgewählte Felder, Vergleichsgewichte und technische Suchparameter bleiben erhalten. Bestehende Ergebnisse und gespeicherte Reisen werden nicht nachträglich umgeschrieben. Die Übernahme löst keine Suche aus.

Ein Snapshot des Formulars und eigene Anfragetokens verhindern alte Antworten. Text- und Formularänderungen invalidieren auch eine fertige Vorschau. Alle Vorschläge starten nicht ausgewählt.

## Datenschutz und Laufzeit

Übertragen wird ausschließlich der ausdrücklich eingegebene Wunschtext samt Feldbeschreibungen an den konfigurierten Loopback-Dienst. Der eingegebene Text selbst kann persönliche Angaben enthalten; bestehende Formularadresse, übrige Formularwerte und private gespeicherte Reisen werden nicht angehängt.

Die Anwendung speichert Freitext, Vorschau oder Modellantworten nicht automatisch in Reisen, Datenbank, Suchdiagnosen oder Protokollen. Eingabe und Ergebnisse liegen nur im Arbeitsspeicher. Der Prüfbericht enthält ausschließlich synthetische Wünsche. Die diagnostizierte echte Reise-Tabelle blieb unverändert.

Der bestehende LocalModelClient, die zentrale Konfiguration und die gemeinsame Parallelitätsbegrenzung mit Erklärungen aus Schritt 2 bleiben maßgeblich. Kein Cloud-Fallback, automatischer Download oder Dienststart. Modell/Runtime unverändert: Qwen3-4B-Instruct-2507-Q4_K_M und Ollama 0.40.13, 127.0.0.1:11435, Kontext 4.096 und regulär maximal 768 Ausgabetoken.

## Automatisierte Tests

**248 Tests bestanden in 11,455 Sekunden:** bisherige 215 plus 23 neue Unit- und zehn neue GUI-Tests. Suche, Filter, Ranking, Budget, Persistenz, PDF und Erklärungen aus Schritt 2 bleiben abgedeckt. `compileall` und `git diff --check` bestanden.

Zusätzliche Tests decken unter anderem falsche echte Fundstellen, erfundene Fundstellen, Negationen, Frageform, spätere Rücknahme, Budgetbezug, Nächte, Jahresangaben, bedingte Aussagen, klare Synonyme, Listenoperationen, gemeinsame Validierung, selektive Übernahme und veraltete Antworten ab.

Frühe Tk-Tests deckten außerdem eine Bereinigung geschlossener Fenster im Worker auf. Panel-/App-Referenzzyklen werden beim Schließen aufgelöst; vor dem neuen Worker werden ausstehende Tk-Objektgraphen im UI-Thread gesammelt. Die abschließende Suite lief ohne diese Warnungen oder blockierte Tests.

## Echte Modellqualität und Grenzen

Die Zwei-Feld-Kampagne enthielt 14 synthetische Fälle. Vier frische held_out_final-Formulierungen wurden erst nach Festlegen des vereinfachten Vertrags aufgenommen. Frühere held_out_initial-Fälle waren bereits im fehlgeschlagenen ersten Vertrag gelaufen. Die frischen Fehlfälle wurden nicht durch Promptanpassung passend gemacht.

| Fall | Gemessene Zeit | Vollständig extrahiert | Keine unzulässige Freigabe |
|---|---:|---|---|
| vollstaendig_beispiel | 5.014 s | ja | ja |
| ausgeschrieben_neue_formulierung | 4.611 s | ja | ja |
| bekannter_see_fehler | 3.554 s | ja | ja |
| budgetbezug_unbekannt | 2.423 s | ja | ja |
| widerspruch_nicht_entscheiden | 3.052 s | ja | ja |
| negation_kinder_grossstadt | 3.509 s | ja | ja |
| datum_ausstattung_ergänzung | 4.982 s | ja | ja |
| relative_daten | 3.362 s | ja | ja |
| alternative_kein_stilles_teilverstaendnis | 3.787 s | nein | ja |
| eingeschleuste_befehle | 1.870 s | ja | ja |
| frische_zahlen_und_startort | 4.768 s | ja | ja |
| frische_gewichtung_ausstattung_monat | 4.923 s | ja | ja |
| frische_nachtangabe_unklarer_preis | 3.471 s | nein | ja |
| frische_gruppe_mit_kindern | 1.442 s | nein | ja |

**Ursprüngliche Kampagne: 11/14 vollständig, 14/14 ohne unzulässige Freigabe.** Das bedeutet nicht 14 perfekte Modellantworten. Unbelegte oder falsch zugeordnete Angaben wurden verworfen. Ein Konditionalfall erreichte das Zeitlimit; zwei frische Fälle blieben unvollständig:

1. „Wir möchten fünf Nächte bleiben“: Modell lieferte verkürzte statt vollständiger Textstelle; Nächte/Dauer wurden zurückgehalten und als ausgelassen angezeigt.
2. Gruppe mit Kindern: Erwachsene korrekt erkannt, zusätzlich ausdrücklich genannte Verkehrsmittel ausgelassen. Kinder blieben separat als nicht unterstützt sichtbar.

Der Konditionalfall wird nach dem gezielten Nachbessern der Vorprüfung ohne Modell zurückgehalten. Tatsächlicher Nachtest: 0.000302 s, null Modellaufrufe, sichtbarer Klärungshinweis. Zusammengeführte Evidenz ergibt damit zwölf von vierzehn vollständig behandelte Fälle; dies ist **keine zweite vollständige Modellkampagne**. Die beiden übrigen Auslassungen bleiben offen und erfordern eine manuelle Präzisierung.

Ein zusätzlicher echter Nachtest belegt „nur mit der Bahn“ und ausdrücklich beziffertes Nachtleben: 4.847 s, beide Vorschläge angenommen. Ursprüngliche Rohfehler und die Wirkung der nachgeschalteten Prüfung werden im JSON getrennt ausgewiesen.

## Echte GUI, Abbruch und Offline-Abnahme

- Vorschau und explizite Übernahme von Erwachsenen, Zimmern und Gruppenbudget: 3.356 s. Vor der Übernahme blieb das Formular identisch, anschließend änderten sich genau diese drei Felder. Kein Suchstart und keine Speicherung.
- Währenddessen 129 Tk-Callbacks, größter Abstand 0.116 s.
- Echter laufender Abbruch: Worker nach 0.038 s beendet; keine Vorschau übernommen, Formular unverändert.
- Eigener Dienst vollständig gestoppt: nach 0.324 s verständliche Fehlermeldung und Startbefehl; Text/Formular erhalten.
- Normale manuelle Suche ohne Dienst: 7.085 s, abgeschlossen mit **0 Filtertreffern und sechs offenen Reiseideen**. Kein Umetikettieren offener Angaben.

Zusätzlich tatsächliche Fehlerpfade über den neuen Service:

- ausgabelimit: 0.219 s, ValueError – bestanden.
- zeitlimit: 0.279 s, TimeoutError – bestanden.
- modell_fehlt: 0.013 s, ValueError – bestanden.

Die Prüfungen verwendeten einen temporären Reise-Speicher und den öffentlichen vorhandenen Zielbestand. Der normale main.py-Einstieg wurde anschließend ohne Fehlereintrag gestartet. Eine erneute visuelle CUA-Prüfung scheiterte am ScreenCaptureKit-Aufnahmefehler -3811 / Computer Use -10005. Daher keine behauptete vollständige manuelle Sicht-/Klickabnahme; echter Tk-Ablauf und Widgetinhalte sind automatisiert geprüft.

## Reproduzieren

```bash
.venv/bin/python -m unittest discover -q
.venv/bin/python scripts/verify_travel_wishes.py --live
# Optional sichtbares Prüffenster:
.venv/bin/python scripts/verify_travel_wishes.py --live --visible
```

Das Live-Skript verlangt einen nachweislich eigenen laufenden Dienst, hält ausschließlich diesen für den Offline-Test an, startet ihn anschließend wieder und entlädt das Modell. Rohberichte werden nur durch dieses ausdrücklich aufgerufene synthetische Prüfskript geschrieben. Ein Exit-Code 1 bleibt bei unvollständiger Extraktion beabsichtigt, auch wenn Schutz- und GUI-Abnahme bestehen.

Zum Abschluss: Dienst erreichbar, genau ein Modell installiert und entladen. Keine Änderung an Ranking, harten Filtern, Preis-/Budgetberechnung oder gespeichertem Reiseformat; keine neue Recherche, kein Chat und keine PDF-Erweiterung. Bestehende uncommittete Arbeit erhalten; kein Commit oder Push.
