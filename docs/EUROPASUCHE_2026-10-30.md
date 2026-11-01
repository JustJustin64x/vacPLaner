# Europäische lokale Reisezielsuche – Prüfbericht vom 30.10.2026

Der GeoNames-Ortsbestand des definierten europäischen Suchraums ist eingerichtet und im normalen Suchpfad aktiv. Freizeitdaten liegen jetzt für sieben größere Gebiete vor. Sie sind weiterhin **keine europaweite Vollabdeckung**. Einrichtungsdialog, Suche und Ergebnisdetails machen diese Grenze sichtbar.

Der Ausgangsbericht vom 29.10. wurde anhand von Code und Anwendungsdatenbank bestätigt: 46 technisch auswählbare Länder/Gebiete, drei tatsächlich importierte GeoNames-Länder und drei kleine OSM-Ausschnitte. Der folgende Stand ersetzt diese Bestandszahlen. Die ursprünglichen Prüfprotokolle bleiben als Historie erhalten.

Alle tatsächlichen Zahlen, Quellenrevisionen, Prüfsummen, Ausschnittgrenzen, Vergleichskriterien, Ergebnisbelege und offenen Angaben stehen im [maschinenlesbaren Prüfbericht](EUROPASUCHE_PRUEFUNG_2026-10-30.json).

## Unmittelbar nutzbar

`Urlaubsplaner.command` startet die normale lokale Anwendung. Der Erstaufbau ist auf diesem Rechner erledigt; beim Programmstart werden keine Länder- oder PBF-Dateien geladen. Deutsch, Euro, Kilometer sowie die bisherigen Reise-, Preisrecherche- und PDF-Funktionen bleiben erhalten. Es wurden keine KI, zusätzlichen kostenpflichtigen Dienste oder Schlüssel eingerichtet.

Der Bestand enthält **852.761 Aufenthaltsorte** sowie **202.509 separat geführte Regions-, See- und Naturobjekte**. Es gilt keine allgemeine Einwohner-Mindestgrenze. Historische, aufgegebene Orte und reine Stadtteile werden nicht als eigenständige Aufenthaltsorte importiert. Geografische Ortsidentität, Quellenstand, alternative Namen und alternative Länderzuordnungen werden gespeichert.

Die Vorauswahl verwendet **34.532 räumliche Ortsvertreter**, einschließlich zusammengeführter Reiseführerziele. Die vollständigen Ortsdatensätze bleiben in SQLite/RTree aktiv und für Namensauflösung sowie Umgebungssuche erreichbar. Zwei stabile Vertreter je 0,35-Grad-Zelle, Land und Ortstyp begrenzen den Speicherbedarf. Die Typtrennung erhält Dörfer neben Städten. Das ist eine geografische Vorauswahl, keine Bewertung jedes europäischen Ortes auf vollständiger Angebotsgrundlage. OSM darf diese Auswahl nicht nachträglich mit allen dicht kartierten Nachbarorten auffüllen.

## Definierter europäischer Zielraum

Es gibt **55 technisch unterstützte und tatsächlich importierte Länder/Gebiete**. Die folgende Liste ist vollständig. Einwohnerzahlen dienen ausschließlich der Ortstyp-Einordnung, nicht als allgemeiner Eignungsbonus.

