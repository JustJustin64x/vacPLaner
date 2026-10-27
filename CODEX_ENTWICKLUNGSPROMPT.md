# Entwicklungsauftrag: Lokaler Überraschungsreise-Planer für Europa

Entwickle dieses Projekt zu einer tatsächlich nutzbaren lokalen Desktop-Anwendung zur automatischen Urlaubsplanung weiter. Implementiere die Funktionen, teste sie und dokumentiere den tatsächlichen Stand. Liefere nicht nur einen Plan oder ein UI-Mockup.

## Ziel und Ausgangslage

Der Nutzer gibt Rahmenbedingungen und Interessen ein. Die Anwendung findet selbstständig passende europäische Reiseziele und erstellt komplette vergleichbare Reisevorschläge mit Anreise, Rückreise, mindestens zwei Unterkunftsalternativen pro Ziel, Kostenübersicht und interessenbasierten Aktivitäten. Der Nutzer muss kein Reiseziel kennen oder eine Suchanfrage formulieren.

Arbeitsverzeichnis: `/Users/justinzimmermann/Documents/vacPLaner`.

Untersuche zunächst den aktuellen Code, lokale Anweisungen, README, PROJECT_LOG und Git-Status. Bewahre vorhandene uncommittete Änderungen. Die bisherige Prüfung ergab:
- Python mit Core, Infrastructure und Entry Points; Tkinter-Dashboard, CLI und HTTP-API.
- Vorhandene Adapter simulieren Flug- und Bahnangebote, berechnen Autorouten aus Luftlinien und verwenden feste Unterkunfts-/Aktivitätskataloge mit teilweise erfundenen Fallbacks.
- Ortsauflösung ist auf wenige Städte beschränkt; Zielentdeckung fehlt.
- Speicherung erfolgt nur im Arbeitsspeicher.
- Bestehende Tests belegen keine funktionierende Live-Anbindung.

Du darfst Architektur und Oberfläche ändern sowie kostenlose Bibliotheken einsetzen. Nutze brauchbare bestehende Fachlogik weiter. Bevorzuge Python, ein geeignetes Desktop-Framework und SQLite, sofern die Untersuchung keinen guten Grund für etwas anderes ergibt. Das Ergebnis startet als Desktop-Anwendung; ein separat zu bedienender Browser oder Cloud-Dienst ist keine Voraussetzung. Primärplattform ist der vorhandene Mac. Halte Provider, Fachlogik, Speicherung und Oberfläche getrennt.

## Verbindliche Grenzen

- Zunächst private Nutzung auf einem lokalen Rechner. Keine Benutzerkonten, Serverbereitstellung oder Mehrbenutzerarchitektur erforderlich.
- Deutsch, Euro, Kilometer; Datenformate und Zeitzonen korrekt behandeln.
- Laufende API-, Hosting-, Scraping- und KI-Kosten müssen strikt 0 Euro betragen. Keine Kreditkarte, kostenpflichtigen Testphasen, automatischen Upgrades oder Dienste mit möglicher kostenpflichtiger Überschreitung voraussetzen. Ein lokaler Zähler allein macht einen kostenpflichtigen Dienst nicht zulässig.
- Kostenlose API-Schlüssel sind erlaubt. Registrierung nur, wenn notwendig; Konten legt der Nutzer selbst an. Ohne Schlüssel muss die Anwendung mit verfügbaren Quellen und transparenten Fallbacks benutzbar bleiben.
- Keine kostenpflichtigen LLM-Aufrufe. Zielauswahl und Ranking funktionieren ohne KI. Lokale KI ist kein Bestandteil der ersten Version und darf keine Voraussetzung sein.
- Keine Buchung oder Zahlung innerhalb der Anwendung; nur Informationen, Vergleich und Links.
- Keine erfundenen Unterkünfte, Angebote, Verfügbarkeiten, Bewertungen, Fahrpläne oder Buchungslinks. Demo-Daten dürfen ausschließlich in einem klar getrennten Test-/Demomodus vorkommen.

## Eingaben und Filter

