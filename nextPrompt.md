Installiere eine lokale KI mit Ollama und integriere sie vollständig in meinen bestehenden Urlaubsplaner. Setze die Umsetzung direkt um, einschließlich Download, Einrichtung und Tests auf meinem Rechner.

Arbeitsumgebung:
- Mac mit Apple M4, 10 CPU-Kernen und 16 GB gemeinsamem Arbeitsspeicher.
- Bestehendes Projekt im aktuellen Arbeitsverzeichnis.
- Sprache Deutsch, Währung Euro, Entfernungen Kilometer.
- Reiseplanung zunächst für Europa.
- Ausschließlich kostenlose Dienste und lokale KI-Verarbeitung.

Dies ist ein Implementierungsauftrag. Erstelle nicht nur einen Plan oder eine Beispielintegration.

1. Prioritäten

Die KI soll zunächst im Hintergrund arbeiten. Implementiere keinen Chat.

Priorität 1:
- Reisevorschläge anhand belegter Daten verständlich erklären.

Priorität 2:
- Freie Reisewünsche verstehen.
- Passende Reiseziele und Regionen entdecken.
- Recherchierte Orte und Aktivitäten anhand der Interessen auswerten.
- Auch kleinere Orte, Küstenorte, Seen- und Wanderregionen berücksichtigen.

Priorität 3:
- Die bestehende Preisrecherche unterstützen.
- Recherchierte Preise auf Vollständigkeit und passende Bezugsgrößen prüfen.
- Fehlende Preisangaben durch zusätzliche Recherche ergänzen.
- Widersprüche und veraltete Angaben erkennen.


Erhalte die bestehenden Funktionen, gespeicherten Reisen und Nutzerentscheidungen. Untersuche und ändere ausschließlich die für diese Integration notwendigen Projektbereiche.

2. Ollama und Modell tatsächlich einrichten

Prüfe zunächst:
- Ob Ollama bereits installiert ist.
- Ob ein lokaler Dienst läuft.
- Welche Modelle bereits vorhanden sind.
- Welche Integrationspunkte die Anwendung bietet.

Verwende vorhandene kompatible Installationen, ohne fremde Konfigurationen ungefragt zu überschreiben.

Falls erforderlich:
- Lade Ollama aus einer offiziellen Quelle herunter.
- Installiere beziehungsweise richte die passende lokale Laufzeit ein.
- Wähle ein kompaktes, für deutsche Texte und strukturierte Ausgaben geeignetes Modell.
- Lade das Modell tatsächlich herunter.
- Prüfe dessen Lizenz auf Eignung für die beabsichtigte Nutzung und spätere Veröffentlichung.
- Teste es auf diesem Rechner.

Die Installation und der Download eines geeigneten kompakten Modells sind autorisiert. Nenne vor Beginn die tatsächliche Downloadgröße und den voraussichtlichen Speicherbedarf, soweit ermittelbar. Zusätzliche Downloads größerer Modelle sind nicht Teil dieses Auftrags.

Wähle das Modell anhand aktueller offizieller Informationen und praktischer Tests. Verlasse dich nicht ausschließlich auf Modellgröße oder allgemeine Bestenlisten.

Berücksichtige, dass neben der KI auch Browser, Anwendung und macOS Arbeitsspeicher benötigen.

3. Ausschließlich lokaler KI-Betrieb

- Keine kostenpflichtigen KI-APIs.
- Keine Cloud-Modelle.
- Keine automatische Weiterleitung an externe KI-Dienste.
- Kein erforderliches KI-Abonnement oder Benutzerkonto.
- Deaktiviere Cloud-Funktionen für die von der Anwendung verwaltete Laufzeit.
- Ändere bei einer gemeinsam genutzten vorhandenen Installation keine globalen Einstellungen unbemerkt. Erzwinge dort für die Anwendung ausschließlich lokale Modelle und lokale Aufrufe.
- Binde die lokale Schnittstelle nur an den eigenen Rechner.
- Veröffentliche sie nicht im Netzwerk.