| Code | Unterstützt und importiert | Aufenthaltsorte | Regionsobjekte |
|---|---|---:|---:|
| AL | Albanien | 4.155 | 1.341 |
| AD | Andorra | 62 | 196 |
| BY | Belarus | 25.188 | 1.619 |
| BE | Belgien | 12.479 | 59 |
| BA | Bosnien und Herzegowina | 21.388 | 5.967 |
| BG | Bulgarien | 6.059 | 2.012 |
| DE | Deutschland | 75.974 | 8.589 |
| DK | Dänemark | 7.106 | 353 |
| EE | Estland | 6.921 | 375 |
| FI | Finnland | 24.492 | 43.387 |
| FR | Frankreich | 80.259 | 6.550 |
| FO | Färöer | 180 | 243 |
| GI | Gibraltar | 2 | 3 |
| GR | Griechenland | 14.230 | 3.053 |
| GG | Guernsey | 262 | 70 |
| IE | Irland | 11.987 | 2.766 |
| IS | Island | 115 | 2.609 |
| IM | Isle of Man | 43 | 15 |
| IT | Italien | 61.868 | 7.712 |
| JE | Jersey | 85 | 18 |
| KZ | Kasachstan (westlich des Ural) | 1.622 | 68 |
| XK | Kosovo | 2.564 | 984 |
| HR | Kroatien | 11.360 | 1.868 |
| LV | Lettland | 7.637 | 2.385 |
| LI | Liechtenstein | 67 | 73 |
| LT | Litauen | 20.555 | 2.424 |
| LU | Luxemburg | 641 | 8 |
| MT | Malta | 191 | 27 |
| MD | Moldau | 1.797 | 24 |
| MC | Monaco | 1 | 1 |
| ME | Montenegro | 4.000 | 2.503 |
| NL | Niederlande | 6.966 | 1.011 |
| MK | Nordmazedonien | 2.529 | 3.441 |
| NO | Norwegen | 13.183 | 34.438 |
| PL | Polen | 45.416 | 2.335 |
| PT | Portugal | 16.562 | 1.449 |
| RO | Rumänien | 15.425 | 3.342 |
| RU | Russland (europäischer Teil) | 145.046 | 12.587 |
| SM | San Marino | 24 | 7 |
| SE | Schweden | 27.961 | 13.798 |
| CH | Schweiz | 11.410 | 8.173 |
| RS | Serbien | 9.489 | 2.969 |
| SK | Slowakei | 4.981 | 1.561 |
| SI | Slowenien | 6.567 | 387 |
| ES | Spanien | 28.498 | 4.087 |
| SJ | Spitzbergen und Jan Mayen | 11 | 1.718 |
| CZ | Tschechien | 16.464 | 1.049 |
| TR | Türkei (europäischer Teil) | 1.024 | 81 |
| UA | Ukraine | 32.464 | 844 |
| HU | Ungarn | 10.048 | 677 |
| VA | Vatikanstadt | 1 | 0 |
| GB | Vereinigtes Königreich | 34.286 | 3.900 |
| CY | Zypern | 751 | 224 |
| AX | Åland | 336 | 104 |
| AT | Österreich | 20.029 | 7.025 |

