# Lokale KI – Schritt 2: Beleggebundene Reiseerklärungen, 30.10.2026

Schritt 2 ist implementiert. Beim ausgewählten Ergebnis öffnet **„Passung erklären“** einen eigenen Bereich im normalen Reiseplaner. Die lokale KI wählt vorhandene Hinweise zu den ausdrücklich gewählten Interessen aus und ordnet sie. Der angezeigte Wortlaut entsteht aus überprüfbaren Vorlagen. **Es wird kein frei erfundener Modelltext als Reiseinformation übernommen.**

[Messwerte, Modellnachrichten, Rohantworten und Prüfungen](LOKALE_KI_SCHRITT2_2026-10-30.json) dokumentieren die tatsächliche Abnahme. Der [Bericht zu Schritt 1](LOKALE_KI_SCHRITT1_2026-10-30.md) einschließlich des dortigen See-/Wandern-Fehlers bleibt unverändert gültig. Eine Freitextübernahme wurde nicht eingebaut.

## Bedienung

```bash
.venv/bin/python scripts/local_ai.py start
.venv/bin/python main.py
```

1. Normal suchen und einen Treffer oder eine als offen gekennzeichnete Reiseidee auswählen.
2. **Passung erklären** wählen. Vorhandene Reiseinformationen bleiben im Reisevergleich nutzbar.
3. Im Erklärungsbereich Hinweise, Grenzen, Quellenstand und anklickbare Quellen ansehen.
4. Eine laufende Anfrage mit **Erklärung abbrechen** beenden. Erneutes Anzeigen derselben Erklärung verwendet den Sitzungscache.

Der Reiseplaner startet keinen KI-Dienst automatisch. Fehlt der Dienst, nennt die Oberfläche den Startbefehl und zeigt eine Belegübersicht ohne KI-Auswahl. Fehlendes Modell, Timeout, abgeschnittene oder fachlich ungültige Antworten führen ebenfalls zu einer beleggebundenen Übersicht. Ein Abbruch zeigt keine Teilantwort. Es erfolgen keine Downloads und keine Cloud-Anfragen.

## Aufgabenverteilung und Daten

- `core/planning/TripExplanation.py`: deterministische Kontextauswahl, Aussagevertrag, Referenzprüfung und Darstellung.
- `infrastructure/local_ai/ExplanationService.py`: bestehender lokaler Client, Fehlerbehandlung und Sitzungscache.
- `entrypoints/gui/ExplanationPanel.py`: eigener Worker, Abbruch, Status, Quellenlinks und Schutz vor verspäteten Antworten.
- `SurprisePlannerApplication.py`: Aktion beim Ergebnis und Einbindung in Auswahl, Suche, Polling und Schließen.
- Neue Unit-/GUI-Tests und `scripts/verify_trip_explanation.py` für echte lokale Abnahmen.

Dem Modell werden ausschließlich Zielname/Land, ausdrücklich gewichtete Interessen sowie begrenzte kanonische Aussagen mit internen Beleg-IDs und Unsicherheiten übergeben. Keine Startadresse, kein Startort, Budget, Personenzahl, Reisetermine, Reisehistorie oder vollständige Datenbank. Die Auswahl verwendet vorhandene strukturierte Interessenbelege; ältere Reisen können strukturierte Aktivitäten mit Quelle und passender Themenzuordnung nutzen. Redaktionelle Freitexte allein werden nicht zu konkreten Fakten aufgewertet.

Höchstens acht Beobachtungen, höchstens zwei je Interesse, deterministisch nach Interessengewicht und stabilen Beleg-Hashes ausgewählt. Höchstens sechs werden angezeigt. Der Kontext wird am bestehenden zentralen Zeichen-/Kontextlimit ausgerichtet: Beobachtungen werden vollständig entfernt, Pflichtunsicherheiten bleiben erhalten. Passt kein ausreichender Kontext, wird keine Modellanfrage gemacht. Die Darstellung erklärt die begrenzte Auswahl ausdrücklich.

URLs und Quellenmetadaten werden aus den tatsächlichen Eingabebelegen im Programm zur Anzeige ergänzt; das Modell muss keine URLs erzeugen. Links werden nur auf ausdrücklichen Klick geöffnet. Fehlender Abrufstand bleibt unbekannt; kein Abruf wird als neue Livebestätigung bezeichnet.

## Warum eine Beleg-ID nicht als Faktenprüfung genügt

Das Modell darf nur vorgegebene `claim_id`-/`evidence_ids`-Paare zurückgeben. Unbekannte, fremde, doppelte oder falsch zugeordnete Referenzen und zusätzliche Freitextfelder werden verworfen. Alle verpflichtenden Unsicherheiten werden geprüft und unabhängig von der Modellauswahl vollständig angezeigt.

