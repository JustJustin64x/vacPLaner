# Preisrecherche und Verkehrsmittelvergleich, 29.10.2026

## Diagnose und gezielte Korrekturen

Der vorhandene Angebotsweg lieferte bereits echte Smoobu-Aufenthaltspreise und RegioJet-Gruppentarife. Die Preisnormalisierung verlor diese Beträge nicht. Die übrigen Ortsdaten waren Reiseführer-Einträge mit Suchlinks. Es gab keinen Aktivitätstarif-Adapter. Unbekannte Preise wurden bereits als offene Kosten geführt.

Der PDF-Presenter übernahm nur `trip.transports`; dieses Feld enthielt nur aktive Suchmodi und gegebenenfalls durch Zeitfilter reduzierte Optionen. Deshalb verschwanden Vergleichsmöglichkeiten im Export. `TravelComparison` ergänzt für den Export fehlende Modi mit ehrlichem Status und Suchlink. Vorhandene Nutzerwahlen bleiben erhalten. Tatsächlich gefundene weitere Bahn-/Flugangebote dürfen als Vergleichsalternative hinzukommen, ohne Suchmodi oder Auswahl zu ändern.

Die Exportaktion „recherchieren“ startete Orts-/Bildanreicherung. Sie startet jetzt die echte Preisrecherche im Hintergrund für jede ausgewählte Reise und kehrt anschließend zur Exportprüfung zurück. Ein Quellen-/Zeitlimit entfernt keine noch ungeprüfte Reise aus der Exportauswahl. Es wird nicht automatisch gespeichert.

Automatische Preise werden erst nach Sortierung der gefundenen Reisevorschläge für die besten `price_targets` Ziele ermittelt (Standard 3, einstellbar 0–12). Es bleiben maximal 32 zusätzliche HTTP-Aufrufe innerhalb der verbleibenden Suchzeit. Manuelle und Export-Prüfungen teilen maximal 40 Aufrufe und 600 Sekunden; jede Anfrage hat ihr eigenes kleineres Limit. Keine Wiederholung blockierter Quellen. Große Umfänge können daher ausdrücklich ungeprüfte Preise behalten. Es gibt keine erfundenen Fortschrittsprozente.

## Tatsächlich integrierte und live geprüfte Quellen

Die maschinenlesbaren Parameter, Zeitpunkte, Preise und Quellen stehen in [PREISPRUEFUNG_2026-10-29.json](PREISPRUEFUNG_2026-10-29.json). Der Lauf nutzte den normalen Produktionsweg und neue lokale Datenbanken. Er führte ausschließlich lesende Abfragen aus.