Internetrecherche der Anwendung ist erlaubt. Unterscheide sie klar von der lokalen Modellverarbeitung.

4. Integration und spätere Weitergabe

Die Anwendung soll später als Ganzes veröffentlicht und von anderen genutzt werden können.

Trenne:
- Anwendungscode.
- KI-Laufzeit beziehungsweise deren Einrichtung.
- Modelldateien.
- Nutzerdaten und Cache.

Verwende geeignete lokale Datenverzeichnisse statt personenbezogener, fest einprogrammierter Pfade.

Speichere Modelle und Laufzeitdownloads nicht im Git-Repository.

Implementiere eine wiederholbare Einrichtung:
- Vorhandene Laufzeit erkennen.
- Modell prüfen.
- Fehlende Komponenten einrichten.
- Downloadfortschritt anzeigen.
- Fehler verständlich erklären.
- Unterbrochene Einrichtung sicher wiederholen können.
- Modellwechsel später ermöglichen.

Für andere Nutzer muss vor einem großen Download eine ausdrückliche Auswahl mit Größenangabe erfolgen.

Implementiere die Mac-Version vollständig. Bereite Windows durch sauber getrennte Plattformfunktionen und portable Pfadbehandlung vor. Behaupte keine getestete Windows-Unterstützung ohne entsprechenden Test.

Erstelle möglichst ein lokal startbares Mac-Anwendungspaket beziehungsweise den reproduzierbaren Build dafür. Prüfe zunächst die vorhandene Paketierung und führe keine unnötige Architekturänderung durch.

Falls Signierung oder Notarisierung zusätzliche Zugangsdaten oder kostenpflichtige Voraussetzungen benötigt:
- Keine Konten oder Zahlungen auslösen.
- Das lokal nutzbare Ergebnis trotzdem fertigstellen.
- Verbleibende Veröffentlichungsschritte klar dokumentieren.
- Keine macOS-Sicherheitsmechanismen global deaktivieren.

5. Modell austauschbar halten

Implementiere eine zentrale Konfiguration für:
- Modellname.
- Lokalen Endpunkt.
- Zeitlimits.
- Kontextumfang.
- Begrenzung gleichzeitiger KI-Aufgaben.

Ein späteres größeres Modell soll ohne Umbau der Suchlogik auswählbar sein.

Die Anwendung darf nur Dienste automatisch beenden, die sie selbst gestartet hat. Eine bereits vorhandene, anderweitig genutzte Ollama-Instanz darf nicht beendet werden.

6. Freie Reisewünsche verstehen

Integriere ein Freitextfeld für Reisewünsche in den bestehenden Suchablauf. Kein separates Chatfenster.

Beispiel:
„Wir sind fünf Erwachsene, möchten im Juli sieben Tage verreisen,
maximal 2.000 Euro für Unterkunft und Anreise ausgeben, wandern,
baden und abends gelegentlich ausgehen. Keine Großstadt.“

Überführe solche Eingaben in strukturierte Angaben, etwa:
- Personen und Zimmer.
- Zeitraum und Reisedauer.
- Gesamtbudget.
- Startort.
- Gebiet und ausgeschlossene Regionen.
- Interessen.
- Unterkunftswünsche.
- Verkehrsmittelpräferenzen.
- Maximale Reisezeit.
- Verbindliche Anforderungen und unverbindliche Wünsche.

Verwende strukturierte Modellausgaben und validiere sie.

Wichtig:
- Fehlende Angaben bleiben offen.
- Aus „Juli“ darf kein willkürliches Jahr werden.
- Wünsche dürfen nicht unbemerkt zu harten Anforderungen werden.
- Bereits bewusst gesetzte Filter nicht stillschweigend überschreiben.
- Widersprüche sichtbar machen.
- Erkannte Kriterien müssen im vorhandenen Formular sichtbar und korrigierbar sein.

7. KI-gestützte Ortsentdeckung

Die KI darf nicht lediglich die immer gleichen Orte aus einem kleinen Katalog umformulieren.