Der Renderer zeigt ausschließlich die ursprünglichen kanonischen Aussagen. Dadurch kann eine Antwort mit gültiger Beleg-ID keinen abweichenden Preis oder eine erfundene Badezusage einschleusen. Nicht als Luftlinie belegte Entfernungsarten werden nicht als Weg ausgegeben. Ein Badethema bedeutet lediglich eine bestehende Quellenzuordnung; es bestätigt keine sichere, nutzbare Badestelle. Natur-/Grünräume werden nicht als Ruhebeleg verwendet. Fehlende Daten bleiben Datenlücken.

Widersprüchliche Quellen bleiben getrennte Beobachtungen. Öffnungsangaben werden in diesem Schritt weder interpretiert noch gegeneinander entschieden. Die Erklärung weist auf ungeprüfte Widersprüche und kombinierte Eignung hin. Die vorhandenen Reise-/Quelldetails bleiben maßgeblich. Auch tatsächlich vorhandene Preisangaben werden von diesem Modul weder neu bewertet noch überschrieben.

**Grenze:** Das Programm prüft den erlaubten Wortlaut, die Zuordnung und die übergebenen Werte. Es verifiziert nicht unabhängig die Richtigkeit der Kartierung oder die ursprüngliche Themenklassifikation. Eine Zuordnung ist kein Eignungsversprechen. Die KI liefert eine begrenzte redaktionelle Auswahl; kein neues Suchranking und keine freie Reiseberatung.

## Sitzung und Bestandsschutz

Anfragen laufen außerhalb des Tk-Threads und verwenden die vorhandene Begrenzung auf eine lokale Modellaufgabe. Auswahlwechsel, geänderte Belege, neue Suche und Schließen invalidieren die Anzeige über eigene Anfragetokens; verspätete Antworten erreichen kein anderes Ziel.

Der Cache hält höchstens 64 Einträge im Speicher. Sein Schlüssel enthält die Vertragsversion und einen lokalen Hash des vollständigen aktuellen Reisezustands, damit Kriterien- oder Belegänderungen eine neue Erklärung verlangen. Dieser Hash wird nicht als privater Reiseinhalt an das Modell übertragen. Erfolgreiche Auswahlen und fachlich verworfene Auswahlen mit sicherer Rückfalldarstellung werden wiederverwendet; Verbindungs-/Transportfehler werden bei einem erneuten Klick erneut versucht. Kein Cacheeintrag wird in Reise-Snapshots geschrieben.

Ranking, harte Filter, Preise, Budgetarithmetik, Suchprovider, gespeichertes Reiseformat und PDF-Pfad wurden in diesem Schritt nicht verändert. Die bestehenden uncommitteten Europa-Änderungen bleiben erhalten. Kein Commit oder Push.

## Automatisierte Tests

**215 Tests bestanden in 9,732 Sekunden**, davon 23 neue Tests für Schritt 2 (17 Unit-, sechs GUI-Tests). Die bisherigen 192 Tests einschließlich Suche, Ranking, Budget, Speicherung und PDF bleiben bestanden. Zusätzliche GUI-Prüfungen decken aktive Abbrüche, neue Suche, Zielwechsel, Belegänderung, Wiederverwendung und unveränderte Reiseinformationen ab. `compileall` und `git diff --check` bestanden.

## Tatsächliche lokale Qualitätsprüfungen

Modell unverändert: `qwen3:4b-instruct-2507-q4_K_M`, Ollama 0.40.13, Endpoint `127.0.0.1:11435`, Kontext 4.096, regulär höchstens 768 Ausgabetoken.

| Künstlicher Fall | Verhalten | Gemessene Zeit | Fachliche Abnahme |
|---|---|---:|---|
| kultur_see_ruhe_unbekannte_preise | local_ai | 16.392 s | bestanden |
| quellenname_mit_fremder_anweisung | local_ai | 12.500 s | bestanden |
| keine_belege_keine_erfundene_passung | deterministic | 0.000 s | bestanden |
| widerspruechliche_oeffnung_nicht_aufgeloest | local_ai | 14.826 s | bestanden |
| see_landschaft_ohne_badebeleg | deterministic | 0.000 s | bestanden |
| entfernungsart_unbekannt | local_ai | 7.150 s | bestanden |
| kontextgrenze_viele_interessen | local_ai | 31.436 s | bestanden |

