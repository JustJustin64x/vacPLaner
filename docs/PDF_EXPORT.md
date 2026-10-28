# Reiseführer-PDF und gezielte Anreicherung

## Aufbau

Der PDF-Export besitzt eine eigene Darstellungsschicht (`PdfTripPresenter`). Gespeicherte Reisedaten werden nicht für das Layout verändert. Der Presenter übersetzt alte und neue Snapshots in ein kompaktes Modell für Reiseüberblick, Kosten, Anreise, maximal drei Unterkünfte, maximal acht Aktivitäten, Kartenpunkte und Quellen. `TripPdfExporter` setzt dieses Modell als durchsuchbares Hochformat-PDF mit Inhaltsverzeichnis, internen Zielen, Lesezeichen, wiederholten Tabellenköpfen und eingebetteter Schrift um.

Mehrere gespeicherte Reisen werden in der Desktop-Anwendung einer Exportliste hinzugefügt und dort sortiert. Vor dem Export werden Unterkunft, Belegung, Anreisezeit und Kostenabdeckung geprüft. Der Nutzer kann gezielt nachrecherchieren, bewusst als unvollständige Reiseidee exportieren, unvollständige Reisen aus einer Mehrfachauswahl entfernen oder zurückkehren. Ein fehlendes Bild zählt nicht als blockierende Lücke.

## Bilder

Die explizite Aktion **Angaben & Bilder recherchieren** arbeitet auf einer Kopie der geöffneten Reise. Sie aktualisiert stabile Wikivoyage-Felder und sucht nur eindeutig zuordenbare Bilder:

- Zielbild: Seitenbild der exakten Wikivoyage-Zielseite;
- Unterkunft oder Aktivität: Wikimedia-Commons-Bild nur bei vorhandener exakter Wikidata-ID (`P18`);
- keine Namens- oder Bildersuche als Ersatz und keine Platzhalter;
- Freigabeliste für Public Domain, CC0, CC BY und CC BY-SA;
- Autor, Lizenz, Quellseite, Abrufdatum, Zuordnung und lokale Cachedatei werden gespeichert;
- 8 MB Dateigrenze, Zeitlimit, Abbruch und Offline-Fallback.

Die Commons-Action-API liefert Thumbnail-URL und `extmetadata`. Wikimedia weist darauf hin, dass die jeweilige Dateiseite und Lizenzbedingungen maßgeblich bleiben. Die API-Anfragen sind deshalb einzeln und begrenzt; das PDF führt Bildnachweise mit Quellseite auf.

## Karten

Die PDF enthält eine klar als schematisch bezeichnete geografische Übersicht aus belegten Koordinaten sowie nummerierte Marker, Legende und OpenStreetMap-Links. Sie zeichnet keine Straßen, Fahrtrouten oder unbekannten Standorte. Rasterkacheln werden nicht automatisiert für den Offline-PDF-Export geladen: Die OSMF Tile Usage Policy untersagt Hintergrund-Prefetching und Offline-Pakete des Standard-Kachelservers.

## Anreise und verbleibende Grenzen

Für das Auto bleiben die vorhandene OSRM-Straßenroute, getrennte Streckenabschnitte und die dokumentierte Kraftstoffschätzung erhalten. Maut, Vignetten, Parken und Fähren bleiben offen, wenn sie nicht belegt sind. Zug und Flug werden nicht als bestätigte oder günstigste Verbindung dargestellt. Der Export zeigt ihren Datenumfang und offene Kosten ausdrücklich.

Die DB Timetables API ist kostenlos registrierbar und liefert Bahnhofstafeln sowie Fahrtinformationen, aber keinen vollständigen Tür-zu-Tür-Verbindungs- und datierten Gruppenpreisvergleich. Sie wurde deshalb nicht als vermeintliche Buchungsauskunft integriert. Ebenso werden Portal-Suchergebnisse ohne belegten Zeitraum, Belegung, Gebührenumfang und Nutzungsrecht nicht als Unterkunftspreis übernommen.

Konkrete Aktivitäten stammen weiter aus expliziten Wikivoyage-vCards. Bei exakter Wikidata-ID können passende Bilder hinzukommen. Öffnungszeiten, Eintritt, Wanderroutendaten und Veranstaltungen werden nur gezeigt, wenn sie in den gespeicherten Feldern belegt sind. Fehlende Angaben bleiben offen; es werden keine Einträge zum Auffüllen erfunden.

## Quellenprüfung vom 28.10.2026

- MediaWiki Action API: `prop=imageinfo`, `iiprop=url|extmetadata`, begrenzte Thumbnail-Abfragen.
- Wikimedia Developer App Guidelines: Lizenz pro Bild prüfen und Attribution der jeweiligen Commons-Datei beachten.
- OpenStreetMap Foundation Tile Usage Policy: sichtbare Attribution, identifizierender User-Agent und Cache; kein Bulk-Download oder Offline-Prefetching.
- Deutsche Bahn API Marketplace, Timetables: kostenloser Nutzungsplan nach Registrierung; Bahnhofstafeln und Fahrtinformationen, keine vollständige Preis-/Buchungssuche.