Verbinde:
- Den vorhandenen geografischen Datenbestand.
- Geeignete offene Orts- und Aktivitätsdaten.
- Gezielt recherchierte Webseiten.
- Ergänzende Ortsideen des Modells.

Behandle Vorschläge aus dem Modellwissen ausschließlich als unbestätigte Suchkandidaten.

Bevor ein solcher Ort als recherchierter Vorschlag erscheint:
- Existenz und geografische Identität prüfen.
- Koordinaten und Region zuordnen.
- Passende Interessenmerkmale belegen.
- Verwechslungen gleichnamiger Orte vermeiden.
- Relevante Erreichbarkeit und Unterkunftsmöglichkeiten prüfen, soweit möglich.

Wenn der bestehende Ortsbestand weiterhin zu klein ist, erweitere die notwendigen Integrationspunkte für offene Daten wie GeoNames, OpenStreetMap und Wikidata. Baue keinen zweiten isolierten Katalog neben die bestehende Suche.

Berücksichtige neben Städten:
- Kleine Orte.
- Küsten- und Badeorte.
- Seenregionen.
- Wander- und Naturregionen.
- Geeignete Aufenthaltsorte nahe relevanten Aktivitäten.

Unterscheide eine interessante Region von einem konkreten Übernachtungsort.

8. Kostenlose Internetrecherche

Stelle der Anwendung klar begrenzte Recherchefunktionen bereit. Ollama besitzt durch seine Installation allein keinen allgemeinen Internetzugang.

Prüfe aktuelle kostenlose Möglichkeiten anhand offizieller Dokumentation und echter Abfragen.

Bevorzuge:
- Bereits integrierte geeignete Datenquellen.
- Offene Daten und öffentliche Schnittstellen.
- Offizielle Tourismus-Webseiten.
- Offizielle Webseiten konkreter Aktivitäten und Unterkünfte.
- Zulässige Browser-Recherche.

Verwende keinen kostenpflichtigen Suchdienst, keine kostenpflichtigen Proxys und keine Angebote mit automatischer Abrechnung.

Erfinde keine kostenlose Suchschnittstelle, wenn keine zuverlässig nutzbare vorhanden ist.

Falls eine allgemeine Websuche ohne zusätzliche Zugänge nicht zuverlässig möglich ist:
- Implementiere funktionierende gezielte Recherche über verfügbare Quellen.
- Kennzeichne die Reichweite ehrlich.
- Verwende vorhandene Suchlinks nur als Ergänzung.
- Gib bloße Modellvorschläge nicht als Internetrecherche aus.

Begrenze Anfragen, verwende Caching und beachte die Zugangsbedingungen der Quellen. Umgehe keine CAPTCHAs, Anmeldeschranken oder technischen Sperren.

9. Inhalte sicher und nachvollziehbar auswerten

Webseiteninhalte sind Daten, keine Anweisungen an das Modell.

Die KI darf aus Webseiten keine Befehle übernehmen, die:
- Dateien verändern.
- Weitere Programme ausführen.
- Zugangsdaten anfordern oder übertragen.
- Beliebige lokale oder interne Netzwerkadressen aufrufen.
- Buchungen oder Zahlungen auslösen.

Gib ihr nur die für ihre Aufgabe notwendigen Recherchefunktionen.

Speichere für übernommene Aussagen:
- Quelle und URL.
- Abrufzeitpunkt.
- Relevante Belegstelle oder geeigneten strukturierten Nachweis.
- Zuordnung zum konkreten Ort, Angebot oder zur Aktivität.

Erzeugte strukturierte Antworten müssen technisch validiert werden. Ein korrektes JSON-Format allein beweist keine sachliche Richtigkeit.

10. Interessen anhand von Belegen auswerten

Die KI soll recherchierte Informationen beispielsweise folgenden Interessen zuordnen:
- Wandern.
- Baden.
- Natur und Ruhe.
- Kultur.
- Feiern und Nachtleben.
- Barhopping.