Damit fünf echte synthetische Modellgenerierungen und zwei bewusst modellfreie Fälle; keine behaupteten sieben Modellantworten. Alle fünf Modellantworten wurden fachlich als zulässige Referenzauswahl angenommen. Die Prüfung kontrollierte konkrete Grenzen zusätzlich: getrennte widersprüchliche Quellen, fehlender Badenachweis, keine erfundene Wanderabsicht, unbekannte Entfernungsart und sichtbare Preis-/Abdeckungsgrenzen. Ein fremder Befehl im Quellennamen blieb zitierte Quelldaten; daraus folgt keine allgemeine Immunität gegen beliebige Angriffe.

Es gab in diesen fünf Generierungen keine fachlich verworfene Auswahl. Manipulierte IDs, falsche Belegpaare und zusätzliche Modellbehauptungen wurden gezielt in den automatisierten Tests verworfen und durch die Belegübersicht ersetzt. Echte Fehlerpfade wurden zusätzlich über den produktiven Service ausgelöst:

- Ausgabelimit von einem Token: nach 4.785 s als abgeschnitten erkannt, keine Teilantwort angezeigt, Belegübersicht vorhanden.
- Zeitlimit von 0,25 s: nach 0.271 s beendet, Belegübersicht vorhanden.

Diese Prüfungen änderten nur die jeweilige Client-Konfiguration im Test, keine zentrale Datei. Fehlendes Modell und beschädigte Transportantworten sind außerdem durch die bestehenden Client- und neuen Servicetests abgedeckt.

## Echter GUI-/Suchablauf

- Regulärer Suchworker mit vorhandenem europäischem Datenbestand und estnischer Teilraumsuche: 6.689 s, **0 Filtertreffer und sechs offene Reiseideen**. Diese werden nicht zu bestätigten Treffern umetikettiert.
- Erklärung für ein tatsächlich ausgewähltes öffentliches Suchergebnis: 17.935 s, gültige lokale Auswahl, unveränderte Arbeitskopie.
- Währenddessen 783 Tk-Callbacks; größter Abstand 0.026 s.
- Echter Abbruch über das neue Panel: Worker nach 0.031 s beendet, keine übernommene Antwort oder Teilantwort.
- Eigener KI-Dienst vollständig gestoppt: normale Suche weiterhin fertig nach 5.665 s mit sechs offenen Ideen.
- Erklärung ohne Dienst: nach 0.181 s Belegübersicht und konkreter Startbefehl; Suche weiter bedienbar.

Die Suchabnahme verwendete einen temporären Reise-Speicher und den vorhandenen öffentlichen Zielbestand. Die echte Reise-Tabelle wurde nur lesend fingerprinted und blieb unverändert. Keine gespeicherte private Reise wurde für Modelltests verwendet. Die sieben überwiegend synthetischen Fälle und der öffentliche GUI-Fall werden im JSON getrennt ausgewiesen.

Das echte Tk-Fenster wurde für die letzte Prüfung angezeigt und die normale Ereignisschleife ausgeführt. Eine zusätzliche visuelle CUA-Prüfung scheiterte am ScreenCaptureKit-Aufnahmefehler -3811 (Computer Use -10005). Daher wird **keine abgeschlossene manuelle Sicht-/Klickabnahme** behauptet. Bedienlogik und Widgetinhalte wurden automatisiert am echten Fenster geprüft.

Frühe Fehler im Prüfskript (Pfadauflösung, Bereinigung vor Fenstererstellung und eine zunächst nur Filtertreffer akzeptierende Abnahmebedingung) wurden korrigiert. Eine zwischenzeitliche Satzänderung änderte Referenz-IDs und wurde vom Replay korrekt zurückgewiesen; der ursprüngliche geprüfte Vertrag wurde wiederhergestellt. Keine fachlichen Erwartungen wurden an falsche Modellantworten angepasst. Die letzte Gesamtprüfung bestand; die Historie ist im JSON erläutert.

## Wiederholen und nächster Umfang

```bash
.venv/bin/python -m unittest discover -q
.venv/bin/python scripts/verify_trip_explanation.py --live
# Optional mit sichtbarem Prüffenster:
.venv/bin/python scripts/verify_trip_explanation.py --live --visible
```

Die Live-Prüfung benötigt den nachweislich selbst gestarteten Dienst, stoppt ausschließlich diesen für den Offline-Test, startet ihn anschließend wieder und entlädt das Modell. Sie löst reguläre begrenzte Quellensuchen über den bestehenden Suchprovider aus; die Erklärung selbst recherchiert nicht.

Zum Abschluss ist der eigene Dienst erreichbar und das Modell entladen. Keine zusätzlichen Modelle oder Cloud-Funktionen. Freitextauswertung, neue Recherchewerkzeuge, Preisinterpretation und PDF-Erklärungen sind weiterhin nicht umgesetzt. Der See-/Wandern-Fehler aus Schritt 1 wird durch den beschränkten Aussagevertrag umgangen, nicht als allgemein gelöst ausgegeben.
