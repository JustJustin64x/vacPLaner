# Allgemeine Unterkunftssuche: Ziel, Arbeitsplan und Fortschritt

Stand: **17.11.2026** · Status: **C mit echter Familien- und neuer Gruppenquote fortgeführt; D dauerhaft integriert; zusätzliche Betreiberübersichtsvariante live geprüft; native manuelle Sichtabnahme weiterhin technisch blockiert. Aktuelle Abnahme: Abschnitt 11.**

Diese Datei ist die fortlaufende Arbeitsgrundlage. Bei späterer Umsetzung werden je Etappe Ergebnis, geänderte Komponenten, Prüfungen, Messwerte, Grenzen und Entscheidungen ergänzt. Eine Etappe gilt erst nach erfüllter Abnahme als abgeschlossen.

## 1. Verbindliches Ziel und Auftrag

Für einen räumlich eindeutig bestimmten Zielort, den gewünschten Suchradius und die Reisebedingungen werden Unterkünfte aus Verzeichnisquellen gefunden. Jede gefundene Identität erhält einen nachvollziehbaren Prüfdatensatz. Offizielle Websites und ihre Buchungsstrecken werden aus Quellen erschlossen. Wiederverwendbare Adapter bearbeiten unterstützte Buchungssysteme; **keine produktive Hotel-, Orts-, Betreiber-, Objekt- oder Zimmerliste begrenzt die Reichweite**.

Unterkunftsidentität, passendes verfügbares Angebot und bestätigter vollständiger Gruppen-/Aufenthaltspreis sind getrennte Aussagen. Unbekannte Pflichtkosten, Eigenschaften und ungeprüfte Verfügbarkeit bleiben offen. Ein Angebot ist keine Reservierung und keine Garantie für eine spätere Buchung.

Der angehängte Gesamtauftrag bleibt verbindlich. Nach der Planungs-/Lesephase hat der Nutzer die Umsetzung von **A und anschließend B** ausdrücklich beauftragt. Die frühere Empfehlung einer ausschließlich Palatino-spezifischen Produktanbindung ist durch diese Planung ersetzt. Vorhandene Berichte und Beispielhotels bleiben historische Nachweise und Regressionstestfälle.

Rahmen: kostenlos, keine Zahlungsdaten; kostenlose Registrierung wäre grundsätzlich möglich, ist aber nicht Voraussetzung des ersten Ablaufs. Keine Kontoanlage, Buchung oder Aktivierung kostenpflichtiger Dienste. Bestehende lokale KI, gemeinsame Warteschlange und Modellverwaltung weiterverwenden; kein neuer Modellclient. Kein Commit/Push beauftragt.

## 2. Tatsächlich geprüfter Bestand

Codebasis: `95d1b35` auf `main`. Bereits vorhandene uncommittete Änderungen an README/PROJECT_LOG sowie Quellenbericht, JSON und Prüfskript werden bewahrt. Keine einschlägige AGENTS.md in den geprüften Projekt-/Vorfahrenpfaden oder im Projektbaum gefunden. Die folgende Bestandsprüfung war statisch; frühere Tests/Liveabnahmen werden nicht als heute erneut ausgeführt ausgegeben.

| Komponente | Tatsächlicher Stand | Konsequenz |
|---|---|---|
| `DestinationInventory` | Räumlicher SQLite-Index, lokale OSM-Merkmale mit Tags/Quell-ID, Regionsabdeckung und Importhistorie; GeoNames-Orte separat | Weiterverwenden. GeoNames findet Zielorte, liefert aber keine Hotelverfügbarkeit |
| `DestinationImportService.update_region` | Eine gebündelte Merkmalsabfrage über `overpass.private.coffee`, Rechteck bis 1 × 1 Grad, 30-Tage-Cache; auch manuelle PBF-Importe vorhanden | Gezielte Unterkunftsabfrage/Coverage ergänzen. Vorhandene Regionsanreicherung ist noch keine systematische Unterkunftssuche für jeden Zielradius |
| `OpenTravelProvider.places`, `_inventory_places` | Lokale OSM-Einträge und Wikivoyage, `website`/`contact:website` übernommen; begrenzte Zuordnung zu Hotel/Ferienwohnung/Camping | Als Verzeichnisbasis erhalten; Roh-Tags/Websiteherkunft in neuen Prüfvertrag übernehmen |
| `PlaceResearch.collect`, `deduplicate` | Umkreisprüfung, wenige Nachbar-/Unterseiten; bei hinreichenden Einträgen früher Stopp. Dubletten nach ID oder gleichem Namen unter 100 m; Details des zweiten Eintrags gehen dabei verloren | Preisrecherche darf keine Vollständigkeit dieser Auswahl behaupten. Quellen zusammenführen statt verlieren; Unterkunfts-Coverage getrennt von Aktivitäten |
| `DiscoveryService.research` | Pflichtfilter vor Preisprüfung, Kürzung auf **acht** Unterkünfte, datierte Booking-Suchlinks ohne geprüfte Angebote | Vollständige Prüfliste vor Kürzung/Filterverlust anlegen. Acht Einträge dürfen höchstens eine Anzeige-/Vorschlagsauswahl sein |
| `DiscoveryService.discover` | Automatische Preisphase nur für beste `price_targets`; 32 HTTP-Aufrufe im verbleibenden Suchzeitbudget | Ziele außerhalb dieser Preisphase und ihre Häuser explizit als noch ungeprüft ausweisen |
| `OpenTravelProvider.research_offers` | Gemeinsamer Service für Smoobu, Aktivitäten, RegioJet und Flugdiagnose | Diesen Einstieg erweitern, keinen parallelen Preisworkflow bauen |
| `SmoobuOfferProvider` | Innsbruck/Betreiber 71379 und sieben Objekt-IDs fest hinterlegt; nur eine Ferienwohnung, Kinderzahl fest null | Als Bestandsnachweis erhalten, aber nicht als allgemeine Unterkunftslösung weiterführen. Neue allgemeine Strecke darf nicht von dieser Tabelle abhängen |
| `OfferResearchService` | Anbieter erhalten eine Reiseanfrage; Ergebnisse nur unter `offer_searches[category]`. Weiterer Provider derselben Kategorie überschreibt den Kategoriestand; `_apply_lodging` ergänzt neue Objekte derzeit mit `rooms=1` | Pro Unterkunft/Quelle sammeln, Kategorie nur aggregieren; Einheiten und Auswahlidentität korrekt übernehmen |
| `OfferQuery`, `TravelOffer`, `OfferQuality`, `CostItem` | Erwachsene, Zimmer und berechnete Belegung; Beleg-/Preisstatus, Kosten/Frische/Qualitätsprüfung vorhanden. Noch kein Kinder-/Altersvertrag | Verträge weiterverwenden und gezielt erweitern. Keine parallele Budgetrechnung |
| `ResearchHttp`, `OfferSourcePolicy` | DNS-geprüfte und gebundene HTTPS-Verbindungen, Robots, Redirect-/MIME-/Größenlimits; bisher enge feste Hosts/Pfade und Smoobu-Parameter | Transport erhalten; dynamische, herkunftsgebundene Freigaben ergänzen. `PublicHttpClient` ist dafür wegen geringerer Ziel-/Redirectprüfung kein Ersatz |
| `probe_accommodation_access.py` | Separate Prüf-Allowlist mit drei Objekten, festen Zimmern/Terminen; echte Quoten und Fehlerfälle | Testmaterial, **kein allgemeiner Produktadapter** |
| GUI/Presenter | Bestehende Hintergrund-Preisaktion, Events, Abbruch/Generationenschutz; Unterkunftsauswahl per Index, nicht durchgehend stabile ID | Statusliste und stabile Auswahl ergänzen; verspätete Antworten dürfen kein anderes Haus verändern |
| `TripStore` | SQLite-Version 1, JSON-Snapshot-Version 1, getrennte Cache-Tabelle; Arbeit erst ausdrücklich speichern | Alte Reisen lesbar halten, Recherchefortschritt von gespeicherten Reise-Snapshots trennen |
| Lokale KI | `LocalModelClient`, `OfferAnalysisService`, bestehende Erklärungen und gemeinsame Begrenzung | Unverändert als optionale Auswertung; erster vollständiger Ablauf muss ohne Modell funktionieren |

## 3. Recherchierte Quellen und belastbare Grenzen

### Verzeichnisdaten für beliebige Zielorte

**Empfehlung:** lokale OSM-Daten zuerst, Wikivoyage als Ergänzung, bei fehlender/alter räumlicher Abdeckung eine kleine, gezielte OSM-Unterkunftsabfrage. Derselbe Algorithmus gilt für jeden aufgelösten Ort im bisherigen geografischen Produktumfang; neue Unterkünfte benötigen keinen Codeeintrag. Er garantiert weder vollständige Kartierung noch für jeden Ort Treffer.