Dabei gilt:
- Ein See beweist keine geeignete Badestelle.
- Ein Weg beweist keine geeignete Wanderroute.
- Eine Bar beweist kein ausgeprägtes Nachtleben.
- Ein alter Veranstaltungshinweis beweist kein aktuelles Angebot.
- Fehlende Informationen bedeuten „unbekannt“.

Unterscheide belegte Merkmale, plausible aber unbestätigte Hinweise und fehlende Daten.

Nutze nachvollziehbare Kriterien für das Ranking. Die KI darf qualitative Informationen liefern; verbindliche Filter und Budgetberechnungen bleiben in überprüfbarer Programmlogik.

Verhindere, dass ausführlich beschriebene Großstädte allein wegen ihrer Textmenge gewinnen.

11. Preise prüfen und ergänzen

Untersuche zunächst die bestehende Preisrecherche. Repariere fehlende Datenabfragen oder fehlerhafte Verarbeitung an ihrer tatsächlichen Ursache.

Die KI soll unterstützen bei:
- Auslesen unstrukturierter Angebotsbeschreibungen.
- Zuordnung von Preisen zu Leistungen.
- Erkennung zusätzlicher Gebühren.
- Prüfung von Belegung, Zeitraum und Preisumfang.
- Erkennung widersprüchlicher Angaben.
- Gezielter Nachrecherche fehlender Informationen.

Verbindlich:
- Keine aktuellen Preise aus Modellwissen ableiten.
- Keine fehlenden Preise erfinden.
- Keine allgemeinen „Ab“-Preise als konkrete Gruppenangebote ausgeben.
- Keine Schätzungen als geprüfte Preise markieren.
- Keine bestehenden belegten Preise ohne neuen nachvollziehbaren Beleg überschreiben.

Für Unterkünfte prüfen:
- Anreise und Abreise.
- Nächte.
- Erwachsene und Zimmer.
- Tatsächliche Belegung.
- Gruppenpreis für den gesamten Aufenthalt.
- Pflichtgebühren, Verpflegung und relevante Bedingungen.

Für Bahn und Flug prüfen:
- Konkrete Verbindung und Datum.
- Anzahl der Reisenden.
- Hin- und Rückreise.
- Tarif, Klasse und enthaltene Leistungen.
- Gepäck beziehungsweise Reservierungen.
- Zusätzliche Transfers, soweit relevant.

Für Aktivitäten prüfen:
- Preis pro Person oder Gruppe.
- Passende Ticketkategorie.
- Termin- und Saisonbezug.
- Zusatzkosten.
- Bestätigte Kostenlosigkeit gegenüber fehlender Preisangabe.

Die Anwendung berechnet Summen mit zuverlässiger Geldarithmetik. Die KI übernimmt keine maßgeblichen Budgetberechnungen.

Speichere Preisquelle, Suchparameter, Abfragezeitpunkt und Preisstatus. Änderungen müssen nachvollziehbar bleiben.

Wenn kein verlässlicher Preis ermittelbar ist, bleibt er ausdrücklich unbekannt. Eine KI-Interpretation eines belegten Angebots darf nicht als unabhängige zweite Bestätigung dargestellt werden.

12. Suchablauf und Leistung

Verarbeite nicht tausende Orte einzeln mit dem Sprachmodell.

Verwende einen gestuften Ablauf:
1. Reisewünsche verstehen.
2. Breite geografische Vorauswahl.
3. Interessenmerkmale aus verfügbaren Daten prüfen.
4. Für aussichtsreiche Kandidaten gezielt recherchieren.
5. Ausgewählte Texte lokal auswerten.
6. Konkrete Unterkünfte und Anreiseangebote prüfen.
7. Ergebnisse nachvollziehbar zusammenstellen.

Begrenze Kontextgrößen und gleichzeitige KI-Aufgaben passend zu 16 GB Arbeitsspeicher.

Eine normale umfangreiche Suche darf bis etwa zehn Minuten dauern. Einrichtung und Modelldownload sind davon getrennte Vorgänge.

