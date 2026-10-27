#!/usr/bin/env python3
"""
Main entry point for the Modulares Urlaubsplanungs-Tool.
Starts the Visual Dashboard Window by default, or provides CLI / REST server modes.
"""
from __future__ import annotations

import argparse
import sys
import os
from pathlib import Path

# Use the project runtime for direct macOS system-python invocations.
# Never modify the Apple Python installation or user interpreter settings.
if __name__ == '__main__' and sys.prefix == sys.base_prefix:
    project_runtime = Path(__file__).resolve().parent / '.venv' / 'bin' / 'python'
    if project_runtime.exists():
        os.execv(str(project_runtime), [str(project_runtime), str(Path(__file__).resolve()), *sys.argv[1:]])
from src.vacation_planner.entrypoints.cli.VacationPlannerCliApplication import (
    VacationPlannerCliApplication,
)
from src.vacation_planner.entrypoints.gui.VacationPlannerDashboardApplication import (
    VacationPlannerDashboardApplication,
)
from src.vacation_planner.entrypoints.web.VacationPlannerHttpServer import (
    VacationPlannerHttpServer,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Modulares Urlaubsplanungs-Tool - Clean Architecture Reiseplanungs-Aggregator"
    )
    parser.add_argument(
        "--cli",
        action="store_true",
        help="Runs the interactive console CLI application instead of the GUI dashboard",
    )
    parser.add_argument(
        "--serve",
        action="store_true",
        help="Starts the REST Web API server on the specified port",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port for the REST Web API server (default: 8080)",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host address for the REST Web API server (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--origin",
        type=str,
        default="Berlin",
        help="Origin location name for CLI mode (default: Berlin)",
    )
    parser.add_argument(
        "--destination",
        type=str,
        default="Paris",
        help="Destination location name for CLI mode (default: Paris)",
    )
    parser.add_argument(
        "--start-date",
        type=str,
        default="2026-07-01",
        help="Start date in ISO format YYYY-MM-DD (default: 2026-07-01)",
    )
    parser.add_argument(
        "--end-date",
        type=str,
        default="2026-07-07",
        help="End date in ISO format YYYY-MM-DD (default: 2026-07-07)",
    )
    parser.add_argument(
        "--budget",
        type=float,
        default=1200.0,
        help="Maximum budget in EUR (default: 1200.00)",
    )
    parser.add_argument(
        "--travelers",
        type=int,
        default=1,
        help="Number of travelers (default: 1)",
    )

    parser.add_argument('--demo', action='store_true', help='Expliziter Demomodus mit simulierten Altdaten')
    parser.add_argument('--search-json', metavar='DATEI', help='Echte Zielsuche mit JSON-Kriterien, Ergebnis als JSON')
    args = parser.parse_args()

    if args.search_json:
        import json
        from src.vacation_planner.core.planning.SearchRequest import SearchRequest
        from src.vacation_planner.core.planning.SearchContext import SearchContext
        from src.vacation_planner.core.planning.DiscoveryService import DiscoveryService
        from src.vacation_planner.infrastructure.planning.DestinationCatalog import DestinationCatalog
        from src.vacation_planner.infrastructure.planning.OpenTravelProvider import OpenTravelProvider
        from src.vacation_planner.infrastructure.planning.TripStore import TripStore
        with open(args.search_json) as stream:
            request = SearchRequest(**json.load(stream))
        request.validate()
        results = []
        def emit(kind, value):
            if kind == 'result':
                results.append(value)
            else:
                print(value, file=sys.stderr)
        try:
            DiscoveryService(DestinationCatalog(), OpenTravelProvider(TripStore())).search(
                request, SearchContext(seconds=request.timeout_seconds, budget=request.request_budget), emit)
        except (InterruptedError, KeyboardInterrupt):
            print('Suche beendet; vorhandene Teilergebnisse folgen.', file=sys.stderr)
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return
    if (args.cli or args.serve) and not args.demo:
        parser.error('Die alten CLI/API-Adapter simulieren Angebote. Nur mit --demo verfügbar; echte Suche: --search-json DATEI.')
    if args.demo:
        print('DEMOMODUS: simulierte Preise und Angebote, nicht buchbar.', file=sys.stderr)

    if args.serve:
        print(f"Starting Vacation Planner REST Web API server at http://{args.host}:{args.port}")
        server = VacationPlannerHttpServer(host=args.host, port=args.port)
        try:
            server.start(run_in_background=False)
        except KeyboardInterrupt:
            print("\nShutting down server...")
            server.stop()
            print("Server stopped cleanly.")
    elif args.cli:
        cli = VacationPlannerCliApplication()
        cli.run_interactive(
            origin=args.origin,
            destination=args.destination,
            start_date=args.start_date,
            end_date=args.end_date,
            maximum_budget=args.budget,
            travelers=args.travelers,
        )
    else:
        # Default mode: Launch the Visual Dashboard GUI window
        if args.demo:
            dashboard_app = VacationPlannerDashboardApplication()
        else:
            from src.vacation_planner.entrypoints.gui.SurprisePlannerApplication import SurprisePlannerApplication
            dashboard_app = SurprisePlannerApplication()
        if args.demo:
            window = dashboard_app.create_window()
            window.title('DEMOMODUS · Simulierte Angebote · Reiseplaner Dashboard')
            window.mainloop()
        else:
            dashboard_app.start_dashboard()


if __name__ == "__main__":
    main()