OSM erfasst Unterkünfte unter anderem über [`tourism=hotel`](https://wiki.openstreetmap.org/wiki/Tag:tourism%3Dhotel), Lage, Anschrift und [`website`](https://wiki.openstreetmap.org/wiki/Key:website). Das sind Verzeichnisangaben, keine freien Zimmer oder aktuellen Preise. Website-Tags können falsch/veraltet sein und müssen vor einer Angebotszuordnung geprüft werden.

Der bereits verwendete Betreiber [Private.coffee](https://overpass.private.coffee/) erlaubt die API-Nutzung ohne Registrierung auch in Anwendungen, fordert faire, begrenzte Nutzung und nennt keine Verfügbarkeitsgarantie. Daher bleibt er der bevorzugte kleine Online-Ergänzungsweg; kein automatischer Wechsel zwischen öffentlichen Servern bei Sperren. Die Regeln anderer Instanzen sind nicht gleichzusetzen: Das [FOSSGIS-Handbuch](https://dev.overpass-api.de/overpass-doc/en/preface/commons.html) warnt vor dauerhafter Backend-Abhängigkeit öffentlicher Instanzen. Große Abdeckung erfolgt über vorhandene explizite Regional-/Dateiimporte, ohne versteckte Massendownloads.

**Heutige begrenzte technische Gegenprobe:** Private.coffee `/robots.txt` lieferte HTTP 404. Eine Unterkunftsabfrage um Bamberg (1.200 m, maximal 15 Ausgabeelemente) und eine unabhängige um Hameln (800 m, maximal zehn) endeten jeweils im bestehenden curl-Zeitlimit (`curl 28`; Hameln gemessen 18,02 s). Keine verwertbaren Unterkunftsantworten, kein Nachweis eines leeren Bestands. Die anschließend unabhängige Beds24-Robots-Prüfung lieferte HTTP 200/Text, 636 Bytes, rund 0,20 s und fünf Sekunden allgemeinen Crawl-Abstand. Keine neuen Hotelpreisabrufe in dieser Planungsphase. Die zwei Overpass-Fehlschläge begründen die frühe Cache-/Fortsetzungsplanung; sie beweisen keine dauerhafte Sperre.

[Nominatim](https://operations.osmfoundation.org/policies/nominatim/) wird nicht zur systematischen Hotel-/POI-Suche zweckentfremdet. Bestehende zurückhaltende Ortsauflösung bleibt getrennt. Ohne Website-Hinweis kann ein vorhandenes eindeutiges Wikidata-Objekt über [P856](https://www.wikidata.org/wiki/Property:P856) ergänzen; Namensähnlichkeit allein genügt nicht. Eine allgemeine kostenlose Websuch-API ist nicht vorausgesetzt.

### Buchungssysteme ohne hotelspezifische Codeänderung

| System / Vertrag | Nachweisstand | Geplante Behandlung |
|---|---|---|
| **Beds24, klassisches Gast-Such-/Auswahlformular** | Vorbericht: echte Einzel-/Mehrzimmerquoten; generische [URL-/Formularparameter dokumentiert](https://wiki.beds24.com/index.php/Category:Developers) | Erste Systemfamilie. Objekt-, Zimmer- und Tarifkennungen ausschließlich aus aktuellen Seiten/Formularen; keine festen Hotels/IDs. Verallgemeinerung auf neue Häuser **noch ungeprüft** |
| **Beds24, responsive Gastseite** | [Konfigurierbare Module/Mehrzimmeroption](https://wiki.beds24.com/index.php/Responsive_Booking_Page); Vorbericht mit Einzelpreisen, Nachtpreis und ungeklärter Einheitenmultiplikation | Eigenständige Variante, zweite Adapteretappe. Keine ungeprüfte Wiederverwendung klassischer Preisfeldsemantik |
| **Smoobu, öffentliche Gaststrecke** | Bestehender Parser objektspezifisch; letzte Regelseite HTML statt Regeln | Erkennen und eindeutig als blockiert/noch nicht allgemein unterstützt ausweisen. Generischer Adapter erst nach nachgewiesenem zulässigem Zugang und Identitätsvertrag |
| **Sonstige direkte Systeme, OTA-Links, reine Anfrageformulare** | Kein allgemeiner passender Preisvertrag geprüft | Links und Variante erfassen; Status unterstützt/unbekannt/anfragepflichtig auseinanderhalten. Kein beliebiger HTML-Preisparser |

Die Anbieter-Host-/Pfad-/Variantenregeln dürfen im Code stehen; die konkreten Hotels und Objektkennungen nicht. Neue Häuser einer abgenommenen Variante laufen ohne Codeänderung durch denselben Adapter. Ein Anbieterlogo ist noch kein Nachweis einer unterstützten Variante.

Kostenfreiheit der konkreten Gastabrufe ist von kommerziellen Gastgeber-/Partnerprodukten zu trennen. Die [Beds24-SaaS-Bedingungen](https://www.beds24.com/en/company/eula-november) sind keine pauschale Lizenz für einen öffentlichen Preisvergleich. Abrufregeln und einschlägige Nutzungsbedingungen bleiben je Quellenweg zu beachten; unklare Zugänge werden nicht still als freigegeben erklärt.

### Grenzen „kostenlos, keine Zahlungsdaten“

- [Booking Demand](https://developers.booking.com/demand/docs/getting-started/prerequisites) verlangt Managed-Affiliate-Zugang/Vertrag und Schlüssel. Kein frei verfügbarer allgemeiner Produktionszugang bestätigt.
- [Hotelbeds](https://developer.hotelbeds.com/documentation/getting-started/) liefert mit Registrierung zunächst Evaluation, nicht automatisch freigeschaltete Produktion.
- [LiteAPI](https://docs.liteapi.travel/docs/getting-a-sandbox-key) beschreibt kostenlosen Sandboxstart, für den Produktionsschlüssel aber eine Kreditkarte; [Preisregeln](https://docs.liteapi.travel/reference/api-pricing-usage-costs) enthalten Nutzungsvoraussetzungen und kostenpflichtige Endpunkte.
- Die [offizielle Smoobu-Konto-API](https://support.smoobu.com/hc/en-us/articles/360003170740-Use-the-Smoobu-API-get-an-API-key-set-up-webhooks-and-sign-your-requests) setzt ein bezahltes Gastgeberkonto voraus. Sie ist kein kostenloser Zugang zu allen fremden Unterkünften.

Folge: Eine breite, sofortige und lückenlose Markt-/Preisabdeckung wird nicht versprochen. Kostenlos sind gezielte zulässige Verzeichnis-/Gastseitenabrufe und lokale Verarbeitung möglich. Betrieb fremder Websites, Sperren, fehlende Daten und Variantenänderungen bleiben externe Abhängigkeiten. Keine Anmeldung löst fehlende öffentliche Preise oder einen unpassenden Zimmervertrag automatisch.

## 4. Durchgängiger Sollablauf

```text
Eindeutiger Zielort + Nutzeranfrage
  → lokale Verzeichnisse + begrenzte Ergänzung / optionale Nutzer-URL
  → alle gefundenen Identitäten mit Herkunft in Prüfliste aufnehmen
  → Dubletten zusammenführen, Lage/Art/Kriterien prüfen
  → Website-Kandidat sicher abrufen, Identität abgleichen
  → belegte Buchungslinks/Einbettungen und Systemvariante erkennen
  → tatsächlichen Bestand und zulässige Auswahl für Anfrage ermitteln
  → Angebot unabhängig prüfen oder präzisen offenen Status setzen
  → bestehende Ergebnisanzeige / Kostenlogik / ausdrückliches Speichern
```

### A. Finden und zuordnen

- Zentrumskoordinate, Suchradius und Unterkunftsarten aus der tatsächlichen Anfrage verwenden. Bestehenden maximalen 50-km-Radius erhalten; keine heimliche Verkleinerung. Grenzüberschreitungen und Länder-/Regionsvorgaben prüfen.
- Lokale RTree-Suche und Verzeichnis-Herkunft weiterverwenden. Unterkunftsbezogene Coverage nach Raum, Kategorien, Quellenzeit und Vollständigkeit des **Abrufs** führen; eine allgemeine Freizeit-Regionsmarkierung genügt nicht.
- Online nur gezielt Unterkunftskategorien abfragen, mit Server-/Antwortgrenzen und exakter anschließender Radiusprüfung. Unvollständige/zu große Antworten als Teilabdeckung behandeln; keine automatischen Raster-Crawls. Regionalimport oder ausdrücklich gestartete weitere räumliche Recherche für große/dichte Gebiete anbieten. Ein Trefferlimit verschwindet nicht hinter einer scheinbar vollständigen Liste.
- Jede tatsächlich eingelesene Unterkunft erhält vor Ranking/Anzeigekürzung eine stabile interne Identität. Quell-IDs bleiben als Aliasse erhalten. ID-Übereinstimmung ist stark; quellenübergreifend Namen, Anschrift und Lage gemeinsam prüfen. Gleicher Betreiber/Domain oder ähnlicher Name reicht nicht. Unsichere Dubletten separat verknüpfen statt zusammenwerfen.
- Optionale Nutzer-URL läuft durch dieselbe Identitäts-/Netzprüfung; sie darf keine harten Raum-/Reisekriterien umgehen. Ohne hinreichenden Standort bleibt die Zuordnung offen.

### B. Offizielle Buchungsquelle erschließen

- Verzeichnis-Website zunächst als **behauptete offizielle Website** behandeln. Name plus belastbare Anschrift/Lage oder eindeutige andere Merkmale abgleichen; Brand-Zentrale von konkretem Haus unterscheiden. Abweichungen/Domainübernahmen offenlegen.
- Begrenzte Homepage und explizit verlinkte Buchungs-/Zimmer-Unterseiten lesen. Links, Form-Actions, Iframes, `data-src`/Lazy-Attribute und explizite strukturierte Widgetkonfiguration auswerten. Keine Ausführung unbekannter Skripte für die erste HTTP-Variante und kein Raten von `/booking`-Pfaden.
- Buchungssystem anhand tatsächlichem Host, Pfad und Vertragsmerkmalen erkennen. Quelle→Betreiber→Objekt→Zimmer als belegte Kette speichern. Betreiberlisten mit mehreren Orten vor Preisübernahme auf das konkrete Haus eingrenzen.
- Neue Unterkunft desselben Systems erfordert neue Laufzeitdaten, keine Code-Freigabe pro Hotel. Unbekannte Systemvarianten und fehlende Links bleiben benannte Ergebnisse.

### C. Dynamischer Zugriff mit bestehenden Schutzmaßnahmen

`ResearchHttp` bleibt der einzige sichere Netzweg für diese Strecke. Die statische Policy wird um auftragsgebundene Freigaben ergänzt, **nicht** durch unbegrenzten Netzzugriff ersetzt:

1. Herkunftsdatensatz/optionale Nutzer-URL erlaubt einen begrenzten Erstabruf des Website-Kandidaten, noch keine Angebotsbestätigung.
2. Eine programmseitige Freigabe bindet Recherche-ID, Unterkunft, beobachteten Ursprung, erlaubten Host/Pfad, Methoden, Parameterherkunft und Laufzeit. Sie wird nicht vom Modell oder einem Webseitenbefehl erzeugt.
3. Wenige explizit beobachtete interne Unterseiten dürfen folgen. Domainwechsel/Weiterleitungen werden erneut auf Herkunft und Rolle geprüft; gleiche Domain allein ist keine Objektidentität. Unsichere Wechsel stoppen die betreffende Kette.
4. Unterstützte externe Buchungsanbieter nutzen weiter systemweite enge Host-/Pfadverträge. Objekt-/Zimmerparameter müssen in dieser Quellenkette beobachtet worden sein. Keine beliebigen GET-/POST-Routen, Abschlussaktionen oder freien Redirect-/Proxyparameter.
5. URL-Normalisierung, sämtliche DNS-Adressen und tatsächlich verbundene IP, Redirects, TLS, Robots, MIME, Download-/Zeitgrenzen, Rate-Limits und Abbruch bleiben wirksam. Kein Fallback auf den weniger restriktiven `PublicHttpClient`; keine lokalen/private/link-local Ziele oder Credentials in URLs.

Erlaubte Netzherkunft und sachlich geprüfte Identität sind zwei getrennte Prüfungen. Ein sicherer Abruf beweist noch keinen richtigen Preis. Für nötige lesende POST-Suchverträge ist später ein eigener enger Methoden-/Bodyvertrag erforderlich; daraus entsteht keine allgemeine POST-Freigabe. Browserverkehr darf diese Schranken ebenfalls nicht umgehen.

### D. Anfrage und Preisprüfung

- `OfferQuery` um eine konkrete Unterkunftsreferenz und explizite Zimmerbelegung ergänzen. Produktive Termine/Personen/IDs ausschließlich aus der Anfrage/Quelle. Bestehende gleichmäßige Belegung darf als **Nutzeranfrage**, nie als Verfügbarkeitsbeleg gelten.
- Zuerst gegen vorhandene Formulargrenzen prüfen; Zimmerkategorien, Mengen, Belegungsregeln und Tarifidentität aus Quelle ermitteln. Kombinationen begrenzt enumerieren, physisch identische/alternativ verkaufte Zimmer nicht doppelt zählen. Ohne ausdrückliche gemeinsame Auswahl keine Gruppenverfügbarkeit bestätigen.
- Das anschließende Preis-/Auswahlresultat muss dieselbe Unterkunft, sämtliche Daten, Zimmer, Personen, Währung und Preisbasis bestätigen. Ein einzelnes Summenfeld oder eine mit `nr` skalierte Antwort reicht nicht. Beim Abbruch der Kombinationssuche wegen Budget lautet das Ergebnis offen, nicht ausgebucht.
- Nacht-/Personen-/Einheitenpreise, Aufenthaltstotal, „ab“-Werte, enthaltene/optionale/zusätzliche Pflichtkosten getrennt behandeln. Keine doppelte Reinigung, unbekannte Pflichtkosten nicht null, keine neue unbelegte Währungsumrechnung. Fremdwährung darf mit Originalbetrag als unvollständig dargestellt werden.
- Harte Eigenschaften brauchen zum gewählten Zimmer/Tarif passende Belege. Insbesondere Gemeinschaftsbad, Frühstück und Stornierung nicht aus einer allgemeinen Hotelseite für jeden Tarif ableiten. Bei fehlendem Beleg höchstens teilweise passend.
- Kinder samt Alter sind im aktuellen Produkt noch nicht darstellbar. In Etappe C den optionalen Anfrage-/Belegungsvertrag ergänzen; bis dahin Erwachsene ausdrücklich als unterstützten Umfang zeigen. Keine Erwachsenen-Suche für eine anders zusammengesetzte Gruppe vortäuschen. „Eigenes Bad“ ebenfalls als explizites Pflichtmerkmal aufnehmen.
- KI ist optional: sie kann begrenzte Quellenausschnitte/Erkennungsmerkmale vorschlagen. Keine KI-Netzfreigaben, Preise, Verfügbarkeit, ID-Erfindung oder harte Merkmalsbestätigung. Bestehender Client und gemeinsame Begrenzung bleiben erhalten.

## 5. Vollständige Prüfliste, Zustände und Fortsetzung

Pro Ziel und konkretem Anfrage-Fingerabdruck wird eine versionierte `lodging_research`-Liste geführt. Jeder Eintrag enthält interne ID, sämtliche Herkunfts-IDs, Lage/Identitätsstatus, beobachtete Website-/Buchungskette, aktuelle Verarbeitungsstufe, Zeitpunkte, Versuche, Angebote, Lücken und Grundcodes. Ergebnisse verschiedener Häuser/Quellen werden nicht unter einer einzigen Kategorie überschrieben.

Eine Unterkunft hat je Anfrage genau einen aktuellen Ergebniszustand; frühere Versuchsergebnisse bleiben getrennt erhalten:

| Ergebniszustand | Bedeutung |
|---|---|
| `pending` / `running` | Noch nicht geprüft / laufende Prüfung |
| `confirmed` | Anfrage, vollständige Auswahl, harte Kriterien und Pflichtgesamtpreis zum Abruf belegt; keine Reservierung |
| `partial` | Preis-/Quellenhinweise vorhanden, aber Pflichtangaben fehlen |
| `no_matching_availability` | Passende konkrete Quelle hat die vollständige Anfrage fachlich korrekt negativ beantwortet |
| `criteria_mismatch` | Nachweislich außerhalb der Kriterien; transparent ausgeschlossen |
| `identity_uncertain` | Ort, Website oder Objekt nicht eindeutig zugeordnet |
| `no_booking_source` | Im erlaubten Umfang keine auswertbare Buchungsquelle ermittelt |
| `unsupported_variant` | Buchungssystem/Variante oder erforderliche Funktion nicht unterstützt |
| `blocked` / `source_error` | Abruf gesperrt / technisch fehlgeschlagen |
| `deferred_budget` / `cancelled` | Wegen Budget noch offen / abgebrochen |
| `interaction_required` | Anmeldung oder Nutzerinteraktion erforderlich; zunächst nur Status/Quellenlink |

Kein technischer Fehler, fehlender Adapter oder „nicht geprüft“ wird zu „ausgebucht“. Ein späterer Fehlversuch löscht keine frühere Quote und erneuert nicht deren Abrufzeit. Preisfrische und letzter Aktualisierungsversuch sind getrennt; alte Quoten werden aus aktuellen Kosten ausgeschlossen.

Anzeige: gefunden (nach belegter Dublettenzusammenführung), abgeschlossen geprüft, laufend, noch offen, bestätigte Angebote, Quellenstand und räumliche Teilabdeckung. Es gilt prüfbar: **Anzahl eindeutiger gefundener Unterkünfte = Summe der aktuellen Zustände**. Die ganze Prüfliste ist erreichbar, auch bei einer kurzen Rangliste/Seitennavigation. Nicht abgerufene Teile eines begrenzten Verzeichnisses sind zusätzliche **Suchabdeckungslücken**, keine erfundenen Unterkunftseinträge.

Anfragewechsel erzeugt neue Jobs; eine laufende Teilantwort ist an Ziel, Unterkunft, Anfragehash und GUI-Generation gebunden. Gewählte Unterkunft über stabile ID bewahren; keine Verwechslung durch neu sortierte Listenindizes.

Fortsetzung bearbeitet offene Stufen mit fairer Reihenfolge und zuletzt wenig bearbeitete Häuser zuerst. Erfolgreiche frische Metadaten werden wiederverwendet. Fehler-Backoff verhindert Dauerversuche; Preise, Sitzungen und alte Negativantworten erhalten eigene Fristen. „Fortsetzen“ versucht nicht automatisch dauerhaft blockierte Quellen erneut; „erneut prüfen“ ist eine ausdrückliche Aktion.

## 6. Budgets, Speicherung und Komponentenschnitt

**Vorgeschlagene Startwerte, in GUI-/Liveabnahme zu bestätigen:** bisherige automatische Preisphase 32 HTTP im Suchrestbudget erhalten; manuell weiterhin 40 HTTP/600 Sekunden für den gesamten gestarteten Preisauftrag. Unterkunfts-Unterbudgets werden daraus abgezogen, nicht zusätzlich pro Haus gewährt. Maximal zwei gezielte Verzeichnisabfragen, zunächst drei Inhaltsseiten je Website, acht Netztransaktionen/90 Sekunden je Haus (gemessene Anpassung auf zwölf und zusätzliche eng begrenzte Identitäts-/Formularschritte in Abschnitt 9) und höchstens vier Kandidatenkombinationen pro Prüfung; gemeinsame Grenzen gewinnen immer. Jede Robots-/Redirect-/lesende Formularanfrage zählt. Ein Homeserver mit fünf/zehn Sekunden Pause bestimmt den realen Durchsatz. Bei ungenügendem Restbudget keine neue Stufe starten und Häuser als offen erhalten.

Keine Zusatzschleifen über alle im Zielsuchpool betrachteten Orte. Für angezeigte Zielergebnisse wird die vollständige gefundene Unterkunftsliste erfasst; Preisarbeit folgt den vorhandenen `price_targets`. Manuelle Fortsetzung arbeitet am ausgewählten Ziel. Bei unbekannter Identität oder hart verletzten Kriterien darf dieselbe Verarbeitungskette früh mit sichtbarem Grund enden.

Metadaten-/Abdeckungscache zunächst sieben Tage, Robots höchstens 24 Stunden, kein langfristiger Preis-/Verfügbarkeitscache; aktuelle Preisgültigkeit weiterhin konservativ höchstens zehn Minuten und gegebenenfalls kürzer laut Quelle. Fehler-Backoff als Startwert 15 Minuten, bei Rate-Limit mindestens serverseitige Wartezeit. Diese Werte sind Planungsentscheidungen, keine Quellen-Frischegarantien.

Recherchefortschritt in eigenem lokalen Job-/Cachebereich, nicht durch automatisches Umschreiben gespeicherter Reisen. Zunächst additive Snapshot-Metadaten mit eigenem `lodging_research.schema_version`; alte Version-1-Reisen ohne Feld laden unverändert. Neue Quellenbelege und Prüfstand erst bei vorhandener Speicheraktion im Reise-Snapshot bewahren. Flüchtige Cookies/Formularsitzungen, Credentials und vollständige Webseiten nicht in Snapshot/Export. Falls eine echte SQL-Schemaänderung nötig wird: versionierte transaktionale Migration und Altformat-Tests statt stiller Neuerstellung.

| Erhalten | Geplant ändern/ergänzen |
|---|---|
| Zielkatalog, räumlicher Index, Regions-/Dateiimport | Unterkunfts-Coverage und gezielter Verzeichniszugriff |
| Wikivoyage-/OSM-Parsergrundlage | Herkunftstreue Zusammenführung; Rohmerkmale für Identitätsprüfung |
| Bestehender Preisaktion-/Worker-/Eventfluss | Prüfliste je Haus, Quelle und Anfrage; Fortschritt/Fortsetzen |
| `ResearchHttp`-Transport und bisherige Schutztests | Auftragsgebundene Website-Freigaben + systemweite Adapterverträge |
| `OfferQuery`, `TravelOffer`, `OfferQuality`, Kosten/Ranking | Objekt-/Belegungsbezug und später Kinder; keine neue Rankingformel |
| Vorhandene GUI/Presenter/TripStore/PDF-Verträge | Stabile Auswahl, komplette Statusansicht, additive Persistenz und knappe Exporthinweise |
| Ollama-Client, Konfiguration, Sperre und Dienste aus Schritten 1–6 | Allenfalls zusätzliche Aufgabe mit bestehendem Client nach stabilem deterministischem Ablauf |
| Smoobu-/Beds24-Beispielnachweise | Nur Regressionen/Fixtures; keine Übernahme der Hotel-Tabellen in neue Produktlogik |

Neue Verantwortlichkeiten: Unterkunfts-Prüfdatensatz im Core; Verzeichnis-/Website-Erkennung und Systemadapter in Infrastructure; eine Orchestrierung unter dem vorhandenen Angebotsservice. Keine direkte Netzlogik in GUI/Core und keine zweite Modellverwaltung. Benennungen werden bei Umsetzung dem Projektstil angepasst.

## 7. Etappen mit Abnahmekriterien

### A – Minimaler Daten- und Sicherheitsvertrag

Umfang: Prüfliste/Zustände, Anfragebindung, Adaptervertrag und dynamische Website-Freigaben, Quelle→Objekt-Herkunft. Bestehende Reise-/Angebotsverträge additiv anbinden. Noch kein großer generischer Browser oder neues Framework.

**Abnahme:** Fixtures mit mehreren Häusern erhalten lückenlos Zustände; andere Unterkunft/Anfrage kann einen Beleg nicht übernehmen. DNS-Rebinding-/Redirect-/interne Ziele und Abschlussaktionen gesperrt. Alte Reisen laden; Kategorieaggregate überschreiben keine Häuser. Tests zeigen, dass keine feste Hotel-ID zur Freigabe nötig ist.

### B – Erster vollständiger integrierter Ablauf: Verzeichnis bis Anzeige

Umfang: vorhandene lokale OSM-/Wikivoyage-Daten plus begrenzte Ergänzung → Identität/Website → generische Beds24-Erkennung → **klassische und begrenzt vorgezogene responsive Auswahlvariante** (Entscheidung und tatsächlicher Vertrag in Abschnitt 9) → tatsächlich bestätigte Auswahl → bestehende GUI, Teilstatus und ausdrückliches Speichern. Mindestens Erwachsene/Einzimmer und die belegbar unterstützte Mehrzimmerkonstellation mitführen. Alle gefundenen Häuser werden registriert, auch fremde Systeme und Budgetreste. Ein funktionierender Preisweg und sichtbare Lücken entstehen in derselben Etappe.

**Abnahme:** normale GUI bedienbar, keine separate CLI als Ersatz. Mindestens drei zuvor nicht im Produktcode hinterlegte Unterkünfte aus mindestens zwei Orten ohne Quellcodeänderung verarbeiten; Verzeichnisfindung für mehrere neue Orte, nicht nur Nutzer-URLs, demonstrieren. Mindestens zwei unabhängige neue Häuser mit echten datierten Auswahlquoten, darunter eine belegte Mehrzimmerquote; weitere Häuser dürfen korrekte offene Zustände haben. Unterschiedliche Termine/Personenzahlen prüfen. Kein Hotelname-/ID-Schalter in Produktion. Kann die gewählte Variante diese Nachweise nicht liefern, bleibt diese Abnahme offen und wird nicht durch feste Sonderfälle ersetzt.

### C – Zimmerkombinationen und vollständiger Anfragebezug

Umfang: dynamischer Bestands-/Kombinationsvertrag, unterschiedliche Zimmerkategorien, Preisbasis, Gebühren, harte Merkmale einschließlich eigenes Bad. Explizite Belegung und optional Kinderalter durch Formular, Anfrage, Adapter und Prüfschicht führen; nicht unterstützte Fälle klar benennen. Der begrenzte Mehrzimmerweg aus B wird erweitert, nicht erneut parallel gebaut.

**Abnahme:** nachgewiesene 2+2+1-Auswahl, fehlendes drittes Zimmer, alternative Tarife desselben physischen Zimmers, Nacht-/Personen-/„ab“-Preis, unbekannte Pflichtgebühr, Gemeinschaftsbad, Stornonegation und Kinder-Altersgrenzen korrekt. Keine Bestätigung durch bloße Multiplikation oder Echo eigener Parameter. Abbruch der Kombinationssuche erzeugt offenen Status, kein negatives Verfügbarkeitsergebnis.

### D – Abdeckung, faire Fortsetzung und robuste Speicherung

Umfang: komplette Listenansicht/Seitennavigation, Suchabdeckung, Cache-/Job-Fortsetzung über Neustart, Altformat-Kompatibilität, neue Sortierung bei stabiler Auswahl. Große Radien/dichte Städte zeigen begrenzte Quellenabdeckung und ermöglichen bewussten Regionalimport. In-Session-Abbruch/Fortschritt müssen bereits in B funktionieren.

**Abnahme:** mehr als acht gefundene Häuser bleiben alle auffindbar; kleines Budget lässt korrekte Restliste zurück. Fortsetzen wiederholt keine frischen erfolgreichen Schritte, versucht keine Buchung und entwertet keine alte Reise. Quellenfehler, neues Datum, Zielwechsel, Schließen/Neustart, geänderte Auswahl, Dubletten und explizites Speichern/Wiederladen geprüft. Zählergleichung für jede Teilausgabe erfüllt.

### E – Zweite Systemvariante und begrenzte weitere Reichweite

Umfang: Beds24-responsive Variante mit eigener Preis-/Bestandsprüfung. Weitere Systemfamilie erst nach eigener Quellenerhebung/Vertragsabnahme; Smoobu-Erkennung bleibt bis zum gelösten Zugang ein transparenter offener Fall. Bei JS-only/Login-Fällen zunächst `interaction_required`/Quellenlink. Eine sichere systemgebundene Browser-Erweiterung ist eine gesonderte Unteretappe; kein freier KI-Agent als automatischer Universal-Fallback.

**Abnahme:** zuvor unbenutzte responsive Häuser ohne Hotel-Codeeinträge, einschließlich Nachtpreis und Anfrage-only/fehlender Mehrzimmerunterstützung. HTTP- und mögliche Browserphase teilen Budgets, Herkunft und Abbruchschutz. Keine Konten, Zahlungen, Sperrumgehung oder Buchungen. Nicht abgenommene Variante bleibt ausdrücklich nicht unterstützt.

### F – Gesamtprüfung und verlässliche Veröffentlichung des Funktionsstands

Umfang: relevante gesamte Regression, Tk-Abläufe, Livevergleich verschiedener Orte/Zeiträume/Belegungen, Offline-/Quellenausfall, Speicherung und bestehender PDF-Export. Ohne lokalen KI-Dienst muss derselbe deterministische Ablauf nutzbar sein.

**Abnahme:** Prüfmatrix trennt Verzeichnisfunde, zugeordnete Websites, erkannte Varianten, vollständig geprüfte Angebote, Teilquoten, negative Verfügbarkeit und offene Fälle. Dokumentierte Quelle, Laufzeit, Abrufzahl, Frische, Ablehnungsgrund; Fixtures/Internet/Modell getrennt. GUI-Reaktionszeit/Abbruch messen und visuell prüfen; technisch gescheiterte Sichtprüfung ehrlich benennen. Neue Häuser einer unterstützten Variante ohne Codeänderung belegt. README/PROJECT_LOG/Quellen- und Fortschrittsdatei stimmen mit Code überein; kein Vollständigkeitsversprechen.

## 8. Offene Annahmen und Entscheidungsgrenzen

| Punkt | Status / Umgang |
|---|---|
| Klassische Beds24-Formulare sind bei mehreren unabhängigen neuen Häusern gleichartig genug | **Ungeprüfte Verallgemeinerung.** Vorbericht beweist nur ausgewählte Objekte. Gate in B; gegebenenfalls klar getrennte Systemvariante, keine Hotel-Sonderlogik |
| Verzeichnis liefert für beliebige Orte ausreichend offizielle Website-Hinweise | **Nicht garantiert.** Coverage und fehlende Website separat sichtbar; optionale Nutzer-URL, lokaler Regionalimport |
| Öffentliche Verzeichnisquelle ist erreichbar | **Externe Abhängigkeit, heute zweimal Timeout.** Lokal zuerst, Teilresultate/Backoff/Fortsetzung; kein Verfügbarkeitsergebnis daraus ableiten |
| Gemeinsame Zimmerverfügbarkeit lässt sich ohne Buchung bestätigen | **Je Variante zu belegen.** Wenn nur Rechnung oder Anfrage möglich ist, höchstens Teilquote |
| Nutzungsbedingungen erlauben jeden künftigen Betreiberabruf/Weitervertrieb | **Nicht pauschal bestätigt.** Nur geprüfte zulässige Quellenwege nutzen; kein Lizenzschluss allein aus Robots. Konkrete unlösbare Berechtigungsfrage gesondert vorlegen |
| Vorgeschlagene Budgets liefern ausreichenden Durchsatz | **Zu messen.** Keine automatische Erhöhung pro Haus. Grenzen offen zeigen und gezielte Fortsetzung anbieten |
| Anmeldung durch KI steigert Preisabdeckung | **Nicht belegt und nicht Basis der Architektur.** Kein Konto-/Credential-Automatismus. Nutzerinteraktion nur bei konkretem Nutzen, nicht als Ersatz für fehlende Quelle |

Für den Plan sind keine zusätzlichen Nutzerantworten nötig: Kostenrahmen, Priorität Unterkünfte und Umgang mit sichtbaren Lücken sind geklärt. Eine Rückfrage wird erst nötig, falls ein erforderlicher Zugang tatsächlich Zahlungsdaten, Vertrag/Berechtigung oder eine wesentliche Änderung des Produktumfangs erfordert. Die aktuelle Freigabe umfasst Etappen A/B. C–F bleiben Folgearbeit; kein Commit oder Push beauftragt.

## 9. Fortschrittsprotokoll

| Datum | Schritt | Ergebnis / Nachweis | Status |
|---|---|---|---|
| 10.11.2026 | Bestand | Such-/Preis-/HTTP-/Probe-/GUI-/Speichercode gelesen; Smoobu-/Probe-Festwerte, Acht-Häuser-Kürzung und Kategorieüberschreibung bestätigt | erledigt |
| 10.11.2026 | Quellen | Offizielle OSM-/Overpass-/Beds24-/API-Dokumentation recherchiert; zwei begrenzte Verzeichnisversuche mit Timeout, Beds24-Robots erreichbar | erledigt, Abhängigkeiten offen |
| 10.11.2026 | Kursentscheidung | Allgemeine Findung und Systemadapter statt Palatino-Produktintegration; bestehende Beispiele ausschließlich Testmaterial | im Plan festgelegt |
| 10.11.2026 | Arbeitsplan | Etappen A–F mit früher Integration, Zuständen, Sicherheit, Budgets und Abnahmekriterien dokumentiert | zur Prüfung vorgelegt |
| 10.11.2026 | Umsetzung A/B | In bestehende Suche/Preisaktion/GUI/Speicherung integriert; 393 Tests. Neue-Häuser-Preisabnahme nicht erfüllt | A technisch geprüft; B offen |
| – | Umsetzung C–F | Nicht umgesetzt; keine Abnahme vorweggenommen | nicht begonnen |

Bei späterem Fortschritt hier ergänzen: Etappe, Commit/Arbeitsstand, konkrete Änderungen, ausgeführte Testbefehle/Resultate, Livebelege mit Zeit/Quelle, offene Risiken und nächste Arbeit. Fehlschläge erhalten; keine hypothetischen Erfolge als abgeschlossen markieren.

### Umsetzung A/B – laufender Stand

- Begrenzte Overpass-Diagnose: GET und POST, kleine Zähl- und Unterkunftsabfragen, 1–2 MB Antwortgrenze, 32 s pro Abruf. Alle vier Versuche curl 28; DNS/TCP/TLS erfolgreich (TLS etwa 0,08–0,10 s), kein erstes Antwortbyte. POST löst das Problem in diesen Versuchen nicht. Daten unter tmp/lodging-general/diagnostics.json. Keine leere Ergebnismenge oder dauerhafte Sperre daraus abgeleitet.
- Vor Adapterarbeit tatsächlichen lokalen Findungsweg geprüft: 487.248 vorhandene OSM-Merkmale; räumliche Abfragen liefern unter anderem Unterkünfte in Rostock, Tartu und Binz mit echten Quellen-IDs und Website-Hinweisen. Lokalbestand nur lesend verwendet. Keine Nutzer-URL als Ersatz für Findung.
- Neue Prüfliste vor der Acht-Häuser-Anzeigegrenze, auftragsgebundene Website-/Formular-Policy mit bestehendem ResearchHttp-Transport, begrenzte Website-Erkennung, generischer klassischer Beds24-Adapter ohne Hotel-/Objekt-/Zimmerlisten sowie vorhandene GUI-Preisaktion/Fortsetzen verbunden.
- Erste integrierte Läufe: Binz 201 gefundene Identitäten, 40 HTTP, 50,726 s; Rostock 44 Identitäten, 40 HTTP Budget (tatsächlich 39). Noch keine neuen Angebotsquoten. Quellenfehler, Websitezuordnung und Budgetreste getrennt erhalten. Die Preis-Abnahmekriterien sind damit ausdrücklich noch nicht erfüllt.
- Bestehende 364 Tests vor weiterer Absicherung bestanden (17,758 s). Erste neue Tests fanden Fehler in der eigenen Testvorbereitung (alte Prüfliste aus Fixture übernommen, fehlender Preis-Scope, JSON-Tupelvergleich); korrigiert, danach 19 neue Tests bestanden. Vollständige Regression nach allen Änderungen und GUI-Abnahme stehen noch aus.

### Abschlussstand A/B vom 10.11.2026

**A ist technisch umgesetzt und geprüft. B ist in den normalen Ablauf integriert, seine verbindliche Live-Preisabnahme ist NICHT erfüllt.** Die vorhandenen Kriterien oben bleiben unverändert. Es wurden weder fehlende neue Preise durch feste Hotelintegration ersetzt noch die erfolgreiche Statusabdeckung als Preisabnahme ausgegeben. Messdaten und begrenzte Einzelbelege: [UNTERKUNFTSSUCHE_AB_PRUEFUNG_2026-11-10.json](UNTERKUNFTSSUCHE_AB_PRUEFUNG_2026-11-10.json).

#### Was im normalen Programm jetzt funktioniert

- Bei der regulären Zielrecherche wird vor der bisherigen Acht-Unterkünfte-Auswahl eine vollständige Prüfliste der tatsächlich gefundenen Einträge angelegt. Gleiche IDs behalten Quellenaliase; verschiedene nahe Häuser werden nicht allein wegen ähnlicher Namen verschmolzen. Alle Einträge sind im neuen Fenster **„Alle Unterkünfte und Prüfstände anzeigen“** erreichbar, einschließlich ausgeschlossener und ungeprüfter Fälle.
- Lokale OSM-/Wikivoyage-Verzeichnisse bleiben Ausgangspunkt. Fehlende lokale Unterkunftsdaten können durch maximal zwei gezielte Online-Verzeichnisversuche ergänzt werden; 15-Minuten-Backoff verhindert die Wiederholung des gegenwärtig fehlschlagenden Dienstes. Kalte Gebiete ohne geeignete lokale Daten bleiben offen. Es gibt keinen neuen generischen Marktbestand und keine garantierte Europaabdeckung.
- Die vorhandene Aktion **„Angebote aktuell prüfen“** verarbeitet über einen allgemeinen Unterkunftsprovider die gefundenen Identitäten. **„Unterkünfte fortsetzen“** bearbeitet bisher wenig bearbeitete, noch offene Häuser zuerst. Kein zweiter GUI-Rechercheworkflow. Ergebniswechsel, Abbruch, Quellengrenzen und stabile Unterkunfts-ID bleiben berücksichtigt.
- Öffentliche Website-Hinweise sind Kandidaten, keine ungeprüften Zuordnungen. Name plus Adress-/Postleitzahl-/Telefon- oder explizite strukturierte Lageangaben werden geprüft. Links, Iframes, Lazy-Attribute und explizite Widget-URLs werden ohne Skriptausführung erkannt. Andere Betreiber/Orte bleiben unbestätigt.
- Auftragsgebundene, exakte URL-Freigaben verwenden weiter ResearchHttp mit DNS-/Peer-/TLS-, Robots-, MIME-, Größen-, Redirect- und Budgetprüfung. Beobachtete Beds24-Objekte und Formular-Zimmerfelder ersetzen feste Hotel-/Objekt-/Zimmerlisten. Keine freie Netzwerkfunktion für Modell oder Webseiteninhalte.
- **Unterstützter Preisvertrag:** klassisches Beds24-Gastformular in EUR mit tatsächlich auswählbaren Mengen, begrenzt darstellbarer Erwachsenenbelegung und gemeinsam bestätigter Auswahl. Angefragte Daten, sichtbare Belegung, Zimmerzeilen, Einzel-/Zeilensummen und Gesamtsumme sowie Objektidentität werden geprüft. Keine Gästedaten und kein Abschluss-POST. Mengen ohne Bestand, deaktivierte/nicht verfügbare Zimmer, andere Daten/Objekte, Nachtpreisvarianten und widersprüchliche Summen werden nicht als Quote akzeptiert.
- Ein Prüfturn fragt höchstens eine konkrete Kombination pro Haus ab. Weitere Kombinationen, Kinder und responsive Beds24-Verträge sind noch nicht abgenommen. Für jede ausgegebene Quote bleibt Pflichtkostenvollständigkeit offen, solange sie nicht ausdrücklich belegt ist. Deshalb wurde auch der echte Kontrollpreis nur als Teilangebot ausgegeben; unbekannte Pflichtkosten gelangen nicht als null ins Budget.
- Booking.com-/OnePageBooking-/Smoobu- und weitere explizite bekannte Systemlinks können erkannt werden, aber haben dadurch keinen Preisadapter. Unbekannte Varianten bleiben offen. Der frühere hotelspezifische Smoobu-Parser ist für Nachweise/Regression erhalten, begrenzt aber nicht mehr den neuen produktiven Unterkunftsprovider.
- Angebotsergebnisse mehrerer Provider derselben Kategorie werden aggregiert statt überschrieben. Eine ungeprüfte Unterkunft wird nicht durch den Erfolg eines anderen Hauses als nicht verfügbar entwertet. Arbeitskopie und ausdrücklich gespeicherter Snapshot bleiben getrennt; alte Version-1-Reisen laden weiter. Fortsetzung über einen vollständigen Anwendungsneustart ohne gespeicherte Arbeitskopie gehört weiterhin zu D.

#### Tatsächliche Findungs-, Status- und Preisabdeckung

Alle folgenden Verzeichnisfunde stammen aus dem bereits vorhandenen regionalen OSM-Bestand (überwiegend Abrufstand 30.10.2026), mit Quellen-IDs und realen Website-Hinweisen. Sie sind **keine frisch erhobene Markt-/Verfügbarkeitsliste**. Je Ziel wurden 3 km und Hotel/Ferienwohnung angefragt. Andere gefundene Unterkunftsarten bleiben als Kriterienabweichung sichtbar. Die regulären DiscoveryService-/OpenTravelProvider-/OfferResearchService-Wege wurden mit separatem temporärem Reisespeicher verwendet; die eigentliche Nutzer-Reisedatenbank wurde nicht geöffnet.

| Fall | eindeutige Funde | Websites zugeordnet | erkannte Systeme/Varianten | Angebotsversuche | neue bestätigte / Teilangebote | HTTP verwendet / Budget | Sekunden Preisphase |
|---|---:|---:|---|---:|---:|---:|---:|
| Binz, erster abschließender Lauf | 201 | 6 | 2 OnePageBooking-Linkfälle | 0 | 0 / 0 | 40 / 40 | 50,223 |
| Binz, Fortsetzung derselben Anfrage | 201 | 12 insgesamt | 3 OnePageBooking-Linkfälle insgesamt | 0 | 0 / 0 | 40 / 40 zusätzlich | 47,708 |
| Rostock | 44 | 6 | keine im damaligen Erkennungsstand | 0 | 0 / 0 | 39 / 40 | 67,912 |
| Stralsund | 50 | 6 | 1 Booking.com-, 1 OnePageBooking-Linkfall | 0 | 0 / 0 | 40 / 40 | 56,492 |
| Tartu | 25 | 4 | keine | 0 | 0 / 0 | 30 / 30 | 35,415 |

Über die vier Orte wurden 320 verschiedene Quellidentitäten gefunden. Beispiele ohne Eintrag in produktiven Hotellisten: Appartementhaus Gutenberg in Binz; Hotel Greifennest/Hotel Verdi in Rostock; Aparthotel Markt Fuffzehn/Hotel am Jungfernstieg in Stralsund; Hansa hotell/Hotell Dorpat in Tartu. **Diese Beispiele belegen die allgemeine Findung und Zustandsverfolgung, keine erfolgreichen neuen Preisangebote.** Der Gutenberg-Eintrag verweist bereits auf Beds24, konnte aber nicht hinreichend mit zusätzlichen Standortmerkmalen auf der Gastseite zugeordnet werden; die Anwendung hat daraus keinen Preis übernommen.

| letzter jeweiliger Stand | fehlende/keine auswertbare Buchungsquelle | Identität unklar | technischer Fehler | gesperrt | System/Variante nicht unterstützt | Kriterienabweichung | wegen Budget offen |
|---|---:|---:|---:|---:|---:|---:|---:|
| Binz nach Fortsetzung | 62 | 6 | 9 | 2 | 3 | 2 | 117 |
| Rostock | 13 | 3 | 2 | 3 | 0 | 0 | 23 |
| Stralsund | 13 | 3 | 6 | 0 | 2 | 1 | 25 |
| Tartu | 5 | 1 | 4 | 0 | 0 | 0 | 15 |

Die Zustandszahlen ergeben jeweils exakt die Fundzahl. Quellenfehler umfassen unter anderem DNS-/TLS-Fehler und technische Abruffehler; keine Zertifikatsprüfung wurde umgangen. Die einzelnen Gründe stehen im JSON/GUI. Die Roh-Läufe entstanden an ausdrücklich dokumentierten Arbeitsständen; spätere Schutz-/Erkennungskorrekturen wurden mit Tests abgesichert, nicht als neue Internetabfragen ausgegeben.

**Reichweitenverlust:** 320 Verzeichnisidentitäten sind vorhanden, aber nur ein kleiner Teil der Websiteketten ist innerhalb des Budgets zugeordnet. In den untersuchten neuen Fällen erreichte keine Kette einen abgenommenen klassischen Preisvertrag. Statusabdeckung ist damit vollständig für die Funde, Preisabdeckung dieser neuen Funde null. Das Problem liegt vor allem vor der eigentlichen Preisnormalisierung: fehlende/unklare Websiteketten und andere Systemvarianten.

#### Erfolgreicher echter Kontrollpreis – ausdrücklich kein neuer Abnahmenachweis

Der generische Provider verarbeitete Hotel Palatino anhand des bereits bekannten öffentlichen Tourismus-/Websitehinweises, ohne diesen Namen oder seine Objekt-/Zimmerkennungen im Produktadapter zu hinterlegen. Für 23.–25.11.2026, fünf Erwachsene und drei ausgewählte Zimmer lieferte er eine gemeinsame Quote **534 EUR**: zwei Standardzimmer und ein Luxuszimmer in Einzelbelegung. Das ist eine andere Auswahl als die historischen 436 EUR mit Economy-Zimmer, keine still geänderte Preiserwartung. Pflichtkosten bleiben offen.

Dieser bekannte Kontrollfall belegt, dass der produktive generische Preisweg mit echten Daten funktioniert. Er zählt **nicht** zu den geforderten zwei unabhängigen neuen Häusern. Die Altbeispiele/Fixtures wurden nicht zu neuer Preisabdeckung umetikettiert. Ein vollständiger Pflichtgesamtpreis wurde auch hier nicht bestätigt.

#### Budgets und Bedienbarkeit

Die gemeinsamen Abrufgrenzen wurden nicht erhöht. Die Messungen zeigen, dass 40 HTTP-Aufrufe nicht annähernd alle 201 Binzer Häuser prüfen können. Nach der Fortsetzung wurden **41 zuvor unbearbeitete Häuser** erstmals angefasst und kein bereits bearbeitetes Haus wiederholt; die Budgetrestliste sank von 157 auf 117. Das ist ein tatsächlicher Fortsetzungsnachweis, kein Preisgewinn.

Zusätzlich ist jetzt die reine Bearbeitung auf maximal **64 Häuser je Turn** begrenzt, damit sehr große Verzeichnisse mit vielen fehlenden URLs nicht unbegrenzt CPU-/GUI-Arbeit auslösen. Die Fundliste wird nicht gekürzt. Teilsnapshots werden höchstens fünfmal pro Sekunde gesendet; der vorhandene abschließende Ergebnisweg bleibt erhalten. Der zusätzliche CPU-Schutz liegt oberhalb der tatsächlich verarbeiteten Mengen der gemessenen HTTP-Pässe; 101 lokale Fixture-Häuser prüfen seine faire Fortsetzung unabhängig ohne Netz.

Die normale Tk-Preisaktion mit echtem Kontrollabruf und abschließenden Identitäts-/Zimmerguards dauerte **14,762 s**, verwendete fünf HTTP-Abfragen, führte 629 periodische Test-Callbacks aus und zeigte maximal **0,03443 s Callback-Abstand**. Der vorher ausdrücklich gespeicherte Test-Snapshot blieb unverändert. Das Prüflistenfenster zeigte seinen Eintrag und Quellenbezug. Diese Ein-Haus-Messung beweist keine entsprechende Reaktionszeit einer kompletten 201-Häuser-Live-GUI-Kampagne.

Automatisierte Tk-Tests prüfen alle 20 Fixture-Einträge im neuen Fenster, Fortsetzung über die normale Preisaktion, explizites Speichern, alte Snapshots, geänderte Auswahl und verspätete Antworten. Native Sichtprüfung: das tatsächliche Hauptfenster und die neuen Aktionen wurden gesehen. Eine spätere Aufnahme lieferte nur ein graues Pixel, ein Klickversuch meldete kein verfügbares Fenster; eine vollständige manuelle Klick-/Layoutabnahme des Prüflistenfensters wird deshalb **nicht behauptet**.

#### Tests, erhaltene Fehlschläge und nächste Arbeit

- **393 Tests bestanden, 18,600 s**: alle 364 bisherigen plus 25 neue Unit-/HTTP-/Vertragstests und vier neue Desktoptests. Reale lokale HTTP-Fixtures verwenden den Produktions-Prüfpfad mit ausschließlich testseitigem Wire-Seam; keine Produktionsfreigabe für interne Fixture-Server.
- Geprüft: neue dynamische Objekt-/Zimmerkennungen ohne Produkt-Codeänderung; gleiche Namen/falsche Lage, strukturierte Websitehinweise, reine Webseitenanweisungen ohne Werkzeugwirkung, exakte Grants, DNS/Redirect/Robots, verbotene Abschlussfelder, belegte Mengen, falsche Daten/Objekte/Summen/Währung, deaktivierter Bestand, unabhängige Quote-Identität, unbekannte Gebühren, Kategorieaggregation, mehr als acht Funde, Fairness/CPU-Limit, Cache-Zeitpunkt und Altformat-/Arbeitskopielogik.
- `compileall` und `git diff --check` bestanden. Keine erwarteten realen Preise angepasst, keine bestehenden Tests entfernt.
- Fehlversuche erhalten: Overpass GET/POST ohne Antwortbyte; frühere Website-/Variantenfehler; anfängliche neue Testvorbereitung mit übernommenen Alt-Fixture-Einträgen; erster GUI-Live-Harness ohne Länderfeld im synthetischen Kontrollziel. Korrekturen betrafen Testaufbau beziehungsweise begründete Schutz-/Adapterverträge, keine Umdeutung fehlender Angebote.
- Keine Modellaufrufe, kein neuer Client, Dienststart, Modell-Download, Cloud-Fallback, Konto, Buchung oder Zahlungsdaten. Bestehende uncommittete Änderungen bleiben erhalten. Kein Commit/Push.

**Offene B-Kriterien:** zwei zuvor nicht hinterlegte neue Häuser mit echten datierten Quoten, darunter eine neue Mehrzimmerquote; erfolgreiche Preisprüfungen für verschiedene neue Unterkünfte/Belegungen/Termine; vollständige manuelle GUI-Sichtabnahme. Ein eigenständiger Quellenbericht oder die 393 Tests schließen diese Lücke nicht. Vor einem B-Abschluss müssen geeignete neue Quellenketten eine abgenommene Systemvariante tatsächlich erreichen.

**C–F bleiben:** umfassendere Zimmerkombinationen und Kinder-/Altersvertrag, zusätzliche harte Merkmale und Gebühren-/Stornoprüfung; dauerhafte Jobfortsetzung/Abdeckung und Listenkomfort; responsive Beds24-/weitere Systemverträge und gegebenenfalls begrenzter Browserweg; breite Gesamt-/GUI-/Liveabnahme. Diese Folgeetappen wurden nicht als erledigt markiert. Zuerst bleibt die fehlende B-Preisabnahme sichtbar zu bearbeiten.

## 9. Fortführung von B: neue Preisquoten und verbleibende Sichtabnahme (10.11.2026)

**Aktueller Befund:** Der zuvor offene Neue-Häuser-Preisnachweis ist jetzt erfüllt: drei unabhängig aus Verzeichnisdaten gefundene Häuser in drei Orten, drei datierte Auswahlquoten, darunter eine gemeinsame Zwei-Zimmer-Auswahl. Es gibt weiterhin **keinen vollständig bestätigten Pflichtgesamtpreis**. Die automatisierte GUI-Abnahme funktioniert; die vollständige native manuelle Sichtprüfung ist technisch blockiert. Deshalb wird B hier **nicht uneingeschränkt als abgeschlossen** bezeichnet. Die vorherigen Abschnitte und Null-Preis-Kampagnen bleiben historische Befunde.

### 9.1 Entscheidungen und behobene Engpässe

1. **Responsive Auswahlvertrag aus E vorgezogen.** Die gefundenen neuen Beds24-Quellen liefern nicht den klassischen `sr1`-/Tabellenvertrag. `Beds24OfferAdapter` verwendet jetzt zusätzlich `Beds24ResponsiveQuote` für das tatsächlich gelieferte `formlook`/`book3` und die gemeinsame serverseitige `formbook`-Auswahl. Das ist ein begrenzter zweiter Vertrag im bestehenden Provider, kein zweiter Rechercheablauf und keine neue KI-Integration. Breitere responsive/AJAX-/Browser-/Private-Label-Varianten bleiben E.
2. **Quellenzuordnung durch tatsächliche Links ergänzt.** Ein OSM-Einstieg direkt bei Beds24 kann nur einen Unterkunftsnamen zeigen. Bis zu zwei dort tatsächlich verlinkte Betreiber-Start-/Kontaktseiten können den zusätzlichen Adress-/Telefonnachweis liefern. Bei normalen Websites kann eine tatsächlich verlinkte Kontakt-/Impressumsseite fehlende Identitätsmerkmale ergänzen. Eine spezifische Markenbezeichnung mit geänderter generischer Unterkunftsbezeichnung bleibt an unabhängige Orts-/Adress-/Telefonmerkmale gebunden. Keine Hotel-Ausnahme und keine Zuordnung allein durch ähnliche Namen.
3. **Öffentliches Suchformular vor Beds24 unterstützt.** Enger beobachteter WordPress-Vertrag `form.acantic-beds24-search-form`, GET, ohne fremde Aktion und ausschließlich `checkin`, `checkout`, `numadult`, `numchild`. Die Kandidatensuche verwendet die größte gewünschte Einzelzimmerbelegung; erst die nachfolgende Beds24-Auswahl muss die komplette tatsächliche Gruppe bestätigen. Die im Ergebnis wirklich veröffentlichte Objekt-/Zimmerkennung bleibt erhalten. Keine allgemeinen Formulare, Konto-/Reservierungs-/Gästedaten oder geratenen IDs.
4. **Linkerkennung verbessert.** Beobachtete Buchungs-/Verfügbarkeitsseiten auf Deutsch, Französisch, Polnisch und einigen gängigen weiteren Bezeichnungen, verzögerte Einbettungen und explizite Widget-URLs; Buchungsunterseiten vor allgemeinen Zimmerbeschreibungen. Alte HTTP-Hinweise werden ausschließlich am selben Host über HTTPS versucht. Kein unverschlüsselter Rückfall oder erratener Ersatzhost. Nicht unterstützte Systeme bleiben offen.
5. **Funktionierender kalter Verzeichniszugang.** Die alten Private.coffee-Timeouts sind nicht zu Leerständen umgedeutet. Der nach Betreiberbeschreibung kostenlose, schlüssellose [Europa-Overpass-Dienst](https://ovp.dresel.systems/) lieferte in einer begrenzten Gegenprobe 50 Unterkünfte in 2,199 s bei zwei HTTP-Transaktionen. Er ersetzt für die kleine Online-Ergänzung den ausgefallenen Zugang als **einzelner festgelegter Verzeichnisdienst**. Keine automatische Serverrotation. Lokaler OSM-Bestand und bestehende Wikivoyage-Daten bleiben vorrangig. Kalte Abfragen bleiben maximal zwei pro Suche, höchstens 500 Quellelemente, 2 MB, Quellen-Timeout zehn Sekunden, Transportlimits und siebentägiger Cache. Reichweite: Europa-Extrakt des Betreibers; keine Vollständigkeits- oder Verfügbarkeitsgarantie.

Primärgrundlagen: [Beds24-Gastparameter und vorgewählte Zimmer](https://wiki.beds24.com/index.php/Category:Developers), [responsive Buchungsseite](https://wiki.beds24.com/index.php/Responsive_Booking_Page), Betreiberseite des neuen Verzeichnisdienstes. Die Beds24-Verwaltungs-API mit Betreiberzugängen wird weiterhin nicht als kostenloser allgemeiner Hotelmarkt behandelt.

### 9.2 Nachprüfbarer Preisvertrag

- Objektkennung aus tatsächlich gefundenen URLs; erneuter Namens-/Objektbezug auf der Buchungsseite und der Auswahlquote. Verzeichnis-/Website-Zuordnung muss vorher belegt sein. Keine Modellkennungen.
- Übernommene An-/Abreise und Nächte unabhängig aus Quellfeldern; responsive Anfangsdaten zusätzlich aus begrenzten veröffentlichten Datumswerten. Kein Ausführen von Seitenskripten.
- Zimmer und zulässige Belegung aus gelieferten Steuerelementen. Höchstens 24 Kandidatentypen, zwei Auswahlversuche je Buchungsobjekt, höchstens zwei beobachtete Buchungsobjekte je Haus/Turn. Alternative Tarife desselben Zimmertyps erzeugen keinen zusätzlichen Bestand. Unterschiedliche Belegungen innerhalb desselben Typs bleiben vorerst eingeschränkt.
- Veröffentlichtes Kalenderdatum dient nur zum Verwerfen ungeeigneter Kandidaten, **nicht** als Preis-/Gruppenverfügbarkeitsnachweis. Fehlende Daten bedeuten offenen Buchungshorizont/Bestand. Mindestaufenthalte können eine scheinbar freie Kalenderfolge trotzdem unbuchbar machen.
- Nur die vollständig zurückgelieferte gemeinsame positive Auswahl zählt: `page=book`, Objekt, Zeitraum, Zimmermengen, Belegung, sichtbare Erwachsenen-Symbole, Zimmerzeilen, sichtbare Beträge und Gesamtsumme gegen unabhängige Quellfelder abgeglichen. Sold/Nullbeträge, Anfrageformulare, falsche Belegung, Summen-/Währungswidersprüche und fehlende Teile werden verworfen.
- Explizite obligatorische Zuschläge werden mit ihrer sichtbaren Zeile und der Gesamtsumme abgeglichen und als **bereits enthalten** angezeigt. Unbekannte örtliche Abgaben/weitere Pflichtkosten bleiben offen. Keine zweite Belastung enthaltener Gebühren und keine Vollständigkeitsannahme aus einer positiven Quote.
- Belege behalten ursprüngliche Abrufzeit, gewählte Zimmer und Beträge, tatsächliche sowie finale bereinigte Auswahl-URL und Antwort-SHA256. Keine Sitzungskennung/Gästedaten in den Belegen, keine vollständigen Webseitenarchive. URLs/Hash sind Herkunftsnachweise, keine spätere Preisgarantie.
- Das gelieferte POST-Gästeformular wird ausschließlich gelesen. Kein POST, kein `bookbook`, keine persönlichen Angaben, keine Reservierung/Buchung. Die lokale KI wird für diesen Preisweg nicht benötigt oder aufgerufen.

### 9.3 Echte neue Auswahlquoten im normalen Ablauf

Alle drei folgenden Endläufe verwenden `DiscoveryService.research` → den normalen Unterkunftsprovider → `OfferResearchService`/Qualitäts-/Kostenvertrag. Keine Hotel-URLs als Suchparameter, keine im Produkt hinterlegten Objekt-/Zimmerkennungen. Der Ortsparameter gehört nur zum opt-in Abnahmeskript. Daten sind echte Abrufbefunde vom 10.11.2026; nach zehn Minuten gelten sie im Produkt als veraltet.

| Neuer Verzeichnisfund | Anfrage | Tatsächlich zurückgelieferte Auswahl | Quellenbetrag | Einordnung |
|---|---|---|---:|---|
| Appartementhaus Gutenberg, Binz, OSM node 3518713754 | 10.–14.05.2027, 2 Erwachsene, 1 Einheit | 1-Raum-Appartement, veröffentlichter Tarif 2; 420 EUR plus 105 EUR Servicegebühr | **525,00 EUR** | Teilangebot, u. a. weitere/örtliche Abgaben und Schlafzimmervertrag offen |
| Domaine du Grenier, Yffiniac, OSM node 7837766717 | 12.–15.04.2027, 2 Erwachsene, 1 Einheit | FOUGERE, Gîte für zwei Personen; 342 EUR plus 11,22 EUR veröffentlichte Taxe de séjour | **353,22 EUR** | Teilangebot; vollständige Pflichtkostenerklärung nicht nachgewiesen |
| H41-Inn, Gundelfingen, Verzeichnisbezeichnung „H41-Inn Hostel“ | 13.–17.11.2026, 3 Erwachsene, 2 Zimmer | 1 Einzelzimmer Economy, 343 EUR; 1 Doppelzimmer Economy, 411 EUR; gemeinsame bestätigte Auswahl | **754,00 EUR** | Teilangebot; weitere Pflichtkosten bleiben offen |

Quellenketten: [Gutenberg-Verzeichnis](https://www.openstreetmap.org/node/3518713754) → beobachtete Beds24-Seite → [verlinkte Betreiberseite](https://binzurlaub.com/) mit passender Telefonnummer; [Grenier-Verzeichnis](https://www.openstreetmap.org/node/7837766717) → [offizielle Website](https://www.domainedugrenier.fr/) → tatsächlich verlinkte Verfügbarkeitsseite und deren reale Buchungsergebnisse; kalte räumliche OSM-Abfrage Gundelfingen → [offizielle H41-Website](https://www.h41-inn.de/) mit Namens-/Telefonzuordnung → beobachteter Beds24-Gasteinstieg. Exakte Quoten-URLs, Objekt-/Zimmerkennungen und Abrufzeiten stehen im vorhandenen [JSON-Prüfprotokoll](UNTERKUNFTSSUCHE_AB_PRUEFUNG_2026-11-10.json), Abschnitt `stage_b_follow_up`.

**Getrennte Tarifstände:** Der erste Gutenberg-Durchlauf verwendete den Standardpreis (Tarif 1), 440 + 105 = 545 EUR. Der finale Durchlauf verwendet den ebenfalls tatsächlich veröffentlichten Sparpreis (Tarif 2), 420 + 105 = 525 EUR; die Auswahl-URL enthält `br2-130446`. Die unterschiedlichen Tarifbedingungen werden nicht als gleichwertig normalisiert. Das ist **kein belegter Preisrückgang desselben Tarifs** und keine Anpassung eines erwarteten Sachwertes. Beide echten Abrufstände bleiben im JSON erhalten. Storno-/Zahlungsbedingungen bleiben im Produkt ausdrücklich nicht unabhängig normalisiert.

**Gehaltene zusätzliche Fälle:** Hotel Classic und Friz Ferienapartments wurden im abschließenden Gundelfinger Lauf ohne auf diese Häuser zugeschnittene Codeänderung verarbeitet. Classic: offizielle Website zugeordnet, im begrenzten Umfang keine abgenommene Buchungsquelle. Friz: Identität offen. Diese zuvor nicht zur Preisparser-Entwicklung verwendeten Häuser sind unabhängige **Statusfälle**; es wird kein vierter erfolgreicher Preis-Hold-out behauptet. Die drei obigen Häuser haben voneinander unabhängige echte Preise. Die H41-Quellennamensabweichung wurde während der Identitätsprüfung untersucht und wird deshalb nicht als völlig ungesehener Quellenkettenfall ausgegeben.

### 9.4 Gemessene Reichweite, Budgets und Fortsetzung

| Abschließender Ziel-Lauf | Eindeutige Funde | Zugeordnete Websites | Erkannte Systeme | Angebotsversuche / tatsächliche Auswahlantworten | Angenommene vollständige / Teilangebote | HTTP Preisphase / vorherige Suche | Preisphase |
|---|---:|---:|---|---:|---:|---:|---:|
| Binz | 201 | 4 | 1 Beds24 responsive, 1 OnePageBooking-Link | 1 / 1 | 0 / 1 | 39 / 0 | 59,069 s |
| Yffiniac | 16 | 3 | 1 Beds24 responsive | 1 / 1 | 0 / 1 | 15 / 0 | 25,604 s |
| Gundelfingen | 3 | 2 | 1 Beds24 responsive | 1 / 1 | 0 / 1 | 13 / 2 | 21,825 s |

Das sind **220 Funde, neun zugeordnete Websites, drei tatsächliche Auswahlantworten und drei Teilangebote** in den finalen drei Kampagnen; drei vollständige Reisebudgets werden daraus ausdrücklich nicht. Der Reichweitenverlust vor der Website-/Buchungszuordnung bleibt erheblich.

Alle begrenzten Folge-Kampagnen zusammen enthalten **619 unterschiedliche Verzeichnis-IDs**; wiederholte Termine/Entwicklungsstände werden nicht als zusätzliche Häuser gezählt. Das ist keine europaweite Preisabdeckung. Weitere echte Ziel-/Fehlversuchsläufe sind im bestehenden JSON erhalten, insbesondere Wałbrzych, Fulda, Oberstaufen, Hardheim, Langenburg, Hannoversch Münden, Zadar, Frankfurt (Oder), Freden und Wiefelstede. Alte Einzelmetriken dokumentieren ihren jeweiligen Arbeitsstand und werden nicht als aktuelle Endcode-Abnahme umetikettiert.

**Begründete Budgetanpassung:** Das Haus-Unterbudget steigt von acht auf **zwölf** Netztransaktionen; gemeinsame 40 HTTP/600 s manuell bzw. 32 HTTP im automatischen Suchrest bleiben erhalten, ebenso 90 s je Haus. Der erfolgreiche Grenier-Weg benötigt zehn HTTP einschließlich Robots-/WWW-Weiterleitungen, öffentlichem Formular und Auswahlquote. Acht reichten dafür nicht. Ein isolierter Diagnoseversuch benötigte 13; er zählt nicht als reguläre Abnahme. Das Beibehalten des realen Zimmerhinweises reduzierte den produktiven erfolgreichen Weg auf zehn. Es gibt kein zusätzliches volles Budget pro Haus.

Maximal zwei beobachtete Such-/Buchungsunterseiten, bei fehlender Identität eine beobachtete Kontaktseite, bei direktem Backend-Einstieg höchstens zwei Betreiberlinks; öffentliche Formularabfragen liegen ebenfalls innerhalb des Haus-/Gesamtbudgets. Kein flächiges Crawling, keine Abrufziele aus Modellwissen.

**Echte Fortsetzung:** Binz mit weiteren 20 HTTP/180 s bearbeitet **25 zuvor unangetastete Häuser**, keines mit vorherigem Versuch erneut. Budgetreste 164 → 140; zusätzliche definitive/offene Zustände sind einzeln erhalten. Der vorhandene Gutenberg-Beleg behält seinen ursprünglichen Abrufzeitpunkt; keine nur vorgetäuschte Preisaktualisierung. Die Summe aller Zustände bleibt 201. Die alten, unabhängigen Fortsetzungsmessungen aus Abschnitt 8 bleiben erhalten.

### 9.5 Erhaltene Fehlversuche und Zugangsgrenzen

- Private.coffee: alte GET-/POST-Timeouts bleiben belegt. Ein begrenzter anderer Overpass-Zugang wurde durch Robots gesperrt; keine Interpreterabfrage dahinter. Der OSM-Editing-API-Gegenversuch endete an der nicht freigegebenen Robots-Weiterleitung; die kanonischen Regeln sperren `/api/`, daher kein Datenabruf. Keine Umgehung, keine automatische Wechselkette. Der neue Europa-Dienst ist ein separat dokumentierter, tatsächlich funktionierender Verzeichnisweg.
- Hardheim: beobachteter WWW-Einstieg mit TLS-Zertifikatsfehler (`curl 60`), kein Abschalten der Prüfung oder geratener Alternativhost. Langenburg: veraltete Hinweise/HTTPS-Downgrades und unklare Identität. Fulda: untersuchte offizielle Seite lädt inzwischen Viato, während ein Suchindex noch eine Beds24-Seite zeigt; kein falscher aktueller Beds24-Nachweis.
- H41: Mai 2027 lieferte keine auswertbare Kalenderabdeckung; 23.–27.11.2026 keine vollständige Kandidatenfolge. Diese Anfragen bleiben erfolglos/offen. Der gesonderte veröffentlichte November-Zeitraum wurde als neue Anfrage geprüft; die vorherigen Antworten wurden nicht umgeschrieben.
- Haser: zunächst Null-/Sold-Auswahlen; ein tatsächlicher Einzelpreisabruf nannte vier Nächte Mindestaufenthalt. 25.–29.12.2026 ergab danach eine parsergeprüfte Zwei-Zimmer-Auswahl über 1.142,40 EUR. **Kein integrierter Verzeichnisfund dieses Hauses, deshalb nicht Teil der B-Neue-Häuser-Abnahme.** Laa, Heidelberg und Palatino zählen ebenfalls nicht als neue Häuser.
- Website-/Kontaktmerkmale, publizierte Kalender und Schema-Gültigkeit ersetzen keine vollständige positive Auswahl. Fehlende freie Daten/Adapter bleiben konkrete Lücken. Keine allgemeine Websuche, keine Kontoanlage, Zahlungsdaten, kostenpflichtigen APIs, Buchung oder Sperrumgehung.

### 9.6 GUI, Speicherung und Tests

- Derselbe normale GUI-Preisbutton liefert mit der echten H41-Quelle die gemeinsame Auswahl. Gemessen **22,909 s, 13 HTTP, 975 periodische Test-Callbacks, maximal 0,04068 s Callback-Abstand**. Der vorher ausdrücklich gespeicherte temporäre Snapshot blieb unverändert. Alle drei tatsächlichen Funde und Quellen sind in der Prüfliste erreichbar.
- Gesonderter automatisierter GUI-Durchlauf mit den **201 echten Binzer Funden**: Fensteraufbau und erste Aktualisierung **0,143 s**, alle 201 Zeilen vorhanden, letzte Zeile samt Detail erreichbar. Das ist eine programmgesteuerte Tk-Prüfung, keine manuelle Layoutfreigabe.
- **411 Tests bestanden, 19,992 s**: bisherige 393 plus 17 gezielte responsive/HTTP-/Quellen-/Grenztests und ein zusätzlicher Desktoptest mit responsiver Mehrzimmerquote, enthaltenem Zuschlag und ausdrücklichem Speichern. Der gesamte relevante Bestand blieb erhalten. `compileall` und `git diff --check` bestanden.
- Neue lokale HTTP-Fixtures prüfen normale Website → öffentliche Verfügbarkeit → dynamische Objekt-/Zimmerauswahl → Quotenprüfung → Kosten → expliziter Snapshot. Weitere Fälle: falsche Identität/Zeiträume/Belegung/Währung/Summe, fehlende Symbole, Sold/Nullpreis, Pflichtzuschlag, Nachtpreisverwechslung, Anfrage statt Auswahl, beobachtete Felder/URLs, fremde Anweisungen, begrenzter kalter Verzeichnisabruf/Cache/Timeout, Abbruch ohne zweiten Objektversuch. Bestehende DNS-/Peer-/TLS-/Robots-/Redirect-/Größen-/Generations-/Altformatregressionen laufen mit.
- Native manuelle Sichtprüfung erneut versucht: laufende Python-App erkannt, `cua.getApp(org.python.python)` → `cgWindowNotFound -10005`, zweiter Zugang über „Python“ → `timeoutReached -10005`. Damit konnte keine vollständige native Klick-/Layoutprüfung beobachtet werden. Sie bleibt **technisch blockiert**, nicht bestanden. Keine anderen Programme oder echte gespeicherte Reisen dafür verändert.

### 9.7 Abnahmematrix und nächste Etappen

| Kriterium | Stand |
|---|---|
| Allgemeine Unterkunftsfindung für neue Orte ohne Hotel-Codeeinträge | Erfüllt; vorhandener räumlicher Bestand plus funktionierende begrenzte kalte Europa-Abfrage |
| Mindestens drei neue Häuser in mindestens zwei Orten verarbeitet | Erfüllt; drei erfolgreiche Preisfälle in drei Orten, zusätzliche offene Fälle |
| Zwei unabhängige neue datierte Auswahlquoten | Erfüllt; drei Teilquoten mit vollständiger geprüfter jeweiliger Gruppenauswahl |
| Neue echte Mehrzimmerauswahl, verschiedene Termine/Belegungen | Erfüllt; H41 1+2 Erwachsene, zusätzlich zwei Einheiten-/Terminvarianten an anderen Häusern |
| Nicht zur Preisadapterentwicklung verwendete Häuser ohne Sondercode verarbeitet | Erfüllt als zusätzliche Statusfälle; kein vierter erfolgreicher Preis-Hold-out behauptet |
| Normale GUI, Kostenlücken, Unterkunftswechsel, Abbruch/Spätantwort, Fortsetzen, ausdrückliches Speichern/Altformate | Automatisiert erfüllt; echter Preisbutton und reale Fundmenge zusätzlich gemessen |
| Vollständige native manuelle Sicht-/Klickabnahme | Technisch blockiert; exakte Fehler oben, weiterhin offen |
| Vollständige europaweite Preisabdeckung, Pflichtkostenvollständigkeit, Buchbarkeit | Nicht zugesagt und nicht erreicht |

**B-Preis-Gate bestanden; vollständige manuelle GUI-Abnahme bleibt offen.** C: umfassendere Kombinationen/Kinderalter/harte Merkmale/Gebühren und Stornobedingungen. D: dauerhafte Jobfortsetzung über Neustart, größere Suchabdeckung und Listenkomfort. E: weitere responsive-/AJAX-/Browser-/Private-Label-Verträge und zusätzliche Systeme; der oben begrenzt vorgezogene Vertrag ist erhalten. F: breitere unabhängige Live-/Gesamt-/Bedienabnahme einschließlich der hier blockierten Sichtprüfung. Keine dieser Folgeetappen gilt pauschal als erledigt.

Reproduktion: `scripts/verify_general_lodging.py --live --target ... --start ... --end ... --adults ... --rooms ... --radius ... --budget 40 --seconds 300 --output ...`; gleichnamige Orte mit `--target-id` über die reale Siedlungs-ID unterscheiden. Fortsetzung über `--resume` mit eigener Ausgabedatei. Beispiele/öffentliche Identitäten sind Prüfdaten, keine produktive Orts-/Hotelbegrenzung. Tests: `.venv/bin/python -m unittest discover -q`. Kein Commit/Push.

## 10. Fortführung ab 12.11.2026 – B-Abnahme, Anfragebezug und Etappe C

Auftrag: vorhandenen Zwischenstand prüfen und weiterbauen, ohne Platzhalter und ohne produktive Orts-/Hotellisten. Bestehende uncommittete Arbeiten und gespeicherte Reisen bleiben erhalten. Die Nutzerbestätigung umfasst die oben empfohlene Reihenfolge B → C → gezielte Erweiterung der Systemreichweite aus E. Keine zusätzliche kostenpflichtige Abhängigkeit, keine Kontoanlage, Buchung, Commit oder Push.

Arbeitsentscheidungen vor Umsetzung:

- Explizite Zimmeraufteilung und Kinderalter werden Teil desselben Anfrage-/Beleg-/Speichervertrags. Bestehende Erwachsenenreisen ohne diese Angaben behalten ihre bisherige Bedeutung. Altersangaben sind Alter am Reisebeginn, keine Geburtsdaten.
- Auswahlvarianten bleiben aus tatsächlich gelieferten Bestands-/Tariffeldern abgeleitet. Alternative Tarife desselben physischen Zimmertyps zählen nicht als weitere freie Zimmer. Uneinheitliche Belegung innerhalb eines Typs benötigt pro Einheit gelieferte Belegungsfelder und eine bestätigende gemeinsame Auswahl.
- Ein Kinderzähler allein bestätigt keine Alters-/Tarifregeln. Die aktuelle offizielle Beds24-Dokumentation beschreibt individuell konfigurierte Altersgruppen und zusätzliche Abschläge/Steuern. Fehlt der unabhängig prüfbare Altersvertrag einer Quelle, bleibt gerade dieser Quellenweg offen; keine Ersatzsuche ohne Kinder.
- Zimmer-/Tarifbezeichnung, Originalbedingungen und bekannte Zuschläge sollen nachvollziehbar an der konkreten Auswahl bleiben. Freie Gebühren-/Stornoprosa wird nicht pauschal als vollständig verstanden. Eigenes Bad wird als auswählbares Pflichtmerkmal ergänzt; unbekannte oder widersprüchliche Merkmale bleiben ungeprüft.
- Gemeinsame HTTP-/Zeit-/Abbruchgrenzen, der vorhandene lokale Modellclient und die Arbeitskopielogik bleiben maßgeblich. Systemweite technische Verträge sind zulässig; Hotel-/Ortskennungen im Produkt nicht.

Stand zu Beginn: vorhandener Code und Bericht mit 411 Tests geprüft. Der erste neue Teststart in der eingeschränkten Umgebung brach technisch ab; ein vollständiger erneuter Lauf mit Zugriff auf lokale Testports und den macOS-Fensterserver ist gestartet. Keine neue erfolgreiche Abnahme daraus vorweggenommen. Die offene native Sichtprüfung wird erneut versucht; ein technischer Fehler wird nicht als bestandene Prüfung ausgegeben. Fortschritt und Ergebnisse werden in diesem Abschnitt ergänzt.

### 10.1 Implementierung und Quellenvertrag

- Das bestehende Reiseformular enthält Kinderalter am Reisebeginn und einen tatsächlichen Zimmereditor. Alle Personen müssen genau einmal zugeordnet sein; eine nachträglich geänderte Gruppe kann eine alte explizite Aufteilung nicht still weiterverwenden. Automatische Verteilung ist weiterhin möglich. Gemeinsamer `RoomParty`-/`OfferQuery`-Vertrag für Formular, Quelle, Prüfschicht und ausdrücklichen Snapshot. Alte Erwachsenenreisen bleiben ladbar; deren Angebotsparameter bleiben ohne neue leere Altersfelder vergleichbar.
- Der responsive Beds24-Adapter nutzt bis zu 24 tatsächlich gelieferte Zimmer-/Tarifvarianten mit den jeweiligen `naa`-/`ncc`-Feldern pro Einheit. Begrenzte Suche: 2.048 Suchknoten, höchstens zwei gemeinsame Quotenversuche pro Objekt und Runde; bestehende Hausgrenze 12 HTTP/90 s und gemeinsame Gesamtgrenzen bleiben maßgeblich. Unterschiedliche Belegungen desselben Typs sind möglich, wenn die konkreten Felder dies erlauben. Alternative Tarife desselben physischen Typs erzeugen keinen zusätzlichen Bestand. Kalender/Dropdowns bleiben Kandidatenhinweise; erst die vollständige gemeinsame Serverauswahl bestätigt die angefragte Belegung.
- Kinderpreise werden ausschließlich bei eindeutig veröffentlichter, unterstützter Altersgruppe unmittelbar am Kinder-Auswahlfeld ausgewertet. Enger deutscher/englischer Labelvertrag: unter/bis bzw. expliziter Altersbereich. Jede tatsächliche Altersangabe muss passen. Fehlende/mehrdeutige Labels, unbekannte Altersgruppen und klassische Quellen ohne abgenommenen Altersvertrag bleiben ausdrücklich offen. Kein Erwachsenenersatzpreis. Die Prüfschicht kontrolliert zusätzlich die Altersbelege und die vollständige Zimmeraufteilung, statt ein Parameterecho zu akzeptieren. Andere bisherige Preisprovider ohne Altersvertrag erhalten keine Erwachsenen-Anfrage für eine Familie.
- Ausgewählte Zimmer, Quellentarife, begrenzte Originalbedingungen und bekannte Pflichtzuschläge bleiben am jeweiligen Angebot und erscheinen in der vorhandenen Prüfliste. Fehlende Tariftexte bleiben fehlend. Eigener-Bad-/Frühstück-/Stornobefunde stammen aus der konkreten Auswahl; Hotelangaben werden dafür nicht ungeprüft auf jeden Tarif übertragen. Positive harte Aussagen verlangen einen engen vollständigen Textvertrag; zusätzliche Einschränkungen führen zu unbekannt. Zeitlich begrenzte Stornoklauseln werden nicht als Öffnung/Buchbarkeit oder allgemeine Rechtsauskunft dargestellt. Weitere Pflichtkostenvollständigkeit bleibt ungeklärt.
- Unbekannte Pflichtmerkmale dürfen vor der bestehenden begrenzten Preisprüfung nicht bereits jeden Kandidaten aussortieren. Dieselbe Preisphase erhält deshalb bei solchen Kandidaten früh Gelegenheit zur Klärung, innerhalb derselben insgesamt 32 HTTP und Zielanzahl. Ungeklärte oder neu tarifbezogen unbekannte Anforderungen bleiben `offen`; keine automatische Filterlockerung.
- Gruppenangaben, Kinderalter und rechnerische Pro-Person-Aufteilung sind auch im bestehenden PDF berücksichtigt. Keine erfundene Kindertarifmultiplikation. Die normale Arbeitskopie-/Speicherlogik, sichere HTTP-Verarbeitung und vorhandene lokale KI bleiben erhalten; kein zweiter Modellclient, Modellstart oder Modell-Download.

Aktuelle Primärquellen: [Beds24-Entwicklerparameter](https://wiki.beds24.com/index.php/Category:Developers), [responsive Buchungsseite](https://wiki.beds24.com/index.php/Responsive_Booking_Page), [Kinderpreise und individuell konfigurierte Altersgruppen](https://wiki.beds24.com/index.php?title=Children_Prices), [Zusatzpositionen](https://wiki.beds24.com/index.php/Upsell_Items), [Buchungsfragen](https://wiki.beds24.com/index.php/Booking_Questions). Buchungsfragen sind keine Freigabe, private Gastformulare zur Preisbeschaffung abzusenden. Keine allgemeingültige Alters-/Gebührenregel aus der Installation abgeleitet.

### 10.2 Echte Abrufe am 12.11.2026

Reproduktion über das erweiterte vorhandene `scripts/verify_general_lodging.py`, keine Hotelvorgabe: `--target Gundelfingen --target-id geonames:2913713 --start 2026-11-13 --end 2026-11-17 --radius 3`; fünf Erwachsene/drei Zimmer bzw. zwei Erwachsene/ein Zimmer/`--children-ages 5`. Auswahl-IDs kamen aus tatsächlichen Quellen. Ein erster Lauf mit falscher expliziter Orts-ID wurde vor Netzabrufen wegen nicht eindeutiger Ortsauflösung beendet; anschließend tatsächliche Bestands-ID verwendet. Öffentliche Quoten und Statusnachweise: [JSON-Prüfprotokoll C](UNTERKUNFTSSUCHE_C_PRUEFUNG_2026-11-12.json).

| Stufe | Fünf Erwachsene, drei Zimmer | Zwei Erwachsene, Kind 5 Jahre |
|---|---:|---:|
| Eindeutige Verzeichnisfunde | 7 | 7 |
| Zugeordnete offizielle Websites | 3 | 3 |
| Erkannte unterstützte Systemverträge | 1 Beds24 responsive | 1 Beds24 responsive |
| Begonnene Angebotsprüfungen | 1 | 1 |
| Tatsächlich erhaltene gemeinsame Auswahlantworten | 1 | 0 |
| Angenommene Teilangebote | 1 | 0 |
| Vollständig geprüfte Angebote | 0 | 0 |
| Quellen ohne unterstützten Buchungslink | 2 | 2 |
| Robots-/Quellenzugang blockiert | 1 | 1 |
| Identität unklar | 1 | 0 |
| Nicht unterstützter Altersvertrag | 0 | 1 |
| Restbudget/Fortsetzung offen | 0 | 1 |
| Unterkunftsart ausgeschlossen | 2 | 2 |

**Tatsächliche 2+2+1-Gruppenauswahl:** H41-Inn Hostel, Quelle `https://beds24.com/booking.php?propid=66897`, Abruf 12.11.2026 11:53:52 UTC. Einzelzimmer Economy 343 EUR + Doppelzimmer Economy 411 EUR + Privatzimmer Studio 448 EUR = **1.202 EUR** für 13.–17.11.2026. Alle drei Zimmer mit konkreten sichtbaren Auswahlzeilen und Belegung bestätigt. Keine Ableitung aus einem Einzelzimmerpreis. **Teilquote**, weitere verpflichtende Gebühren nicht vollständig belegt; kein Reservierungs-/Bestpreisversprechen. Die frühere 754-EUR-Quote für drei Erwachsene/zwei Zimmer bleibt ein anderer Anfragefall.

Erwachsenenlauf: 18 HTTP in der Preisphase / 27,686 s, zusätzlich zwei Verzeichnisabfragen, Gesamtlimit 24. Familienlauf: 16 HTTP / 21,730 s in der Preisphase plus zwei Verzeichnisabfragen, Gesamtlimit 18. H41 veröffentlichte für diesen Vertrag keine unabhängig prüfbare Kinder-Altersgruppe; daher keine Auswahlanfrage ohne Kind und kein Familienpreis. Friz blieb im Familienlauf wegen Restbudget offen; beim Erwachsenenlauf Identität ungeklärt. B&B-Zugang blieb wegen nicht abrufbarer Robots-Regeln gesperrt. Kein Timeout/Sperrfall wurde als ausgebucht ausgegeben. Diese Messung rechtfertigt keine pauschale Budgeterhöhung; bestehende Fortsetzung bleibt erhalten.

### 10.3 GUI, Regression und ehrliche Abnahme

- Gesamter Ausgangsbestand tatsächlich erneut geprüft: 411 Tests / 20,458 s. Erster eingeschränkter Lauf technisch abgebrochen; erneuter Lauf mit lokalen Testports und Fensterserver erfolgreich.
- Ergänzte Unit- und echte Tk-Tests prüfen exakte Personen-/Altersmengen, Formular/Editor/Speichern/Wiederladen/Altformat, gleiche Zimmertypen mit verschiedenen Belegungen, fehlende dritte Einheit, gemeinsame Auswahl statt Multiplikation, alternative Tarife, Quellen-Alterslabel und Grenze, sichtbare Kinderbelegung, gefälschte Altersbelege, keine Anfrage an Erwachsenenprovider, Negationen/Einschränkungen und zeitliche Stornogrenze sowie PDF-Gruppe und Kostenteiler. Vorhandene HTTP-/DNS-/Redirect-/Cache-/Abbruch-/Spätantwort-/KI-Regressionen bleiben Bestandteil der Gesamtsuite.
- **Automatisierter echter GUI-Preisbutton**, mit isolierter temporärer Datenbank und tatsächlichem Verzeichnisresultat: 34,797 s, 3.101 Tk-Callbacks, maximaler Abstand 0,0337 s. Die 1.202-EUR-Quote erschien im normalen Ergebnis. Vorher gespeicherter temporärer Snapshot unverändert; ausdrückliches Speichern erhielt alle neuen Belege. Messung/Quelle im JSON-Protokoll; keine manuelle Sichtprüfung behauptet.
- Native visuelle Gegenprobe erneut technisch gescheitert: `cua.getApp(org.python.python)` → `ScreenCaptureKit.SCStreamErrorDomain -3811`, Audio-/Video-Aufnahmestart fehlgeschlagen. Die Anfrage blockierte ungewöhnlich lange. Keine Aufnahme-/Sicherheitseinstellungen geändert; die manuelle B-/F-Sichtabnahme bleibt offen.
- **426 Tests / 20,136 s bestanden** (411 Ausgangstests und 15 neue Tests). `compileall` und `git diff --check` ebenfalls bestanden. Reproduktion: `.venv/bin/python -m unittest discover`; die Desktop-/HTTP-Fixtures benötigen den lokalen Fensterserver bzw. Testports.

**Abnahme C:** Anfrage-/GUI-/Speicherpfad, dynamische Kombinationsauswahl und reale 2+2+1-Teilquote umgesetzt. Unterschiedliche Belegungen innerhalb desselben Typs und ein passender Familien-Altersvertrag sind mit reproduzierbaren Fixtures geprüft; ein erfolgreicher echter Familienpreis mit eindeutig veröffentlichtem Altersvertrag ist **nicht nachgewiesen**. Keine allgemeine Gebühren-/Stornoprosa-Interpretation, keine gesicherte Pflichtkostenvollständigkeit. C wird deshalb nicht als uneingeschränkt vollständig abgenommen ausgegeben. B-Preis-Gate bleibt erfüllt, native Sichtprüfung offen. E enthält weiterhin nur die bereits integrierte begrenzte responsive Variante; keine weitere Systemfamilie hinzugefügt. D (dauerhafte Jobs/Neustartfortsetzung) und F (breitere unabhängige Gesamt-/Sichtabnahme) bleiben ausstehend. Allgemeine Architektur ohne produktive Orts-/Hotellisten bedeutet keine universelle Preisabdeckung beliebiger Websites.

## 11. Fortführung C–F: Familienbelege, dauerhafte Arbeitsstände und zusätzliche Variante (17.11.2026)

Dieser Abschnitt schreibt den **historischen Stand aus Abschnitt 10** fort. Die dort noch fehlende echte Familienquote und die Neustartfortsetzung wurden inzwischen nachgewiesen. Die folgende Abnahme trennt tatsächliche Internetabrufe vom 12.–15.11., automatisierte Desktopprüfungen, Fixtures und die weiterhin gescheiterte native Sichtprüfung. Spätere Dokumentpflege macht die damaligen Preise nicht frisch.

Nachweise: [Prüfprotokoll C–F](UNTERKUNFTSSUCHE_CDEF_PRUEFUNG_2026-11-17.json), [öffentliche reproduzierbare Prüffälle](UNTERKUNFTSSUCHE_LIVEFAELLE_2026-11-15.json). Die Prüffälle sind Daten für die Abnahme, keine produktive Hotel-/Ortsliste. Vorhandene uncommittete Änderungen blieben erhalten. Keine Buchung, Kontoanlage, Zahlung, kostenpflichtige Abhängigkeit, Commit oder Push.

### 11.1 C – Familien-/Gruppenpreise und Merkmale

Der vorhandene Kinder-Altersvertrag wurde um die tatsächlich beobachtete vollständige englische Auswahlbeschriftung mit `ages … to …` ergänzt. Bei „Children ages 4 to 12“ passen 4 und 12 einschließlich; 3 und 13 passen nicht. Die Originalbeschriftung, der genaue Quellabruf mit URL/Zeitpunkt/SHA-256 und die bestätigte Zimmerbelegung werden gespeichert und angezeigt. Es gibt keine stille Umdeutung eines Kindes zum Erwachsenen und keine frei interpretierte Altersprosa. Die sichtbaren Personen- und Zimmerzeilen der abschließenden gemeinsamen Auswahl müssen weiterhin vollständig passen.

**Neue echte Familienquote:** Casas da Villa / Casa Sobreiro, Monsanto, **12.–15.04.2027, zwei Erwachsene und ein Kind mit sechs Jahren, eine Einheit, 480 EUR**. Die konkrete Quelle nennt die Altersgruppe 4–12; die tatsächliche serverseitige Auswahl bestätigt zwei Erwachsene und ein Kind. Nachgewiesen zuerst über den offiziellen Gemeindeeintrag → Betreiberwebsite → beobachteten Beds24-Objektlink, anschließend auch über die zusätzliche Betreiberübersichtsvariante. Die erfolgreiche GUI-Quote stammt vom **13.11.2026, 18:11:05 UTC**; der eigenständige CLI-Replay vom **15.11.2026, 07:19:55 UTC** bestätigte erneut 480 EUR. Das sind Teilangebote zum jeweiligen Abrufzeitpunkt, keine heutigen Preis-/Reservierungszusagen.

**Wesentliche Reichweitengrenze:** Die normale automatische Verzeichnissuche für Monsanto fand Casa Pires Mateus, aber nicht Casas da Villa. Die Familienunterkunft wurde für diese Abnahme aus dem tatsächlich abgerufenen [offiziellen Gemeindeverzeichnis](https://www.idanha.pt/idanhapt/onde-dormir/casas-da-villa/) ermittelt; die [offizielle Tourismusquelle](https://www.visitportugal.com/pt-pt/content/casas-da-villa-adufe-e-sobreiro) stützt die Straßenidentität. Die [Betreiberwebsite](https://casasdavilla.com/home/) veröffentlicht die konkrete Buchungsstrecke. **Keine allgemeine automatische Gemeindeverzeichnis-Suche implementiert oder behauptet.** Der Replay startet mit dieser dokumentierten Identität und zählt sie nicht als neuen automatischen Verzeichnisfund. Neue OSM-/Website-Unterkünfte mit demselben unterstützten Quellenvertrag können ohne Codeänderung verarbeitet werden.

**Erneute echte Gruppenprüfung:** normale Verzeichnisfindung in Gundelfingen, Abruf **14.11.2026**; H41-Inn bestätigte **16.–20.11.2026, fünf Erwachsene, drei gemeinsam ausgewählte Einheiten (1+2+2)**: 320 + 380 + 420 = **1.120 EUR**. Das ist ein anderer Termin als die früheren 1.202-/754-EUR-Fälle, kein behaupteter Preisverlauf. Unterschiedliche Belegungen desselben physischen Typs, fehlende dritte Einheit und alternative Tarife sind zusätzlich reproduzierbar mit Fixtures geprüft; kein zweiter Livefall für genau diese Kombination innerhalb desselben Typs behauptet.

Zimmerbezogene affirmative Merkmalszeilen werden nur innerhalb der konkreten Zimmerkarte und mit dem gelieferten Bestätigungsmarker ausgewertet. Kontrollierte Bezeichnungen für Frühstück, eigenes Bad und Gemeinschaftsbad; keine Vererbung eines allgemeinen Hotel-Footers. Widersprüche zu konkreten Tarifbedingungen bleiben unbekannt. Bei mehr als 80 Merkmalszeilen unterbleibt die betreffende Übernahme statt einer unbemerkten Teilinterpretation. Die echte Familienquelle liefert so einen begrenzten Frühstückshinweis. Unbekannte Bad-/Stornobedingungen bleiben unbekannt. Positive freie Stornobedingungen benötigen weiterhin den engen vollständigen und zeitlich passenden Vertrag; beliebige Klauselprosa wird nicht zuverlässig normalisiert.

Die bisherige Prüfung von sichtbaren Einzelzeilen, Mengen, Währung, Pflichtzuschlägen und Gruppensumme bleibt erhalten. **Keine neue Behauptung vollständiger Pflichtgebühren**: auch die zwei neuen Preisfälle bleiben Teilangebote. Altersregel, konkrete Auswahl-URL, gewählter Quellentarif und begrenzte Originalbedingungen sind in der normalen Ergebnis-/Unterkunftsprüfliste sichtbar. Ein ortsgebundener Browser-Fallback wurde durch den tatsächlich ausgewählten Unterkunftslink ersetzt.

### 11.2 D – Dauerhafte Fortsetzung im normalen Ablauf

- `LodgingJobStore` speichert Arbeitsstände in einer **separaten** SQLite-Datei neben der Reise-Datenbank: standardmäßig `trips-research.sqlite3`. Weder HTTP-Cache noch ausdrücklich gespeicherte Reisen ersetzen diesen Arbeitsstand. Das bestehende Reiseformat `schema_version=1` und die `trips.sqlite3`-Speicherlogik bleiben erhalten.
- Die vorhandene Preisphase erzeugt einen Arbeitsstand, setzt nach vorhandenen Teilausgaben Checkpoints und hält den letzten Stand auch bei Abbruch/Schließen fest. Datenbankfehler werden sichtbar gemeldet; die Arbeitskopie und übrige Quellen bleiben nutzbar. Terminproben werden nicht unter einem falschen gemeinsamen Anfragebezug vermischt.
- Fingerabdruck bindet Datum, Ziel, Personen, konkrete Kinderalter/Zimmeraufteilung und Kriterien. Ein Token verwirft verspätete Checkpoints eines ersetzten Laufs. Änderungen von Datum oder Ziel entwerten alte Preise auch vor Ablauf des Zehn-Minuten-Frischefensters.
- Der neue Reiter **Recherchefortschritt** listet alle Arbeitsstände. **Arbeitsstand öffnen** führt keinen Internetabruf aus. **Öffnen und Unterkünfte fortsetzen** verwendet dieselbe vorhandene Preisaktion und ihre Grenzen. Aus einem Arbeitsstand wird erst mit **Reise speichern** ein gespeicherter Reise-Snapshot. Löschen eines Arbeitsstands verändert keine gespeicherte Reise.
- Die bisherige faire Reihenfolge nach Bearbeitungszahl bleibt über Neustarts erhalten. Frische erfolgreiche Quoten werden nicht erneut abgerufen; Fehlerwartezeiten und offene Budgetreste bleiben erhalten. Unveränderte terminale Quellenfälle werden bei Fortsetzung nicht ständig wiederholt. Eine ausdrücklich gestartete normale Aktualisierung kann solche Quellen erneut prüfen.
- Geänderte Auswahl bleibt beim Checkpoint erhalten. Die Übersicht liest kompakte Metadaten statt sämtlicher Quellenbelege aller Jobs; alte Arbeitsstandstabellen ohne diese Metadaten werden einmalig ergänzt. Alle gefundenen Häuser verbleiben in der vollständigen Prüfliste, auch außerhalb der acht Vorschläge.

### 11.3 E – Zusätzlicher technisch belegter Quellenvertrag

**Neu: `owner-property-list-v1 / responsive-selection-v1`.** Eine tatsächlich veröffentlichte Betreiberkennung kann zu einer Übersicht statt einem einzelnen Objekt führen. Der Adapter liest daraus tatsächliche Objektlinks, prüft höchstens zwei konkrete Objekte je Runde und ordnet das gewählte Objekt unabhängig durch Name plus weitere Identitätsmerkmale zu. Die Betreiber-Marke allein genügt nicht. Erst danach läuft der vorhandene datierte responsive Preis-/Alters-/Belegungsvertrag. Keine Objekt-ID-Enumeration, keine zusätzlichen Rechte und kein weiterer Modellclient. Betreiberübersicht, gewählter Objektlink und Herkunftsbelege bleiben erhalten; bestehende 12-HTTP-/90-s-Hausgrenzen und Gesamtbudgets gelten weiter.

Der neue Vertrag lieferte die oben belegte 480-EUR-Familienquote. Betreiberkennung stammt aus der tatsächlichen Websiteverlinkung; die Übersicht wurde über den dokumentierten Betreiberparameter aufgerufen. Lokale HTTP-Fixtures mit anderen synthetischen Kennungen prüfen Website → Betreiberübersicht → Einzelobjekt → gemeinsame Quote sowie direkte Betreiber-Einstiege und falsche gleichnamige Objekte. Ein zweites unabhängiges erfolgreiches Livehaus speziell für diese neue Variante ist noch nicht nachgewiesen; keine universelle Betreiberübersichtsabdeckung behauptet.

**Zusätzliche Familie untersucht, nicht vorgetäuscht:** OnePageBooking 6 wurde über die aktuelle [Adler-Betreiberseite](https://adlerehingen.de/hoteladlerehingen) und deren tatsächlichen Buchungslink untersucht. Das öffentliche HTML und ein tatsächlich eingebundenes JS-Bundle wurden begrenzt gelesen, nicht ausgeführt. Der darin referenzierte Property-Pfad auf `v6.onepagebooking.com` wird durch dessen **Robots-Regeln gesperrt**; die bestehende HTTP-Schicht verweigerte den Abruf. Keine Sperrumgehung, Authentifizierungs-/Zahlungsaufrufe oder Preisunterstützung dafür. Eine weitere Version-5-Seite lieferte nur eine JS-Anwendung; ein älterer Litz-Link lieferte „Client doesn't exist“, dessen Betreiberwebsite einen TLS-Fehler (`curl 60`). Das sind konkrete Zugangs-/Vertragsgrenzen, keine Aussage über leere Hotelbestände. [Herstellerangaben](https://hotelnetsolutions.de/damit-der-familienurlaub-nicht-schon-bei-der-buchung-zur-belastungsprobe-wird/) bestätigen zudem individuell konfigurierte Kinder-Altersgruppen; keine fremde Altersregel übernommen.

### 11.4 Getrennte Live-Abnahmematrix und Durchsatz

| Lauf | Automatische eindeutige Funde | Websites zugeordnet | Erkannte unterstützte Variante | Angebotsversuche / Auswahlantworten | Vollständig / teilweise | Bestätigt nicht verfügbar | Andere Zustände |
|---|---:|---:|---:|---:|---:|---:|---|
| Monsanto, normale Suche | 1 | 0 | 0 | 0 / 0 | 0 / 0 | 0 | 1 ohne auswertbare Buchungsquelle |
| Familienfall aus offizieller Gemeindequelle | Kein neuer automatischer Fund; 1 dokumentierte Identität | 1 | 1 | 1 / 1 | 0 / 1 | 0 | Pflichtkostenvollständigkeit offen |
| Betreiberübersichtsvariante / Replay | Dieselbe Familienunterkunft, kein zusätzliches Haus | 1 | 1 | 1 / 1 | 0 / 1 | 0 | Pflichtkostenvollständigkeit offen |
| Gundelfingen, normale Suche | 7 | 3 | 1 | 1 / 1 | 0 / 1 | 0 | 2 ohne Buchungsquelle, 1 Robots-/Quellenblock, 1 Identität unklar, 2 Unterkunftsart ausgeschlossen |

Erste direkte Familienprüfung: 7 HTTP einschließlich Gemeindequelle / 15,938 s Preisphase; ein gesonderter späterer Aktualisierungsversuch scheiterte nach vier HTTP mit `curl 28` und wird separat erhalten. Neue Betreiberauflösung: fünf HTTP / 21,555 s. Endgültiger öffentlicher Replay: fünf HTTP / 21,604 s. Gundelfingen: 18 HTTP in der Preisphase / 33,219 s plus zwei Verzeichnisabfragen, Gesamtbudget 24. Keine pauschale Budgeterhöhung daraus abgeleitet. Wiederholte Abrufe derselben Familienunterkunft zählen nicht als zusätzliche unabhängige Häuser.

### 11.5 F – GUI, Absturzdiagnose und Regression

**Automatisierte reale GUI-Prüfung:** Familienformular und Zimmereditor, normaler Preisbutton, neue Betreiberauflösung mit echter 480-EUR-Quote, Speichern, Schließen und Neustart. Erster Preisabruf **22,073 s**, 1.796 Tk-Callbacks, maximaler Abstand **0,1064 s**, fünf HTTP. Neuer Arbeitsstand nach Neustart geöffnet und fortgesetzt: **0,170 s, null HTTP**, ursprünglicher Quellenzeitpunkt unverändert. Vorheriger ausdrücklich gespeicherter temporärer Snapshot unverändert; neue Belege nur ausdrücklich als Reise gespeichert. Historische echte Binzer Fundliste: **201 Zeilen, letzte Zeile und Detail erreichbar, 0,013 s**; keine neue Binz-Internetrecherche behauptet.

Zusätzliche Desktoptests prüfen Abbruch/Schließen während einer noch laufenden Quelle, persistierten letzten vollständigen Schritt, fortsetzbaren abgebrochenen Schritt, Auswahländerung, neue Generation sowie normale servicegestützte Fortsetzung von 70 Häusern nach Neustart. In der ersten Runde höchstens 64 Häuser; zuvor unbearbeitete Häuser werden bei der Fortsetzung erreicht. Fixtures/HTTP-/Preis-/Fehler-/Altformat- und bisherige KI-Regressionen bleiben erhalten. Diese Prüfungen sind programmgesteuert, keine manuelle Sicht-/Klickfreigabe.

**SIGABRT:** Der tatsächliche Bericht `Python-2026-11-12-122349.ips` zeigt Python 3.13.18, Elternprozess `codex`, Abbruch in `_RegisterApplication` / Tk-AppKit-Initialisierung. Prozessstart und Zeitstempel des leeren eingeschränkten Testlogs stimmen auf dieselbe Sekunde überein; der anschließend mit Desktopzugriff ausgeführte Lauf bestand. Die aktuelle `gui/501`-Sitzung ist Aqua. Drei neue voneinander getrennte Projektstarts mit temporären Datenbanken bestanden, jeweils Returncode 0, Tk 9.1.0, **0,414 / 0,360 / 0,356 s**, ohne stderr. In dieser Sitzung kein entsprechender Projektabsturz reproduziert. Eine abschließende interne LaunchServices-Ursache ist damit nicht bewiesen; keine spekulative Produktkorrektur als Absturzbehebung ausgegeben.

**Native Sichtprüfung weiterhin offen:** laufende isolierte Projekt-App gestartet; `cua.getApp(org.python.python)` scheiterte erneut sofort mit `ScreenCaptureKit.SCStreamErrorDomain -3811` (Audio-/Video-Aufnahmestart fehlgeschlagen). Kein Zugriff auf eine native Aufnahme/Klickfolge. Keine Sicherheitseinstellungen geändert und keine vollständige manuelle Prüfung behauptet.

**444 Tests / 21,727 s bestanden**; `compileall` und `git diff --check` ebenfalls bestanden. Ein neu hinzugefügter Migrationstest hatte im vorletzten Lauf eine ungeschlossene SQLite-Verbindung; diese Testressource wurde ausdrücklich geschlossen und die Gesamtsuite erneut ausgeführt. Keine Sollpreise zum Verdecken von Quellenfehlern geändert. Die Preisrecherche blieb deterministisch; keine neue lokale Modell-Liveprüfung oder Cloud-Nutzung behauptet.

### 11.6 Abnahmestatus und Reproduktion

| Kriterium | Status |
|---|---|
| Echter Familienpreis mit konkretem Alter, Altersregel und gemeinsamer Auswahl | Erfüllt für den dokumentierten Quellenvertrag; Herkunft aus offizieller Gemeindequelle klar getrennt |
| Keine Erwachsenen-Ersatzanfrage; Grenzalter, alternative Tarife, gemischte Belegung, fehlende Einheit | Automatisiert erfüllt; zusätzliche echte neue 1+2+2-Gruppenquote |
| Vollständige Gebühren-/Stornointerpretation beliebiger Quellen | Nicht zugesagt; Teilangebote und unbekannte Merkmale bleiben sichtbar |
| D: dauerhafte Fortsetzung, faire Restbearbeitung, Auswahl, Abbruch, Altformate und ausdrückliche Reiseseparierung | Implementiert und automatisiert einschließlich realem GUI-/Neustartlauf geprüft |
| E: zusätzliche abgegrenzte technisch belegte Variante | Betreiberübersichtsvertrag implementiert und live geprüft; zweites unabhängiges Livehaus dafür offen |
| Zusätzliche OnePageBooking-Familie als Preisquelle | Offen wegen beobachteter Robots-/JS-/Vertragsgrenzen; keine Unterstützung vorgetäuscht |
| F: relevante Regression, normale automatisierte GUI und getrennte Liveprüfung | Erfüllt im dokumentierten Umfang |
| F/B: vollständige native manuelle Sicht-/Klickprüfung | Technisch blockiert durch Aufnahmefehler; offen |
| Allgemeine automatische Entdeckung der Familienunterkunft aus beliebigen Verzeichnissen | Nicht erreicht; konkrete Lücke der normalen Monsanto-Suche dokumentiert |

Reproduktion der normalen geografischen Suche mit zukünftigen Daten über das vorhandene Skript; `--target-id` trennt gleichnamige Orte. Für den dokumentierten öffentlichen Familien-/Betreibervertrag ohne neue Verzeichnisbehauptung:

```bash
.venv/bin/python scripts/verify_general_lodging.py --live \
  --case-file docs/UNTERKUNFTSSUCHE_LIVEFAELLE_2026-11-15.json \
  --case-key owner-overview --budget 16 --seconds 120 \
  --output tmp/replay-owner.json
```

`--case-key family-official` prüft den direkten Betreiberwebsite-Weg. Eingabedaten/Termine sind öffentliche Prüfbeispiele, keine Preisgarantie und keine produktive Einschränkung. Spätere Daten-/Zugangsänderungen können zu offenen Ergebnissen führen. Echte Reisen wurden für die Prüfungen nicht geöffnet oder verändert; nur temporäre Reise-Datenbanken und der vorhandene geografische Bestand im Lesezugriff verwendet.