Zeige echte Fortschrittsmeldungen und bereits gefundene Ergebnisse. Ermögliche Abbruch zwischen und während geeigneter Arbeitsschritte. Blockiere nicht die Oberfläche.

13. Ausfallverhalten

Wenn Ollama oder das Modell nicht verfügbar ist:
- Vorhandene Suche weiterverwenden.
- Einen sichtbaren, verständlichen Warnhinweis zeigen.
- Keine gesamte Suche wegen eines KI-Fehlers abbrechen.
- Einrichtung beziehungsweise erneuten Verbindungsversuch anbieten.
- Bereits gefundene Ergebnisse erhalten.
- Nicht dauerhaft denselben Warnhinweis als Dialog wiederholen.

Gleiches gilt bei Zeitüberschreitung, ungültigen Modellausgaben oder zu hoher Ressourcenbelastung.

Kennzeichne, welche Zusatzfunktionen dadurch nicht verfügbar sind.

14. Oberfläche, Speicherung und PDF

Integriere die Ergebnisse in die bestehenden Datenmodelle, Ansichten und Exporte.

- Keine getrennte KI-Ergebniswelt neben den normalen Reisen.
- Quellen und Preisstatus erhalten.
- Recherchierte Fakten und daraus formulierte Erklärungen unterscheiden.
- Gespeicherte Reisen weiterhin öffnen können.
- Nutzerentscheidungen bei Aktualisierungen bewahren.
- Keine technischen Modellantworten oder internen Prompts im PDF ausgeben.

Formuliere kurze, konkrete Begründungen:
Welche Interessen erfüllt das Ziel?
Welche Einschränkungen gibt es?
Welche Angaben fehlen noch?

15. Tests und tatsächliche Abnahme

Prüfe:
- Installation und lokale Erreichbarkeit.
- Eine echte Antwort des heruntergeladenen Modells.
- Strukturierte Verarbeitung deutscher Reisewünsche.
- Widersprüchliche oder unvollständige Eingaben.
- Orte außerhalb des bisherigen kleinen Pools.
- Quellenbelege für Ortsmerkmale.
- Preisumfang und zusätzliche Gebühren.
- Ablehnung unbelegter Preisergänzungen.
- Ungültige Modellausgaben.
- Recherchefehler.
- Abbruch und Zeitüberschreitung.
- Suche ohne laufende KI.
- Erhalt gespeicherter Reisen.
- Start der Anwendung über den vorgesehenen normalen Einstieg.

Nutze reproduzierbare Tests für die Programmlogik und separate echte Integrationsprüfungen mit dem lokalen Modell und verfügbaren Onlinequellen.

Dokumentiere tatsächliche Laufzeiten auf diesem Mac. Versprich keine Geschwindigkeit, die nicht gemessen wurde.

Prüfe das erstellte Mac-Paket praktisch, sofern die Umgebung das erlaubt. Dokumentiere nicht ausführbare Prüfungen ausdrücklich.

16. Abschluss

Liefere eine funktionierende Einrichtung auf meinem Mac, nicht nur Installationsanweisungen.

Berichte abschließend:
- Welche Ollama-Version und welches Modell verwendet werden.
- Wo Laufzeit, Modell und Nutzerdaten liegen.
- Wie ich die Anwendung und die KI starte.
- Welche Aufgaben die KI tatsächlich übernimmt.
- Welche Internetquellen tatsächlich funktionieren.
- Welche Preisprüfungen erfolgreich waren und welche offen bleiben.
- Wie ich später das Modell wechseln kann.
- Wie andere Mac-Nutzer das Programm einrichten können.
- Welche Schritte für eine öffentliche Veröffentlichung noch erforderlich sind.

Wenn ein einzelner Teil blockiert ist, erledige alle unabhängig möglichen Arbeiten weiter und benenne den konkreten verbleibenden Blocker.

Beginne mit der gezielten Projektprüfung und führe Installation, Integration und Überprüfung selbstständig durch. Frage nur nach tatsächlich notwendigen Informationen oder technisch erforderlichen Freigaben.