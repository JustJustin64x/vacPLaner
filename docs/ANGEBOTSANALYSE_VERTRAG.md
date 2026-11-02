# Schritt 6 – Voruntersuchung und geplanter Angebotsvertrag (02.11.2026)

Vor Implementierung gegen den Repository-Code abgeglichen. Maßgeblich ist der Produktionspfad `DiscoveryService → OpenTravelProvider.research_offers → OfferResearchService → Smoobu/RegioJet/OfficialActivityPrices/FlightAccessDiagnostics`. Kein zweiter Preisablauf, Modellclient oder Laufzeitmanager.

## Tatsächlicher Ausgangsstand

- Smoobu: genau geprüfte Innsbrucker Ferienwohnungen, eine Einheit, datierte Buchungsparameter und Kapazität/Verfügbarkeit; Aufenthaltssumme muss mit allen Preisbestandteilen übereinstimmen. Reinigung ist bereits enthalten. Kein allgemeiner Hotel-/Mehrzimmerzugang.
- RegioJet: öffentlich beobachtete lesende Such-/Detailrouten, zweite Klasse für Erwachsene, getrennte Hin-/Rückgruppentarife, kein vollständiger europäischer Bahnmarkt. Richtungs-/Datums-/Tarif- und Kapazitätsprüfung existieren bereits. Ortszuordnung wählt bislang den ersten Namens-/Alias-Treffer. Tarifbedingungen liegen verschachtelt vor; zusätzliche Zuschläge werden bisher nicht systematisch ausgewiesen.
- Offizielle Eintritte für vier konkrete Einrichtungen: veröffentlichte optionale Tarife, keine datierte Verfügbarkeit; nicht im Hauptbudget. Flug liefert nur Zugangsdiagnose. Suchlinks und Reiseführerangaben sind keine bestätigten Angebote.
- CostItem/Decimal/CostService rechnen bereits deterministisch; unbekannte/veraltete Pflichtkosten sperren Budgetfreigabe. Personen-/Zimmer-/Datumsparameter sind im Snapshot enthalten, alte Angebote bleiben nach Fehlschlag erhalten. Preisablauf hat keinen Livepreis-Cache, nur statische RegioJet-Orte.
- Automatische Preisphase: 32 Abrufe innerhalb Suchrestzeit. Manuelle/Exportpreisprüfung: 40 Abrufe/600 s gemeinsam, bis drei Terminproben im gleichen Kontext. Diese Grenzen werden nicht erhöht.
- KI-Schritte 1–5 verwenden ausschließlich zentrale Config, LocalModelClient mit gemeinsamem Endpunkt-Lock und Runtime-Verwaltung. Neue Verantwortung ist ein Aufgabenservice für Angebotsanalyse; kein weiterer Client/Daemon/Modellmanager.

## Festgestellte Lücken und Änderungen

1. Preisprovider nutzen noch PublicHttpClient mit automatischen Redirects und ohne öffentliche DNS-Bindung/Robots-Allowlist. Sie werden an die bestehende ResearchHttp-Schicht angebunden; deren bestehende Allowlist wird ausschließlich für schon integrierte Preisquellen und notwendige öffentliche Header/Parameter erweitert. Keine Schutzumgehung bei dadurch nicht mehr zugänglichen Quellen. Dokumentation DATENQUELLEN („kein Preisprovider“) ist überholt und wird abgeglichen.
2. Gemeinsame fachliche Zustände/Informationslücken und Quellenstellen fehlen. Core prüft Parameter, Zeiten, Preisbasis, Richtungen, Währung, Zusatzkosten und Widersprüche; Anbieterantworten bleiben die alleinige Preisquelle.
3. Verschachtelte Bedingungen und Leistungsangaben werden als vollständige begrenzte Originalfelder mit Angebots-/Quellenidentität und JSON-Pointer aufbewahrt. Zu lange Felder werden ausgelassen statt sinnentstellend gekürzt. Modell darf nur aufrufgebundene kurze Fundstellen und kontrollierte Kategorien wählen. Programmcode bestimmt alle übernommenen Werte; unverstandene Bedingungen bleiben ausdrücklich Quellenhinweise.
4. Nachrecherche: höchstens eine zusätzliche erneute Anfrage einer bekannten unterstützten Kategorie bei tatsächlich behebbarer Lücke (z. B. fehlende Antwort/Details), maximal vier HTTP-Transaktionen und 15 s aus demselben Kontext. Keine automatisch wiederholten Sperren, keine beliebigen Detailseiten, keine allgemeine Websuche. Unbekannte Angaben ohne unterstützten Abrufweg bleiben offen.
5. Bereits bestätigte aktuelle Preise werden bei KI-Fehler nicht überschrieben. Deterministisch erkannte Fehler können unabhängig von KI die Übernahme unpassender/neuer Werte verhindern. Historische und frische Varianten derselben ID dürfen sich bei Veralterung nicht gegenseitig ungültig machen. Gebührenidentitäten werden einmal gezählt; inklusive/optional/zusätzlich verpflichtend/ungeklärt bleiben getrennt.
6. Bestehende GUI-Preisaktion erhält eine ausdrücklich deaktivierte Option für lokale Analyse. Herkunft, Qualitätszustand, fehlende Bedingungen und begrenzte Auswertung erscheinen in derselben Detailansicht und soweit notwendig im bestehenden PDF. Speicherung nur ausdrücklich, alte Formate bleiben ladbar.

## Feste neue Teilgrenzen

- Ein zusätzlicher Modellversuch je Preisaktion/-Kontext (einschließlich mehrerer Reisen/Terminproben), maximal 15 s einschließlich gemeinsamer Warteschlange, weiterhin zentraler Client und bestehendes Modell.
- Höchstens vier Angebote und zwölf vollständige Quellenausschnitte, höchstens 400 Zeichen je Feld; Gesamteingabe einschließlich Schema am bestehenden konservativen Clientlimit ausrichten. Auswahl/Validierung/Ausgabe ohne freie Texte, Summen oder URLs.
- Höchstens eine gezielte Kategorie-Nachprüfung je Preisaktion, vier Abrufe und 15 s, innerhalb vorhandener 32 beziehungsweise 40 Abfragen und Hauptdeadline. Kein verstecktes Zusatzbudget.
- Sitzungscache mit höchstens 32 Analysen, Schlüssel über Vertragsversion, Inhalt, Angebotsidentität, Quellenzeit und relevante Kriterien; Cache ist keine frische Anbieterprüfung. Modellantworten/Privatdaten werden produktiv nicht protokolliert.
- Keine neue Rankingformel oder KI-Boni. Nur bestehende deterministische Preis-/Kostenregeln verwenden validierte Informationen. Kein Nachweis eines vollständig buchbaren Pakets.

Live-Erreichbarkeit, Robots und aktuelle Anbietergrenzen werden getrennt geprüft; frühere Preisbelege sind keine Zusage heutiger Verfügbarkeit. Umsetzung/Abnahme werden im Schritt-6-Bericht mit tatsächlichen Einschränkungen dokumentiert.