Erstelle eine verständliche Eingabemaske mit sinnvollen Standardwerten und optionalen Detailfiltern:
- Startort, optional genaue Startadresse; ohne Adresse die Ungenauigkeit der Tür-zu-Tür-Zeit ausweisen.
- Zielgebiet innerhalb Europas: Länder, Regionen oder gesamte unterstützte Europaauswahl; Ausschlüsse ermöglichen. Ein Ziel muss nicht eingegeben werden.
- Reisejahr, früheste Abreise und späteste Rückkehr bzw. Monat, Reisedauer und optionale Dauerspanne. Tage und Übernachtungen eindeutig unterscheiden; Beispiel: 7 Kalendertage können 6 Nächte bedeuten. Alle Reisen müssen in den gewählten Zeitraum passen.
- Anzahl Erwachsener und gewünschte Zimmeranzahl. Keine Kinder-/Altersmodelle in Version 1 nötig.
- Gesamtbudget für die ganze Gruppe mit weicher Grenze. Budgetnahe günstigere und teurere Ergebnisse sind erlaubt, Abweichungen sichtbar.
- Interessen als auswählbare, gewichtbare Faktoren: Wandern, Baden/Strand/See, Natur, Berge, Kultur, Städte, Feiern/Nachtleben, Restaurants, Veranstaltungen und kostenlose Unternehmungen. Klima-/Temperaturpräferenzen optional; saisonales Klima nicht als konkrete Wettervorhersage ausgeben.
- Gewichtung von Preis, Reisezeit, Komfort und Interessenpassung; normalisiere Gewichte nachvollziehbar und behandle alle Gewichte gleich null sinnvoll.
- Verkehrsmittel Auto, Zug und Flug einzeln aktivierbar, maximale Reisezeit optional.
- Benzinautos: Fahrzeuganzahl, Sitzplätze, Verbrauch je Fahrzeug und Benzinpreis; sinnvoll vorbelegen und bearbeitbar machen. Gruppen müssen in die Fahrzeuge passen.
- Unterkunftstypen Hotel, Ferienwohnung und Camping; Zimmerbedarf, Küche, Frühstück, Pool, Parkplatz, Haustiere erlaubt, kostenlose Stornierung und maximale Zentrumsentfernung. Pflichtkriterien von Wünschen unterscheiden. Fehlende Ausstattung ist unbekannt und kein bestätigtes Merkmal.
- Am Anfang Reiseart anzeigen: „Ein Ziel“ ist umgesetzt; „Mehrere Ziele“ ist sichtbar als spätere Erweiterung, aber deaktiviert. Keine Rundreiseimplementierung in Version 1.

## Automatische Ziel- und Terminsuche

Implementiere eine mehrstufige Suche: Kandidaten aus einer nachvollziehbaren europäischen Datenbasis erzeugen, nach harten Kriterien filtern, Interessenpassung grob bewerten, Datumsoptionen begrenzen, für geeignete Kandidaten Unterkünfte und Anreise recherchieren und daraus mehrere unterschiedliche Reisevorschläge erstellen.

Vermeide eine unkontrollierte Vollsuche aller Orte, Tage und Anbieter. Verwende ein begrenztes Abfragebudget, Caching für stabile Ortsdaten und eine konfigurierbare Vorauswahl. Dokumentiere die tatsächliche geografische Abdeckung. Eine kuratierte, quellenbasierte Ausgangsliste realer Orte ist zulässig; keine auf neun Städte begrenzte Demo als Europasuche ausgeben. Zeige bei eingeschränkter Suche an, dass nicht alle Möglichkeiten untersucht wurden; behaupte kein globales Preisoptimum.

Jeder Vorschlag erklärt konkret, weshalb Ziel, Zeitraum, Unterkunft und Verkehrsmittel passen. Liefere mehrere sinnvolle Varianten, beispielsweise preisorientiert, zeitorientiert und ausgewogen. Keine überwiegend identischen Kombinationen. Nach dem Austausch einer Unterkunft oder Transportoption aktualisieren sich Preis, Bewertung und Hinweise.

## Anreisevergleich und Kosten

Vergleiche Hin- und Rückreise über Auto, Zug und Flug einschließlich Zubringer, Transfer, relevanter Wartezeiten und Unterkunftsanbindung, soweit Daten verfügbar sind. Gib fehlende Abschnitte und Zeitannahmen an. Flug-/Bahn-Spezialtarife, BahnCard und umfangreiche Gepäckfilter sind für die erste Version nicht erforderlich; erkennbare Einschränkungen der ausgewählten Tarife bleiben sichtbar.

Auto: echte Straßenroute und Fahrzeit bevorzugen. Benzin für alle Fahrzeuge, Hin-/Rückfahrt, Maut, Vignetten und Parken berücksichtigen. Zeitlich gültige Vignetten nicht automatisch doppelt kaufen, wenn eine beide Richtungen abdeckt. Maut und Parkkosten ohne belastbare Quelle als unbekannt oder begründete Schätzspanne anzeigen. Fehlende Kosten sind niemals automatisch kostenlos. Eine Luftlinienrechnung darf nicht als echte Route erscheinen. Verhindere unbrauchbare Kombinationen wie Hinfahrt im eigenen Auto und Rückflug ohne Rückführung des Autos.

