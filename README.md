# Modulares Urlaubsplanungs-Tool (Clean Architecture Reiseplanungs-Aggregator)

Ein robustes, entkoppeltes und modulares Reiseplanungs-Tool, das Reisedaten aus verschiedenen externen Quellen aggregiert und validierte, bezugsfertige Urlaubspakete generiert.

[![Continuous Integration](https://img.shields.io/badge/tests-29%20passed-brightgreen.svg)]()
[![Architecture](https://img.shields.io/badge/Architecture-Clean%20Architecture-blue.svg)]()
[![Python](https://img.shields.io/badge/Python-3.9+-yellow.svg)]()

---

## 1. Kernziel
Die Anwendung aggregiert Reisedaten aus unterschiedlichen Verkehrsmodi (Flug, Bahn, Auto), Unterkunftsdaten und Sehenswürdigkeiten, um komplette Urlaubsrouten zu erstellen. Das System kombiniert Startort, Zielort und Reisedaten zu fertigen Paketen aus Transport und Übernachtung inklusive Budget- und Zeitplan-Validierung.

---

## 2. Architektur & Design-Prinzipien (Strikte Einhaltung)

Das System folgt strikt der **Clean Architecture** (Robert C. Martin) mit Inversion of Control und absoluter Unabhängigkeit des fachlichen Kerns:

```
src/vacation_planner/
├── core/                               # Fachlicher Kern (ISOLIERT, ZERO DEPENDENCIES)
│   ├── domain/
│   │   ├── models/                    # Entitäten und Aggregate Roots
│   │   │   ├── Location.py
│   │   │   ├── Attraction.py
│   │   │   ├── TransportOption.py
│   │   │   ├── AccommodationOption.py
│   │   │   ├── VacationSearchCriteria.py
│   │   │   └── VacationPackage.py
│   │   └── value_objects/             # Unveränderliche Wertobjekte
│   │       ├── TransportType.py
│   │       ├── AccommodationType.py
│   │       ├── MonetaryAmount.py
│   │       ├── GeographicCoordinates.py
│   │       ├── DateRange.py
│   │       └── RouteSegment.py
│   ├── interfaces/                    # Ports (Abstrakte Schnittstellenverträge)
│   │   ├── TransportGatewayInterface.py
│   │   ├── AccommodationGatewayInterface.py
│   │   ├── LocationGatewayInterface.py
│   │   └── PackageRepositoryInterface.py
│   └── use_cases/                     # Anwendungsfall-Logik & Domänenservices
│       ├── CostCalculationService.py
│       ├── TravelPackageAggregatorService.py
│       └── GetVacationPackageDetailsUseCase.py
│
├── infrastructure/                    # Externe Adapter & Scraper/APIs
│   ├── adapters/
│   │   ├── transport/                 # Flug-, Bahn- & Pkw-Adapter
│   │   │   ├── FlightTransportAdapter.py
│   │   │   ├── TrainTransportAdapter.py
│   │   │   ├── CarRouteTransportAdapter.py
│   │   │   └── CompositeTransportAdapter.py
│   │   ├── accommodation/             # Hotel-, Apartment- & Hostel-Adapter
│   │   │   └── HotelAccommodationAdapter.py
│   │   ├── location/                  # Geocoding & Attraktionen
│   │   │   ├── GeographicLocationAdapter.py
│   │   │   ├── LocalAttractionAdapter.py
│   │   │   └── CompositeLocationGatewayAdapter.py
│   │   └── persistence/               # Thread-sichere Ablage
│   │       └── InMemoryPackageRepository.py
│   └── mappers/                       # Explizite Daten-Mapper mit Inline-Dokumentation
│       ├── FlightDataMapper.py
│       ├── TrainDataMapper.py
│       ├── CarRouteDataMapper.py
│       ├── HotelAccommodationDataMapper.py
│       ├── GeographicLocationDataMapper.py
│       └── AttractionDataMapper.py
│
└── entrypoints/                       # Primäre Einfallstore (Backend als Vermittler)
    ├── web/                           # REST Web API
    │   ├── VacationPackageDtoMapper.py
    │   ├── VacationPlannerHttpHandler.py
    │   └── VacationPlannerHttpServer.py
    └── cli/                           # Interaktive Terminal-Anwendung
        └── VacationPlannerCliApplication.py
```

### Strikte Architektur-Vorgaben:
1. **Core-Isolierung:** Die Core-Schicht hat **keine** Abhängigkeiten zu externen Frameworks oder APIs. Sie verwendet ausschließlich die Python-Standardbibliothek (`decimal`, `datetime`, `math`, `typing`, `abc`, `uuid`).
2. **Backend als Vermittler:** Alle externen Datenquellen (Fluggesellschaften, Bahngesellschaften, Routing-Engines, Unterkunftsdatenbanken, Geodaten) werden ausschließlich über die Infrastructure-Schicht des Backends konsumiert. Das Frontend führt **keine** direkten Drittanbieter-Aufrufe aus.
3. **Strikte Dateitrennung:** Genau eine Klasse bzw. Struktur pro Datei.
4. **Explizite Namensgebung:** Keine kryptischen Abkürzungen (`GeographicCoordinates` statt `GeoCoord`, `MonetaryAmount` statt `MoneyVal`).
5. **Keine Platzhalter:** Sämtliche Entfernungsberechnungen (Haversine-Formel), Währungskalkulationen (`Decimal`), Zeitpläne, Umstiegszähler und CO2-Emissionsmodelle sind vollständig und mathematisch korrekt implementiert.

---

## 3. Funktions-Roadmap

- **Transport-Modul:** Berechnung und Integration von Flügen (inkl. Layover/Flugsegmenten), Zugverbindungen (ICE, TGV, Umstiege) und Straßenrouten (Entfernung, Maut, Benzinverbrauch, CO2-Bilanz).
- **Unterkunfts-Modul:** Dynamische Preisberechnung für Hotels, Ferienwohnungen, Hostels und Resorts basierend auf der Aufenthaltsdauer (`calculate_total_nights()`) und Ausstattungsmerkmalen.
- **Lokations-Modul:** Auflösung von Geokoordinaten und automatische Anreicherung von Sehenswürdigkeiten und Freizeitaktivitäten am Zielort.
- **Aggregator-Service:** Kernlogik zur Synchronisation von Hinreise, Rückreise und Hotel-Check-in/Check-out sowie Prüfung der Budget-Vorgaben.

---

## 4. Ausführung & Schnelleinstieg

### A. Ausführung der Testsuite
```bash
python3 -m unittest discover -s tests -p "test_*.py"
```
*Ergebnis: 29 Tests (Unit- und Integrationstests), 100 % Erfolgsquote.*

### B. Interaktive CLI-Nutzung
```bash
python3 main.py --origin Berlin --destination Paris --start-date 2026-07-01 --end-date 2026-07-07 --budget 1200 --travelers 2
```

### C. Starten des REST Web API Servers
```bash
python3 main.py --serve --port 8080
```

#### API Endpunkte:
- **`GET /api/v1/health`**: Health Check
- **`POST /api/v1/packages/search`**: Sucht und generiert Urlaubspakete
  ```bash
  curl -X POST http://127.0.0.1:8080/api/v1/packages/search \
    -H "Content-Type: application/json" \
    -d '{
      "origin": "Berlin",
      "destination": "Paris",
      "start_date": "2026-07-01",
      "end_date": "2026-07-07",
      "maximum_budget": 1500.0,
      "number_of_travelers": 2,
      "allowed_transport_types": ["FLIGHT", "TRAIN", "CAR"]
    }'
  ```
- **`GET /api/v1/packages/{package_id}`**: Ruft Paketdetails anhand der ID ab.

---

## 5. Entwicklungs-Log
Gemäß Anforderung wird jede ausgeführte Aktion lückenlos in [`PROJECT_LOG.md`](PROJECT_LOG.md) chronologisch protokolliert.
