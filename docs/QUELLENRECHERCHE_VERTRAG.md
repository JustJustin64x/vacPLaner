# Schritt 4 – begrenzter Quellenvertrag

Vorab festgelegter Umfang: deutsche Wikivoyage-Artikel aus einer bereits vorhandenen Ziel-URL, zugehöriges Wikidata-Objekt und dessen Länderobjekt über Special:EntityData. Keine allgemeine Websuche und keine vom Modell erfundenen Orte oder URLs. Für Ziele ohne nachprüfbare Identität bleibt die Nachrecherche offen.

Identität: Wikivoyage-Geoindikator (Koordinaten/Land), verknüpftes Wikidata-Objekt, passende Zielbezeichnung und Wikidata-Koordinaten. Das Länderobjekt muss denselben ISO-Code bestätigen. Unterschiedliche Wikidata-/GeoNames-IDs oder fehlende/abweichende Länder-/Koordinatenangaben sperren die Übernahme. Kartenpunkte von Aktivitäten müssen im gewählten Umkreis liegen; eine Region wird nicht als konkreter Aufenthaltsort ausgegeben.

Neue Belege: höchstens acht begrenzte strukturierte vCard-Beobachtungen, vollständige veröffentlichte Öffnungsfelder und ausdrücklich bezeichnete Zugangshinweise, jeweils mit Quellenausschnitt, Herkunft, Abrufzeit, Quellenrevision soweit verfügbar und Geltungsgrenzen. Lange oder verschachtelte Felder werden nicht als abgeschnittene Behauptung übernommen. Preise und Veranstaltungen werden nicht übernommen. Alle Beobachtungen bleiben Aussagen der Quelle, keine unabhängig bestätigte Eignung oder Zusage für den Reisetag.

Die lokale KI darf nur vorhandene Beleg-IDs und erlaubte Aussagearten auswählen. Kein freier Modelltext, kein Abrufwerkzeug, keine neuen URLs. Feldwerte, Fundstellen, Zahlen und Negationen bleiben unverändert aus dem geprüften Quelleintrag. Kein neuer Beleg erhält Rankingwirkung. Neue Belegtypen erscheinen separat; Schritt 2 wird nicht um freie Schlussfolgerungen erweitert.

Netzwerk: nur freigegebene öffentliche HTTPS-Hosts/Pfade, DNS-Prüfung aller aufgelösten Adressen und an dieselbe IP gebundene TLS-Verbindung, jede Weiterleitung erneut prüfen. Keine Proxys, curlrc, Cookies, lokalen oder privaten Ziele. Robots-Regeln, serielle Rate-Limits, begrenzte Downloads und Abbruch. Standardbudget der neuen Textrecherche: zehn HTTP-Transaktionen inklusive Robots/Redirects, höchstens 75 Sekunden, maximal 2 MB je Dokument und 128 KB Robots. Kontext und Modellzeit zusätzlich an Restbudget gebunden. HTTP-Cache speichert nur begrenzte extrahierte Daten und Robots-Regeln, keine vollständigen Webseitenarchive.

Bestehende Wikimedia-Bildabfragen im selben Nachrecherche-Ablauf verwenden ebenfalls die sichere Abrufschicht. Robots-verbotene API-Pfade werden nicht umgangen; vorhandene Bilder bleiben erhalten, nicht mögliche Aktualisierungen werden gemeldet.