Budgetrelevanter Gruppenpreis: Hin-/Rückreise einschließlich relevanter Nebenkosten und Transfers plus Unterkunft für die gesamte Gruppe und den gesamten Aufenthalt einschließlich bekannter Pflichtgebühren. Unterschiede zwischen Preis pro Person, Zimmer, Bett, Stellplatz, Nacht und Aufenthalt korrekt normalisieren. Campingausstattung/-belegung nicht stillschweigend voraussetzen. Zimmeranzahl und Belegung müssen zur Anfrage passen.

Verpflegung und Aktivitäten als separate optionale Zusatzkosten oder Durchschnittsbereiche anzeigen. Sie gehören ausdrücklich nicht in den Budgetvergleich. Weise etwa „Reisebasis“, „optionale Ausgaben vor Ort“ und ggf. „Gesamtschätzung inkl. Extras“ getrennt aus.

Verwende Dezimalarithmetik, nachvollziehbare Rundung und Quellen für Wechselkurse. Unbekannte Preise bleiben unbekannt. Berechne für vollständige Daten einen Gesamtpreis, für geeignete Annahmen eine sichtbar geschätzte Spanne und ansonsten eine bekannte Teilsumme mit fehlenden Positionen. Ein unvollständiger Preis darf weder als vollständiger Gesamtpreis noch als sicher budgetkonform erscheinen. Ranking darf fehlende Preise nicht durch vermeintliche Billigkeit belohnen.

## Unterkünfte und Aktivitäten

Pro vollständig recherchiertem Ziel mindestens zwei unterschiedliche reale Unterkünfte anbieten, sofern auffindbar. Verschiedene Unterkünfte haben Vorrang vor dem Vergleich derselben Unterkunft über mehrere Portale. Anbieterübergreifend dieselbe Unterkunft erkennen und vergleichbare Angebote zusammenführen, ohne verschiedene Zimmer, Stornierungsbedingungen oder Verpflegungsleistungen gleichzusetzen.

Zeige Name, Typ, Lage, Entfernung, relevante Ausstattung, Gruppen-/Aufenthaltspreis, Bedingungen, Datenstatus und Anbieterlink. Ein aus Geodaten bekannter Unterkunftsname beweist keine Verfügbarkeit zum Reisedatum. Bei weniger als zwei Ergebnissen andere Ziele versuchen und verbleibende Lücken ehrlich anzeigen; keine künstlichen Alternativen erzeugen.

Aktivitäten passend zu Interessen vorschlagen, einschließlich kostenloser Aktivitäten, Wandern, Bademöglichkeiten, Kultur, Nachtleben und gegebenenfalls zeitlich passenden Veranstaltungen. Mit Beschreibung, Lage, Link und soweit bekannt Preis und Dauer. Kein automatischer Tagesplan erforderlich. Unbekannter Eintritt ist nicht gleich kostenlos; veranstaltungsbezogene Daten müssen zum Reisezeitraum passen.

## Datenquellen und Webseitenabruf

Recherchiere vor der Integration aktuelle offizielle Dokumentation, Nutzungsbedingungen, Datenabdeckung, Limits und Zugangsanforderungen. Erstelle `docs/DATENQUELLEN.md` mit Quellen-URL, Prüfdatum, Fähigkeiten, Preisstatus, Registrierung, Limits, Lizenz/Attribution, tatsächlichem Integrationstest und Fallback je Anbieter. Unterscheide geprüft, integriert, getestet und nicht verfügbar.

Prüfe geeignete offene Quellen für reale Orte, Unterkünfte als POIs, Interessen und Aktivitäten, z. B. OpenStreetMap/Overpass, Wikidata und Wikivoyage. Prüfe kostenlose Routinganbieter wie openrouteservice sowie geeignete Bahn-/Fahrplanquellen. Diese Namen sind Prüfkandidaten und keine Zusicherung aktueller Eignung. Fahrplandaten sind kein Beleg für Ticketpreise. Geodaten sind kein Beleg für Unterkunftspreise oder Verfügbarkeit. Öffentliche Geocoding-/Kartenserver nicht als unbegrenzte Bulk-Dienste behandeln.

Prüfe gängige Reiseportale, insbesondere Booking, Check24 und Trivago sowie geeignete Bahn-/Flugportale und direkte Unterkunfts-/Tourismusseiten. Implementiere bevorzugt offiziell zugängliche kostenlose APIs. Wenn keine passende API existiert, prüfe einen zulässigen öffentlichen Webseitenabruf: zuerst HTTP und strukturierte Seitendaten, dann bei Bedarf einen im Hintergrund laufenden Browser. Nutze modulare, anbieterspezifische Parser. Verlasse dich nicht auf generische Textsuche nach dem ersten Eurobetrag.

