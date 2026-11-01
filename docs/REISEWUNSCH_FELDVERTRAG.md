# Feldvertrag für lokale Reisewünsche

Die Modellantwort ist ein partieller Vorschlag. Zulässig sind nur ganze, unabhängig erkannte Aussagen; freie Interpretation allein genügt nicht. Die erste Version unterstützt bewusst begrenzte deutsche Formulierungen. Andere Angaben bleiben zur manuellen Präzisierung sichtbar. Kein Formularstandard ist eine extrahierte Tatsache.

| Angabe | Bestehende Felder | Regel |
|---|---|---|
| Explizite Erwachsene / Zimmer | adults / rooms | Ganze Zahl, auch ausgeschriebene Zahlen eins bis zwölf; keine Ableitung voneinander |
| Kalendertage / Nächte | min_days + max_days | Genaue Dauer gemeinsam setzen; Nächte + 1, sichtbar erläutert |
| Expliziter ISO-Zeitraum, Monat mit Jahr | earliest + latest | Gemeinsam setzen, Datum unabhängig prüfen |
| Nächster Juli / Juli nächsten Jahres | earliest + latest | Europe/Berlin; nächster Juli = nächster noch nicht begonnener Juli; Juli nächsten Jahres = aktuelles Jahr + 1 |
| Ausdrückliches Gruppen-/Gesamtbudget in EUR | budget | Dezimalarithmetik, keine Umrechnung pro Person/Tag/Nacht |
| Expliziter Startort | origin | Kopie des genannten Orts, keine Geokodierung oder Adresse |
| Maximale Stunden je Richtung | max_hours | Positiver expliziter Wert |
| Verkehrsmittel | modes | „mit“ ergänzt, „nur mit“ ersetzt, „nicht mit“ entfernt; leere Liste scheitert an Gesamtvalidierung |
| Land / Region / Ausschluss mit eindeutiger Feldbezeichnung | countries / regions / excluded | Einzelnen Namen ergänzen; „nur Land/Region“ ersetzt; Gebietsidentität wird hier nicht recherchiert |
| Interessen mit Zahl 0–5 | einzelner interests-Eintrag | Nur diesen Eintrag setzen; kein erfundenes Gewicht für ungewichtete Interessen |
| Bekanntes Merkmal ist Pflicht / Wunsch / egal | required / desired | Genau dieses Merkmal umsetzen; alle anderen erhalten |
| Expliziter Zieltyp | target_type | Nur vorhandene Aufzählungswerte, keine Übersetzung von „keine Großstadt“ |

Nicht automatisch unterstützt: Kinder, harte negative Aktivitätsfilter, fehlende Jahre, Monatsnamen ohne Jahr, ungewichtete Interessen, ungeklärter Budgetumfang/Währung, bedingte oder alternative Wünsche. Bei Fragen, hypothetischen, Konditional-/Korrektur-/Alternativformulierungen wird konservativ die gesamte Auswertung zur Klärung zurückgehalten. Widersprüchliche Angaben zum selben Feld werden sämtlich blockiert. Freie Zusatztexte werden nicht als vollständig verstanden ausgegeben.

Das Modell erhält den Originaltext und Feldbeschreibungen, keine deterministisch vorgegebenen Musterantworten, Formularwerte oder gespeicherten Reisen. Das Modell liefert ausschließlich Feld und vollständige Originaltextstelle. Werte, Einheiten, Operationen und Datumsauflösung werden ausschließlich vom Programm abgeleitet. Eine echte Textstelle allein genügt nicht: Sie muss eine vollständige unterstützte Aussage sein und zum vorgeschlagenen Feld passen. Zusätzliche Modellwerte werden abgewiesen. Nicht vom Modell extrahierte, aber regelhaft erkannte Angaben werden als ausgelassen gemeldet und nicht still ergänzt.