| Quelle | Zugriff und konkretes Ergebnis | Ausgelesen, integriert und geprüft | Grenze |
|---|---|---|---|
| [Apartments Innsbruck / Smoobu](https://www.apartments-innsbruck.com/en/buchen/) | Sechs datierte Ferienwohnungsangebote, 23.–25.11.2026, zwei Erwachsene, eine Einheit | 234 / 244 / 254 / 276 / 340 / 352 EUR für Gruppe und gesamten Aufenthalt; ausgewiesene Reinigung enthalten; Belegung und Angebotsparameter bestätigt; SQLite/PDF-Modell geprüft | Nur geprüfte Innsbrucker Einheiten; keine allgemeine Hotel-/Mehrzimmerabdeckung. Storno, Verpflegung und zusätzliche örtliche Gebühren nur soweit belegt. Keine Hochrechnung eines Apartments auf mehrere Zimmer. |
| [RegioJet](https://regiojet.com/) | Prag–Brünn, 12.–14.11.2026, zweite Klasse, zwei und fünf Erwachsene | Je Richtung bis zu drei Tarifdetails: günstigste und schnellste unter den geprüften Verbindungen; verschiedene Hin-/Rück-Kombinationen zu 33,60 / 42 EUR für zwei bzw. 84 / 105 EUR für fünf Erwachsene. Gruppentarife einmal summiert; Speicherung geprüft | Kein europaweiter Bahnmarktvergleich; eigenständige Fahrkarten; Zubringer offen. |
| [Museum Goldenes Dachl, Stadt Innsbruck](https://www.innsbruck.gv.at/freizeit/kultur/museen-stadtarchiv/museum-goldenes-dachl) | Offizielle Seite HTTP 200 | Regulärer Erwachseneneintritt 6 EUR, für zwei Erwachsene 12 EUR; eigenes optionales Preisobjekt mit Quelle, Abruf und Parametern | Veröffentlichter Tarif, keine datierte Ticketverfügbarkeit. Schließtage und künftige Geltung prüfen. |
| [Burg Bled](https://www.blejski-grad.si/sl/nacrtuj-obisk/cenik/) | Direkter Produktionsabruf HTTP 200; der Suchmaschinenabruf derselben Seite wurde teilweise mit 403 abgewiesen | Erste Tariftabelle, regulärer Erwachsenentarif 19 EUR; fünf Erwachsene 95 EUR; veröffentlichter Tarif ab 01.01.2026 | Keine datierte Eintrittskarte; regulärer Preis ohne unterstellten Gruppenrabatt; Sonderveranstaltungen separat. |
| [Futurium Berlin](https://futurium.de/de/besuch) | Produktionsabruf HTTP 200 | Allgemeiner Eintritt ausdrücklich kostenlos, Gruppe 0 EUR; Zusatzangebote separat | Workshops/Führungen/Veranstaltungen können kostenpflichtig sein; Öffnung und Gruppenanmeldung prüfen. |
| [National Gallery](https://www.nationalgallery.org.uk/visiting/plan-your-visit) | Offizielle Besuchsseite praktisch abrufbar, kostenloser allgemeiner Eintritt bestätigt | Gezielter Parser vorhanden, keine automatische Erweiterung des bestehenden Zielkatalogs | London fehlt im aktuellen Katalog; deshalb kein erfolgreicher durchgängiger Discovery-Prüffall. Für entsprechende bestehende Reise-Snapshots verwendbar. Sonderausstellungen separat. |

Die letzte Unterscheidung ist bewusst: Ein erreichbarer und korrekt lesbarer Tarif ist noch kein erfolgreich durchgelaufener Ziel-Suchlauf. Ein fehlgeschlagener London-Prüfversuch wurde nicht als Erfolg in den Livebericht aufgenommen.

Die robots-Dateien dieser vier offiziellen Tarifseiten wurden zusätzlich praktisch gelesen. Die benutzten Besuchs-/Tarifpfade sind nicht ausgeschlossen: Innsbruck sperrt `/neos/`, Bled `/styles/`, `/scripts/`, `/umbraco/`, National Gallery `/custom/popups` und `/external`, Futurium `/cpresources/`. Kein freies Crawling oder automatischer Wechsel auf ausgeschlossene Pfade.

## Fachmodell und Darstellung

Aufenthalts- und Rundreisepreise bleiben im bestehenden `TravelOffer`-Vertrag. Unterkunftsobjekte halten zusätzlich eine begrenzte Liste eigener Angebote; verschiedene Wohnungen bleiben verschiedene Unterkünfte. Die vom Nutzer ausgewählte Unterkunft bleibt auch dann gewählt, wenn passende bepreiste Alternativen hinzukommen. Im PDF folgen möglichst zwei aktuell bepreiste Alternativen.

Aktivitäten nutzen `price_basis=indicative` und die explizite Art `published_tariff` oder `free_access`. Regulärer Erwachsenenpreis und rechnerischer Gruppenpreis sind getrennt; `availability=published_tariff_not_ticket_availability` und `date_confirmed=false` verhindern eine Verfügbarkeitszusage. Die Reisedaten werden als Anfrageparameter gespeichert, nicht als belegter Besuchstermin ausgegeben. Reguläre Tarife werden konservativ nach einem Tag als veraltet markiert; kurzlebige Unterkunfts-/Bahntarife nach zehn Minuten. Eine erneute Prüfung liest die Quelle erneut.

Unbekannte Eintrittspreise bleiben unbekannt. Reiseführer-Angaben über kostenlosen Zugang gelten nicht als offizielle Bestätigung. Nicht belegte Wander-, Strand-, Bar- oder Veranstaltungskosten werden weder null gesetzt noch geschätzt. Für terminabhängige Sonderveranstaltungen stehen die fehlenden Informationen ausdrücklich neben dem allgemeinen Tarif. Ein automatischer Veranstaltungskalender oder frei erfundenes Barbudget wurde nicht ergänzt.

Das Hauptbudget umfasst je Szenario nur ausgewählte Unterkunft, ihre Pflichtkosten und genau eine Hin-/Rückreise. Bekannte Teilsummen tragen ihre fehlenden Kosten und erhalten keinen abschließenden Budgetstatus. Aktivitäten und Verpflegung bleiben außerhalb. Unterschiedliche Verkehrsmittel werden niemals addiert.

Die PDF beginnt den Transportabschnitt mit Auto/Zug/Flug, gemeinsamem konkretem Zeitraum, Gruppen-/Personenpreisen, Leistungen, Lücken und Preisstand. Es folgen getrennte Reiseszenarien und die Einzelheiten. Auto zeigt Streckenabschnitte, Fahrzeuge und Kraftstoffannahmen. Bei Bahn sind Datum, Bahnhof, Fahrzeit, Umstiege und gelieferte Tarifbedingungen sichtbar. Verbindungszeiten sind ausdrücklich keine vollständigen Tür-zu-Tür-Zeiten; unbekannte Zubringer werden nicht als null angenommen. Beim Auto sind Pausen, Ortszugang und Reserve geschätzt. Kein unvollständiger Preis wird als Sieger bezeichnet.

## Offene Flug- und Abdeckungsgrenzen

Norwegian und Transavia wurden erneut praktisch geprüft: beide HTTP 403. Es wurde keine Sperre umgangen. Weitere bereits am selben Tag geprüfte Anbieterbedingungen, robots-Regeln und kostenlose API-Zugangshindernisse sind in [ANGEBOTSRECHERCHE.md](ANGEBOTSRECHERCHE.md) dokumentiert. `FlightAccessDiagnostics` ist weiterhin eine Zugangsdiagnose, kein funktionierender Flugpreisadapter. Daher sind Flugpreise, Gepäck, Flughafenauswahl, Umstiege und Transfers nicht bestätigt. Vorausgefüllte Links zählen nicht als Preisbeleg.

„Im Browser unterstützen“ öffnet nur auf Klick die Quelle. Manuelle Preise werden nicht automatisch importiert und Zugangsdaten nicht erfasst. „Quelle überspringen“ überspringt die entsprechende noch ausstehende Kategorie; ein gerade laufender begrenzter HTTP-Aufruf wird damit nicht rückwirkend aufgehoben. Unabhängige Kategorien laufen weiter; Abbrechen stoppt die gesamte Recherche. Gezielte Aktualisierung kann eine zuvor übersprungene Kategorie erneut prüfen.

Keine Schlüssel erforderlich, keine Konten angelegt, keine kostenpflichtigen Dienste, keine Buchungen oder Reservierungen. Vollständige europäische Unterkunftsabdeckung, Mehrzimmerangebote und Flugpreise bleiben ausdrücklich offen.

## Prüfung

Automatisch: bestehende Kosten-/Belegungs-/Währungs-/Abbruchtests plus Rangfolge der Preisziele, drei Modi bei Auto-only-Snapshots, getrennte Szenarien, unbekannt versus kostenlos, offizielle Tarifselektoren, fehlende Terminbestätigung, Tarifalterung, Speicherung, Export-Preisworker für mehrere Reisen und Browseröffnung ausschließlich auf Klick.

Abschlusslauf: `.venv/bin/python -m unittest discover -q`, 126 Tests erfolgreich; `compileall` und `git diff --check` ebenfalls erfolgreich. Vorhandene uncommittete Änderungen wurden erhalten.

Live: fünf erfolgreiche durchgängige Fälle mit Angebotsdetails und Speicherung im JSON-Bericht. Wiederholung: `.venv/bin/python scripts/live_offers.py --live --case rail-near --case lodging-near --case rail-group-five --case activity-bled --case activity-berlin --output tmp/live-prices`.

Drei PDFs aus echten Recherche-Snapshots unter `output/pdf/Preisvergleich-*.pdf`: Innsbruck, Bahnvergleich und zwei Reisen mit Inhaltsverzeichnis. Alle Seiten wurden mit Poppler gerendert, visuell geprüft und der Text mit pypdf kontrolliert. Die Beispiele bleiben historische Abrufstände; sie werden nicht in normale Suchergebnisse eingespeist.