Beachte Nutzungsbedingungen, Zugriffsbeschränkungen, Rate-Limits und Lizenzen. Keine Umgehung von CAPTCHAs, Logins, Paywalls oder technischen Sperren; keine bezahlten Proxys. Bei nicht möglichem Zugriff Anbieter deaktivieren bzw. den vorgesehenen Suchlink-Fallback verwenden und den Grund verständlich nennen.

Jeder Preis trägt Quelle, Abrufzeit, Reisedaten, Personen-/Zimmerbezug, Umfang und Status: aktuell abgerufen, geschätzt, veraltet oder unbekannt. Ein erfolgreicher Seitenabruf allein belegt keine Verfügbarkeit. Aktuelle Preise werden für jede gestartete Suche neu abgefragt; keine permanente Überwachung. Alte gespeicherte Preise bleiben als damaliger Stand sichtbar.

Schätzungen müssen Methode, Grundlage und Unsicherheit besitzen, dürfen keine buchbaren Angebote vortäuschen und benötigen hinreichende Daten. Keine beliebigen pauschalen Hotel- oder Flugpreise nur zum Füllen der Oberfläche.

Wenn Daten nicht abrufbar sind, biete einen funktionierenden Suchlink mit möglichst passenden Parametern. Unterscheide parametrierten Suchlink, allgemeinen Anbieterlink und geprüften Angebotslink. Ein Suchlink allein gilt nicht als vollständig recherchierte Unterkunft oder als erfolgreicher Live-Preisvergleich. Die Anwendung darf bei Ausfall einzelner Quellen weiterarbeiten.

## Desktop-Dashboard und Suchfortschritt

Gestalte eine übersichtliche deutschsprachige Oberfläche mit Filterbereich, Vergleichskarten, Ergebnisdetails, Kostenaufteilung, Unterkunftsalternativen, Aktivitäten und gespeicherten Reisen. Karte optional, wenn sie ohne zusätzliche laufende Kosten sinnvoll integrierbar ist. Technische Architekturbegriffe gehören nicht in die normalen Nutzeransichten.

Die Suche darf mehrere Minuten bis maximal etwa zehn Minuten dauern. Führe Netzwerk-/Browserarbeit außerhalb des UI-Threads aus. Zeige laufend echte Suchphasen, bearbeitete Ziele, gefundene Ergebnisse, verstrichene Zeit und verständliche Quellenprobleme. Keine künstliche Prozentanzeige ohne berechenbare Grundlage. Ergebnisse möglichst schrittweise anzeigen.

Suche muss abbrechbar sein; bei Zeitlimit mit vorhandenen Teilergebnissen enden. Begrenzte Parallelität, Zeitlimits pro Quelle, kontrollierte Wiederholungen und saubere Ressourcenfreigabe vorsehen. Ein verspätetes Ergebnis einer abgebrochenen Suche darf keine neue Suche überschreiben. Die Oberfläche bleibt auch bei langsamen Quellen bedienbar.

## Speicherung und PDF

Speichere mehrere benannte Reisen dauerhaft in einer lokalen SQLite-Datenbank: Suchkriterien, konkrete Daten, Personenzahl, Optionen, Auswahl, Kostenstatus, Quellen und Abrufzeit. Wiederöffnen nach Neustart, Änderungen, Duplizieren und Löschen unterstützen. Suchcache und bewusst gespeicherte Reisen unterscheiden; Schemaänderungen migrationsfähig halten. API-Schlüssel niemals in PDF, Logs oder Git schreiben.

Erstelle über einen Speichern-Dialog eine lokal teilbare PDF mit Reiseziel, Zeitraum, Personen, Anreisevergleich, ausgewählter Unterkunft und Alternativen, Kostenaufstellung, Aktivitäten, klickbaren Links, Zeitstempeln und Schätz-/Datenlückenhinweisen. Keine öffentliche Freigabeplattform nötig. Lange Texte, Umlaute, mehrere Seiten und Drucklesbarkeit visuell prüfen.

## Umsetzung und Prüfung

1. Bestandsaufnahme und kurzer konkreter Implementierungsplan; danach direkt umsetzen.
2. Datenquellen-Machbarkeit früh anhand kleiner echter Abrufe prüfen. Funktionierende Quellen und Lücken dokumentieren, bevor große Integrationen behauptet werden.
3. Suchmodell, Zielauswahl, transparente Kosten-/Rankinglogik und Providerverträge implementieren.
4. Durchgängigen nutzbaren Ablauf mit realen Ziel-/Unterkunftsidentitäten und verfügbaren Transportdaten herstellen; dann Abdeckung und Anbieter erweitern.
5. Desktop-Integration mit Fortschritt/Abbruch, SQLite und PDF fertigstellen.
6. Tests, echten manuellen Suchlauf und visuelle Prüfung durchführen. README und PROJECT_LOG an den tatsächlichen Stand anpassen.