Die Abgrenzung folgt der von der [Europäischen Umweltagentur beschriebenen Ural–Uralfluss–Manytsch–Bosporus-Konvention](https://www.eea.europa.eu/en/analysis/publications/92-826-5409-5/page003new.html). Für Russland/Kasachstan und die Türkei sind explizite Koordinatenpolygone in `EuropeScope.py` hinterlegt; sie werden auf jeden GeoNames-Datensatz angewandt. Diese **vereinfachte, reproduzierbare Anwendungsgrenze** ist kein vermessener Verlauf des Uralflusses und kein amtliches Kontinentalpolygon. Einzelne grenznahe Orte können dadurch ausgeschlossen bleiben. Kaliningrad und der europäische Teil Russlands sind enthalten; Sibirien und Anatolien werden nicht als Europa importiert.

Frankreich ist auf das europäische Mutterland einschließlich Korsika beschränkt; niederländische und britische Überseegebiete sowie Grönland sind ausgeschlossen. Spanien umfasst Festland und Balearen; Kanaren, Ceuta und Melilla liegen außerhalb dieser Definition. **Ausdrückliche Insel-Ausnahmen** sind Zypern, Azoren, Madeira, Island, Färöer sowie Spitzbergen/Jan Mayen. Die übrigen zu den gelisteten europäischen Mittelmeerländern gehörenden Inseln sind eingeschlossen. Die türkischen Inseln Imbros/Tenedos sind explizit erfasst.

**Armenien, Georgien und Aserbaidschan** liegen nach der gewählten Manytsch-Konvention außerhalb des Zielraums und werden deshalb ausdrücklich als ausgeschlossen dokumentiert. Das ist keine fehlende Downloadquelle. Belarus, Ukraine, Russland, Kasachstan und die europäischen Teile der Türkei wurden dagegen tatsächlich verarbeitet. Länder-/Gebietszuordnungen folgen den Quellidentitäten; dies ist weder eine politische Grenzentscheidung noch eine aktuelle Reiseempfehlung.

## Tatsächlicher Freizeitbestand

Die sieben neuen größeren Importbereiche umfassen zusammen 488.170 Objekteinträge vor Überschneidungsbereinigung. Im gesamten Bestand liegen **487.248 eindeutige OSM-Objekte** vor; die drei ursprünglichen Ausschnitte werden als Quellenstände mitverwaltet. Ein Objekt wird über `osm:Typ:ID` genau einmal gespeichert und kann mehreren Ausschnitten angehören.

| Tatsächlich verarbeitetes Gebiet | OSM-Einträge | Dateistand laut Header | Dauer inkl. Import/Quellen |
|---|---:|---|---:|
| Tirol gesamt | 54.440 | 2026-10-29T01:02:19Z | 124.8 s |
| Slowenien gesamt | 46.277 | 2026-10-28T21:21:02Z | 438.7 s |
| Kroatien gesamt | 82.410 | 2026-10-28T21:21:02Z | 327.1 s |
| Atlantik: Bretagne | 125.464 | 2026-10-28T21:21:02Z | 451.8 s |
| Ostsee: Mecklenburg-Vorpommern | 66.496 | 2026-10-28T21:21:02Z | 157.9 s |
| Binnenland: Niederschlesien | 58.810 | 2026-10-28T21:21:02Z | 236.5 s |
| Nordosteuropa: Estland | 54.273 | 2026-10-28T21:21:02Z | 168.7 s |


Tirol, Slowenien und Kroatien wurden aus vorhandenen Dateien neu und wesentlich breiter verarbeitet. Bretagne, Mecklenburg-Vorpommern, Niederschlesien und Estland wurden zusätzlich heruntergeladen. Die vier neuen PBF-Dateien umfassen **764.640.447 Byte** laut tatsächlichen Größenabfragen und gespeicherten Dateien. Die GeoNames-Vorprüfung ergab rund 106,4 MiB aus gerundeten Verzeichnisangaben; exakte Archivgrößen stehen im JSON. Ein Europa-PBF von etwa 33 GB wurde verworfen zugunsten regionaler Dateien. Die PBF-Verarbeitung nutzt temporäre dateibasierte Knotenindizes und speichert anschließend abgeleitete Merkmale/Geometriestichproben.

Nur diese sieben Länder besitzen größere zusätzliche OSM-Freizeitbestände; Frankreich, Deutschland, Polen und Österreich dabei jeweils **regional**. Auch Slowenien, Kroatien und Estland sind nur nach Quelle/Auszugsgrenze kartografisch erschlossen, nicht in Bezug auf reale Angebote vollständig erhoben. Für die übrigen **48 Länder/Gebiete** fehlen größere zusätzliche OSM-Freizeitimporte. Dort stehen GeoNames und teilweise der bestehende Reiseführerkatalog zur Verfügung. Die fehlenden Länder werden im JSON ausdrücklich aufgelistet.

## Abdeckung, Quellen und Importverhalten

Erfolgreiche Datensätze und Importversuche werden getrennt gespeichert. Eine fehlgeschlagene Aktualisierung ersetzt keinen funktionierenden Datenstand. Erfolgreiche Landesimporte bleiben bei späterem Abbruch erhalten; das gerade bearbeitete Land wird transaktional zurückgerollt. Wiederholung ersetzt anhand stabiler IDs statt Duplikate anzulegen. Bereits vorhandene vollständige Downloads werden wiederverwendet. Angefangene Downloads dürfen sicher neu gestartet werden; eine bytegenaue Fortsetzung wird nicht zugesichert.

Pro Bereich sind Quelle, Zeit, Kategorien und räumliche Grenzen hinterlegt. Geofabrik-Polygone begrenzen, soweit abrufbar, die tatsächlich untersuchte Auszugsfläche. Ein PBF-Dateiname oder seine rechteckige Hülle wird **nicht** als bestätigte Länderzuordnung einzelner Unterkünfte benutzt. Ohne belastbare Zuordnung bleiben verbindliche geografische Anforderungen offen.

Die Interessenprofile unterscheiden „nicht untersucht“, „untersucht, keine passenden kartierten Objekte im Radius“, „Quelle nicht erreichbar“, „teilweise untersucht“ und „passende Karteneinträge vorhanden“. Erfolgreiche Kartierung ist ausdrücklich keine Vollerhebung realer Angebote. Ruhe bleibt ohne geeigneten Nachweis unbekannt. Negative Ergebnisse beziehen sich auf abgefragte Kartendaten, nicht auf das sichere Fehlen realer Angebote.

Geprüfte Quellen und Zugänge:

- [GeoNames: Dumpformat, Aktualisierung und CC BY 4.0](https://download.geonames.org/export/dump/readme.txt). Kostenlose Länderdateien; keine Registrierung. Alle 55 Importe waren erfolgreich.
- [Geofabrik Europa und regionale Downloads](https://download.geofabrik.de/europe.html), [OSM France Tirol](https://download.openstreetmap.fr/extracts/europe/austria/). Vier neue Downloads, drei vorhandene Dateien und sieben erfolgreiche PBF-Importe; OSM/ODbL-Quellenstände sind gespeichert.
- [Pyosmium-Filterdokumentation](https://docs.osmcode.org/pyosmium/latest/user_manual/04-Working-with-Filters/). Der neue Leser bestimmt Relationen zuerst und erhält unmarkierte Wege, Knotenreferenzen und verschachtelte Mitglieder. Fehlende Mitglieder werden gekennzeichnet. Geometriestichproben ersetzen weder vollständige Topologieprüfung noch einen bekannten Wanderstart.
- [Overpass Private.coffee: Bedingungen und Zugang](https://overpass.private.coffee/) sowie [Ressourcenteilung](https://dev.overpass-api.de/overpass-doc/en/preface/commons.html). Ein zusätzlicher Live-Abruf in Tallinn scheiterte nach 22.018 Sekunden am Netzwerk-/Zeitlimit. Es wird weiterhin **kein erfolgreicher Live-Overpass-Abruf** behauptet. Fehlerstatus und Rückoffzeit vermeiden ständige Wiederholungen.
- [FOSSGIS/OSRM: Betrieb und Nutzungsregeln](https://routing.openstreetmap.de/about.html). Kostenloses Fußwegmodell praktisch erfolgreich geprüft. Höchstens zwei gebündelte Prüfungen je normaler Suche, jeweils höchstens zwei Punktangebote; serielle Abrufe mit mindestens 1,1 Sekunden Abstand und 30-Tage-Cache. Keine privaten Startadressen werden für diese Prüfungen übertragen.

Die vorhandenen 60 Wikidata-Identitäten wurden erhalten. In diesem Ausbau wird keine neue flächige Wikidata-Abfrage behauptet. GISCO-Ländergrenzen wurden als mögliche weitere Referenz recherchiert, aber nicht integriert; daraus werden keine bestätigten Länderzuordnungen abgeleitet.

## Bewertungs- und Auswahlregeln

Die Suche trennt geografische Vorauswahl, belegte Interessenpassung, begrenzte Ergänzung und vertiefte Unterkunfts-/Transportrecherche. Standardmäßig stehen zwei kleine regionale Zusatzabfragen für plausible **noch nicht untersuchte** Regionen bereit, maximal drei. GeoNames-Seen/-Naturregionen dienen als Recherchehinweise; sie erzeugen keinen positiven Interessenwert. Ein Quellenausfall lässt die lokale Suche weiterlaufen und wird mit gezieltem Einrichtungsangebot angezeigt. Die Kontrollkampagne schaltet diese Ergänzung bewusst ab, damit bei allen Interessen derselbe Datenbestand verglichen wird; ein eigener Live-Test prüft den Ausfallweg.

Wenn noch keine Interessenbelege vorliegen, erhalten bis zu drei bekannte Reiseführer-Quellseiten eine reservierte Gelegenheit zur vertieften Recherche. Das verändert den vorläufigen Passungswert nicht. Tatsächlich gelesene, lokalisierte Angebote ergänzen später Bewertung und Erklärung mit höchstens 40 % Themenstärke; unlokalisierte Einträge und unbelegte Ruhe bleiben unberücksichtigt. Auch die übrigen Reiseführerziele verwenden dieselbe kartografische Merkmalsbewertung. Ihre abgeleiteten Profile sind revisionsabhängig gecacht.

Belegzahlen werden pro Kategorie gesättigt. Grünflächen ergeben keinen Ruhebonus; Wasser allein ergibt keine Badeeignung, ein einzelner Weg keine Wanderrelation. Badeschwimmbereiche und Strände unterscheiden sich von bloßen Gewässern. Einzelne Bars und Clubs bleiben schwache Hinweise. Barhopping benötigt mehrere Bars in einem kompakten Umfeld von 800 Metern, höchstens zwei Kilometer Luftlinie vom Basisort; die Bewertung bleibt ohne bestätigte Fußwege begrenzt.

Wandern/Baden wird über beide Komponenten bewertet. Badebelege liegen höchstens acht Kilometer entfernt; ausschließlich mehr als fünf Kilometer entfernte Badeangebote werden zusätzlich begrenzt. Wanderbelege verwenden höchstens zehn Kilometer Luftlinie zu Stichproben, samt Hinweis auf unbekannte Schwierigkeit, Zugang und persönliche Eignung. Unvollständige Relationsgeometrien begrenzen die Bewertung.

Kultur/Nachtleben benötigt für eine hohe gemeinsame Bewertung außerdem zusammenliegende Kultur- und Ausgehbelege: maximal 1,5 Kilometer Luftlinie zwischen ihnen. Ein Museum im einen Nachbarort und Clubs auf der anderen Seite des Basisortes ergeben keine starke gemeinsame Bewertung. Namentlich bekannte Museen/Schlösser stehen bei den Belegen vor einer Menge kleiner unbenannter Kunstobjekte.

Nahe Ziele und weitgehend gemeinsam genutzte Aktivitäten werden grenzübergreifend zusammengefasst. Regionszugehörigkeit beeinflusst Vielfalt; Verwaltungszugehörigkeit allein unterdrückt keine unterschiedlichen Reiseorte. Vielfalt greift nur unter ähnlich passenden Kandidaten. Nach verbindlichen Unterkunfts-/Transportausschlüssen werden weitere Kandidaten geprüft. Zeitraum, Dauer, Reisende/Zimmer, Gebiet, Ausstattung, Verkehrsmittel, Reisezeit und Budgetlogik werden nicht gelockert. Unbekannte Preise/Fahrzeiten ergeben keinen Vorteil.

Für vertiefte Vorschläge werden geeignete echte OSM-Punktangebote im Fußwegmodell geprüft. Entfernung, Modellzeit, Versatz zum angeschlossenen Wegepunkt und Quelle werden gespeichert. Das ist **keine Bestätigung des Eingangs oder der letzten Meter**. Für Flächen/Wanderrelationen ohne bestätigten Zugang bleibt die Wegprüfung offen; ihre Repräsentanten werden nicht als Wanderstarts geroutet. Die individuellen Nachweise stehen im JSON unter `access_research`.

## Echte Vergleichssuchen und auffällige frühere Ziele

Abschließend wurden 30 kontrollierte Suchläufe über sechs Teilräume mit dem endgültigen Index durchgeführt; keiner endete mit einem Fehler oder Zeitabbruch. Gemessene Laufzeiten: 2.02–18.84 Sekunden. Zusammen 4 tatsächliche HTTP-Aufrufe; weitere Angaben stammen aus dem lokalen Bestand/Cache. Zusätzliche frühere Kontroll- und Fußwegprüfungen sind getrennt im JSON erhalten.

Die Kontrollparameter sind Berlin, Juli 2027, sieben Kalendertage, zwei Erwachsene/ein Zimmer, Gruppenbudget 2.000 €, gleiche Gewichte, Zug als unbestätigte Transportoption, zehn vertiefte Kandidaten, vier HTTP-Abfragen und 120 Sekunden Höchstzeit. Preisrecherche und regionale Zusatzabfragen sind abgeschaltet. Die ersten vier Fälle je Teilraum ändern ausschließlich die Interessen. Der fünfte vergleicht Baden/Wandern zusätzlich mit ausdrücklich bevorzugten kleinen Orten. Diese Kontrollen prüfen die Zielauswahl, **keinen** bestätigten Zugfahrplan oder buchbaren Komplettpreis.

| Teilraum | Interessen / Präferenz | Erste ausgegebene Ziele (Kartierungsorientierung) |
|---|---|---|
| Alpen | Wandern und Ruhe | Seefeld in Tirol (21%, passend); Walchsee (21%, offen); Scholastika (21%, offen) |
| Alpen | Baden und Wandern | Seefeld in Tirol (73%, passend); Ellmau (73%, passend); Walchsee (73%, offen) |
| Alpen | Kultur und Nachtleben | Innsbruck (100%, passend); Kitzbühel (77%, passend); Obergurgl (44%, passend) |
| Alpen | Barhopping | Ellmau (65%, passend); Seefeld in Tirol (65%, passend); Obergurgl (65%, passend) |
| Alpen | Kleine Orte | Seefeld in Tirol (73%, passend); Ellmau (73%, passend); Walchsee (73%, offen) |
| Mittelmeer | Wandern und Ruhe | Benkovec (21%, passend); Mareda (21%, passend); Nova Drenčina (21%, passend) |
| Mittelmeer | Baden und Wandern | Mareda (73%, passend); Opatija (73%, passend); Dolinci (73%, passend) |
| Mittelmeer | Kultur und Nachtleben | Zagreb (100%, passend); Monterol (100%, passend); Rijeka (100%, passend) |
| Mittelmeer | Barhopping | Zagreb (65%, passend); Monterol (65%, passend); Opatija (65%, passend) |
| Mittelmeer | Kleine Orte | Mareda (73%, passend); Opatija (73%, passend); Dolinci (73%, passend) |
| Atlantik | Wandern und Ruhe | Bel-Air (21%, offen); La Ville Gueurie (21%, offen); Pléhérel-Plage-Vieux Bourg (21%, offen) |
| Atlantik | Baden und Wandern | Notre-Dame de la Cour (73%, offen); Landrellec (73%, offen); Vannes (73%, offen) |
| Atlantik | Kultur und Nachtleben | Rennes (100%, offen); Saint-Brieuc (100%, offen); Vannes (100%, offen) |
| Atlantik | Barhopping | Fougères (65%, offen); La Ville Gueurie (65%, offen); Rennes (65%, offen) |
| Atlantik | Kleine Orte | Notre-Dame de la Cour (73%, offen); Landrellec (73%, offen); Vannes (73%, offen) |
| Ostsee | Wandern und Ruhe | Rechlin Nord (21%, offen); Ausbau (21%, offen); Bakendorf Siedlung (21%, offen) |
| Ostsee | Baden und Wandern | Rechlin Nord (73%, offen); Ablage (73%, offen); Sassnitz (73%, offen) |
| Ostsee | Kultur und Nachtleben | Rostock (100%, passend); Waren (Müritz) (40%, passend); Neubrandenburg (100%, offen) |
| Ostsee | Barhopping | Waren (Müritz) (65%, passend); Zingst (65%, passend); Neubrandenburg (65%, offen) |
| Ostsee | Kleine Orte | Rechlin Nord (73%, offen); Ablage (73%, offen); Sassnitz (73%, offen) |
| Binnenland | Wandern und Ruhe | Węgliniec (21%, offen); Drożyna (21%, offen); Neu Scheibe (21%, offen) |
| Binnenland | Baden und Wandern | Bolesławiec (73%, offen); Neu Scheibe (73%, offen); Legnica (73%, offen) |
| Binnenland | Kultur und Nachtleben | Legnica (100%, offen); Wrocław (100%, offen); Strupice (45%, offen) |
| Binnenland | Barhopping | Zgorzelec (65%, offen); Góra (65%, offen); Legnica (65%, offen) |
| Binnenland | Kleine Orte | Bolesławiec (73%, offen); Neu Scheibe (73%, offen); Gniewomierz (73%, offen) |
| Nordosteuropa | Wandern und Ruhe | Vilivalla (21%, passend); Vilkla (21%, passend); Sindi (21%, passend) |
| Nordosteuropa | Baden und Wandern | Viira (73%, passend); Haapsalu (73%, passend); Pärnu (73%, passend) |
| Nordosteuropa | Kultur und Nachtleben | Pärnu (100%, passend); Tallinn (100%, passend); Tartu (100%, passend) |
| Nordosteuropa | Barhopping | Kuressaare (65%, passend); Haapsalu (65%, passend); Pärnu (65%, passend) |
| Nordosteuropa | Kleine Orte | Viira (73%, passend); Haapsalu (73%, passend); Pärnu (73%, passend) |

Zusätzlich wurde **Norwegen ohne größeren OSM-Import** geprüft: 8,48 Sekunden, drei HTTP-Aufrufe und drei reservierte Quellseiten. Oslo und Bergen erhielten konkrete Kulturbelege (unter anderem Storting, Lepramuseet und KODE); Nachtleben blieb ohne Nachweis. Die kombinierte Orientierung beträgt dort nur 12 %, keinen starken Kultur-/Nachtlebenwert. Weitere Vorschläge bleiben teilweise offene Ideen ohne Interessenbelege. Dieser Lauf zeigt die Ergänzung aus vorhandenen Quellen und zugleich die Grenze fehlender Freizeitkartierung.

Für jedes ausgegebene Ziel enthält das JSON Auswahlbegründung, konkrete OSM-Quellen/Objektidentitäten, Belegentfernungen, untersuchte Kategorien, offene Pflichtangaben und Kostenlücken. Die Diagnose enthält untersuchte und gruppierte Alternativen. Die Kombination aus geografischer Vorauswahl, Belegsättigung und fehlendem Unbekannt-Bonus verhindert einen automatischen Sieg dicht kartierter Ausschnitte; sie beweist keine optimale Auswahl für schlecht erschlossene Länder.

| Früher auffälliger Ort | Wandern/Ruhe | Baden/Wandern | Kultur/Nachtleben | Barhopping |
|---|---:|---:|---:|---:|
| Rum | 21% | 73% | 45% | 15% |
| Reith bei Seefeld | 21% | 73% | 10% | 0% |
| Eng | 12% | 12% | 6% | 0% |
| Dovje | 12% | 40% | 18% | 0% |
| Absam | 12% | 52% | 30% | 65% |
| Jesenice | 21% | 73% | 30% | 65% |

Rum bleibt mit vorhandenen Kultur-/Clubangeboten grundsätzlich plausibel, erhält aber keinen starken Kombinationswert ohne belegtes gemeinsames Viertel. Reith bei Seefeld besitzt Bade-/Wanderhinweise, jedoch keinen belegten Nachtleben-Schwerpunkt. In Eng gibt es im engeren Bade-Radius keine passenden Belege; der frühere Bade-/Wander-Vorschlag ist damit nicht mehr stark begründet. Dovjes Badestelle in Jesenice liegt rund 7,8 Kilometer Luftlinie entfernt; tatsächlicher Weg und Zugang bleiben offen. Absams Bars liegen teilweise in Hall; das ist als kompaktes Umfeld plausibel, nicht als eigenständiges großes Nachtleben Absams. Jesenice besitzt zentrale Bars und eine kartierte Badestelle, aber keine belegte Clubdichte. Keiner der sechs Orte wird pauschal ausgeschlossen.

## GUI, Tests und gemessene Leistung

Gemessen auf Apple M4 mit 16 GiB RAM:

| Vorgang | Tatsächlich gemessen |
|---|---:|
| GeoNames-Aufbau aller 55 Dateien | 53.498 s |
| Sieben PBF-Verarbeitungen inkl. ergänzender Downloads/Metadaten | 1905.358 s |
| Abschließender Indexaufbau | 59.385 s |
| Controllerstart der Kontrollkampagne | 7.544 s |
| Anwendungsinitialisierung mit warmem vollständigem Index | 2.029 s |
| Natives Fenster mit vorhandenem Index bereit | 2.385 s |
| Zieldatenbank, physische Dateigröße | 2.311.426.048 Byte |
| Wiederverwendbare Download-Dateien | 1.513.500.915 Byte |
| Spitzen-RSS im GeoNames-Prozess | 74.153.984 Byte |
| Spitzen-RSS im PBF-Prozess | 1.193.476.096 Byte |
| Spitzen-RSS im abschließenden Index-Prozess | 733.773.824 Byte |
| Spitzen-RSS der abschließenden 30 Suchläufe | 805.666.816 Byte |
| Echte GUI-Suche (Estland) | 4.852 s |

RSS ist die gemessene Prozessspitze einschließlich nativer Bibliotheken, keine Messung des gesamten Systems. Die Laufzeiten verwenden die monotone Prozessuhr; unterbrochene Arbeits-/Ruhezeiten des Rechners sind kein Suchleistungsmaß. Downloads und Erstaufbau sind ausdrücklich getrennt von normalen Suchen.

Die normale GUI wurde mit echtem Anwendungsbestand, echten Formularwerten, Suchworker und Ergebnis-Tabellen geprüft. Eine estnische Kultur-/Nachtleben-Suche lieferte drei im Widget sichtbare Filtertreffer; Preise und Zugverbindungen blieben ausdrücklich unbekannt. Hauptfenster und Ergebnisdarstellung wurden visuell kontrolliert. Der Einrichtungsworker, Abbruch, Katalogübernahme, Reiseerhalt und PDF-Funktionen werden zusätzlich durch die Tk-Integrationstests geprüft. Native automatisierte Reiterklicks lieferten über die macOS-Schnittstelle keine bestätigte Zustandsänderung; eine vollständige manuelle Klickabnahme aller Bedienelemente wird nicht behauptet.

179 automatisierte Tests bestehen. Sie prüfen unter anderem europäische Abgrenzung/Übersee-Ausnahmen, Länderwechsel stabiler IDs, unbekannte/negative/teilweise Merkmale, Quellenausfall, wiederholte und abgebrochene Importe, unmarkierte/verschachtelte Relationsmitglieder, fehlende Geometrie, lokale Interessenänderungen, kompakte Bargruppen, gemeinsame Kultur-/Nachtlebenbereiche, Regionsduplikate über Grenzen, Nachrücken, Pflichtfilter und gespeicherte Reisen/PDF. Die reale Nutzerdatenbank enthielt zu Beginn keine gespeicherten Reisen und blieb unverändert; der Bestandsschutz bestehender Reise-Snapshots wird deshalb zusätzlich an gezielt gespeicherten Testreisen geprüft.

## Bedienung und verbleibende Ergänzungen

Unter **Reise → Zieldaten einrichten** lassen sich Länder nach Namen auswählen, der europäische Ortsbestand einrichten/fortsetzen oder gezielt aktualisieren, eine der sieben größeren Freizeitregionen laden sowie eigene Ausschnitte ergänzen. Vorhandene regionale PBF-Dateien können mit gewähltem oder eigenem Ausschnitt verwendet werden. Eine weitere Schaltfläche ergänzt höchstens drei getrennte Ortsumfelder im aktuellen Suchgebiet über begrenzte Onlineabfragen. Bei Overpass-Ausfall bleiben die regionalen Dateien der funktionierende Weg. Datenstände, fehlende Länder, Fehler und Speicherverbrauch stehen im Dialog. Abbruch behält abgeschlossene Arbeit; große Importe laufen getrennt von normalen Suchen.

Für die übrigen 48 Länder/Gebiete sind größere Freizeitimporte offen. Geeignete lokale regionale Dateien sind nachladbar; für sehr große Dateien ist ein kleinerer Auszug erforderlich. Der Ausbau behauptet weder vollständige reale Freizeitangebote noch bestätigte Ruhe, Zugänge, Saisonöffnungen, Unterkunftsmerkmale, Zimmerverfügbarkeit, Gesamtpreise oder europaweit beste Vorschläge. Verbindliche Angaben bleiben bis zu einer belastbaren Prüfung offen. Es wurden keine zusätzlichen KI- oder Abodienste installiert.

Reproduzierbare Prüfungen nach vorhandenem Aufbau:

```bash
.venv/bin/python -m unittest discover -q
.venv/bin/python scripts/verify_europe_search.py --live --output tmp/europe-verification
```
