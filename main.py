#!/usr/bin/env python3
"""
Main entry point for the Modulares Urlaubsplanungs-Tool.
Provides CLI execution or HTTP REST API server startup.
"""
from __future__ import annotations

import argparse
import sys
from src.vacation_planner.entrypoints.cli.VacationPlannerCliApplication import (
    VacationPlannerCliApplication,
)
from src.vacation_planner.entrypoints.web.VacationPlannerHttpServer import (
    VacationPlannerHttpServer,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Modulares Urlaubsplanungs-Tool - Clean Architecture Reiseplanungs-Aggregator"
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
        help="Origin location name (default: Berlin)",
    )
    parser.add_argument(
        "--destination",
        type=str,
        default="Paris",
        help="Destination location name (default: Paris)",
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

    args = parser.parse_args()

    if args.serve:
        print(f"Starting Vacation Planner REST Web API server at http://{args.host}:{args.port}")
        server = VacationPlannerHttpServer(host=args.host, port=args.port)
        try:
            server.start(run_in_background=False)
        except KeyboardInterrupt:
            print("\nShutting down server...")
            server.stop()
            print("Server stopped cleanly.")
    else:
        cli = VacationPlannerCliApplication()
        cli.run_interactive(
            origin=args.origin,
            destination=args.destination,
            start_date=args.start_date,
            end_date=args.end_date,
            maximum_budget=args.budget,
            travelers=args.travelers,
        )


if __name__ == "__main__":
    main()