Teste insbesondere Gruppenkosten und mehrere Fahrzeuge, Zimmerbelegung, Tage/Nächte, flexible Zeiträume, Mitternacht/Zeitzonen, Budget ohne Verpflegung/Aktivitäten, unbekannte Preise, Ranking, Deduplizierung, Provider-Ausfall, Quotenbegrenzung, Abbruch und Persistenz nach Neustart. Verwende feste Testdaten für reproduzierbare Parser-/Fachtests; prüfe Live-Quellen separat und datiere die Ergebnisse. Bestehende Tests nicht nur umschreiben, um neue Fehler zu verdecken.

## Konkrete Abnahme

Nutze als Beispiel: Startort Berlin, Europa, fünf Erwachsene, drei Zimmer, 2.000 Euro Gruppenbudget, Interessen Wandern/Baden/Feiern, nächster zukünftiger Juli mit explizitem Jahr, sieben Kalendertage/sechs Nächte, Auto/Zug/Flug aktiviert. Dies sind Testwerte und keine fest eingebauten Nutzerpräferenzen.

Erwarteter Ablauf:
- Die Anwendung wählt ohne eingegebenes Ziel selbstständig passende reale Ziele und konkrete Termine.
- Ein vollständig ausgearbeiteter Vorschlag besitzt mindestens zwei reale, unterscheidbare Unterkunftsalternativen mit passendem Belegungsbezug; fehlende Verfügbarkeit/Preise werden ausdrücklich markiert.
- Auto, Zug und Flug werden soweit verfügbar gegenübergestellt. Eine begründete Empfehlung folgt den Nutzergewichten und berücksichtigt die Datengüte. Nicht vergleichbare Optionen werden gekennzeichnet statt erfunden.
- Ein nachvollziehbarer ungefährer Gruppenpreis bzw. Preisbereich ergibt sich aus belegten Preisen und ausdrücklich gekennzeichneten fundierten Schätzungen; bei unzureichenden Grundlagen erscheint eine Teilsumme mit Lücken.
- Aktivitäten passen zu den gewählten Interessen.
- Der Nutzer kann eine Unterkunft bzw. Anreiseoption ersetzen, die Reise speichern, die Anwendung neu starten und eine lesbare PDF exportieren.
- Während der Suche ist tatsächlicher Fortschritt sichtbar; Abbruch und Ausfälle führen nicht zum Einfrieren.
- Es entstehen keine laufenden Kosten.

Unterscheide im Abschlussbericht klar zwischen vollständig getesteten Funktionen, funktionierenden Fallbacks und verbleibenden Einschränkungen. Ein Demo-Modus oder Suchlinks allein erfüllen die Abnahme nicht. Wenn Null-Euro-Zugänge einen vollständigen Live-Preisvergleich verhindern, implementiere alle übrigen Teile und dokumentiere exakt die betroffenen Quellen/Funktionen; behaupte keine vollständige Erfüllung.

Entscheide technische Details eigenständig und dokumentiere relevante Annahmen. Stelle nur bei echten Blockaden Rückfragen. Gib abschließend Startanleitung, benötigte optionale Schlüssel, Testergebnisse und bekannte Grenzen an.

## Recherchehinweise zur erneuten Prüfung

Diese Quellen wurden bei der Prompt-Erstellung am 27.10.2026 konsultiert; prüfe ihre Aktualität vor der Integration:
- Booking Demand API erfordert Managed-Affiliate-Partnerzugang: https://developers.booking.com/demand/docs/getting-started/prerequisites
- Nominatim-Richtlinien des öffentlichen Servers: https://operations.osmfoundation.org/policies/nominatim/
- openrouteservice-Tarife/Quoten prüfen: https://openrouteservice.org/plans/
- Amadeus-Testdaten sind keine vollständigen Live-Daten; Produktion kann nach Freikontingent Kosten auslösen: https://amadeus4dev.github.io/developer-guides/test-data/ und https://admin.developers.amadeus.com/self-service/apis-docs/guides/developer-guides/faq/

Die Anbieterhinweise sind keine Vorgabe, genau diese Dienste einzusetzen. Die strikte Null-Euro-Grenze und nachgewiesene tatsächliche Nutzbarkeit haben Vorrang.
