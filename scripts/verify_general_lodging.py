#!/usr/bin/env python3
"""Opt-in public acceptance campaign through ordinary discovery/offer services.

Uses the existing regional OSM inventory read-only and a separate temporary trip
store. A city is resolved from the guide catalogue or exact GeoNames inventory,
never from a list of hotels. No model start, booking, account or payment calls.
"""
import argparse
from contextlib import contextmanager
import json
from pathlib import Path
import sqlite3
import sys
import tempfile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from vacation_planner.infrastructure.planning.DestinationInventory import DestinationInventory
from vacation_planner.infrastructure.planning.DestinationCatalog import DestinationCatalog
from vacation_planner.infrastructure.planning.TripStore import TripStore
from vacation_planner.infrastructure.planning.OpenTravelProvider import OpenTravelProvider
from vacation_planner.core.planning.SearchRequest import SearchRequest
from vacation_planner.core.planning.SearchContext import SearchContext
from vacation_planner.core.planning.SearchDiagnostics import SearchDiagnostics
from vacation_planner.core.planning.DiscoveryService import DiscoveryService


class ReadInventory(DestinationInventory):
    def __init__(self,path):self.path=path
    @contextmanager
    def connect(self):
        db=sqlite3.connect(self.path.resolve().as_uri()+'?mode=ro',uri=True)
        try:yield db
        finally:db.close()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--live',action='store_true');p.add_argument('--target')
    p.add_argument('--target-id',help='Explicit public settlement ID to disambiguate same-name towns')
    p.add_argument('--start',default='2026-11-23');p.add_argument('--end',default='2026-11-25')
    p.add_argument('--adults',type=int,default=2);p.add_argument('--rooms',type=int,default=1)
    p.add_argument('--children-ages',default='',help='Comma-separated ages at arrival')
    p.add_argument('--room-assignments',type=Path,help='JSON array of actual adult/child-age room assignments')
    p.add_argument('--radius',default='3');p.add_argument('--budget',type=int,default=40);p.add_argument('--seconds',type=int,default=300)
    p.add_argument('--inventory',type=Path,default=Path.home()/'Library/Application Support/Urlaubsplaner/destinations.sqlite3')
    p.add_argument('--output',type=Path,required=True);p.add_argument('--resume',type=Path)
    p.add_argument('--case-file',type=Path,help='Explicit public acceptance data; does not claim new directory discovery')
    p.add_argument('--case-key',help='Case key from the public acceptance JSON')
    a=p.parse_args()
    if not a.live:p.error('Explicit --live required')
    if sum(bool(x) for x in (a.resume,a.target,a.case_file))!=1:p.error('Exactly one of --target, --resume, --case-file required')
    if a.case_file and not a.case_key:p.error('--case-key required with --case-file')
    if not 2<=a.budget<=40 or not 10<=a.seconds<=600:p.error('Shared acceptance limit: 2–40 HTTP, 10–600 seconds')
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='vac-lodging-accept-') as folder:
        store=TripStore(Path(folder)/'trips.sqlite3');cat=DestinationCatalog();cat.inventory=ReadInventory(a.inventory)
        provider=OpenTravelProvider(store,catalog=cat)
        ctx=SearchContext(seconds=a.seconds,budget=a.budget)
        def emit(kind,value):
            if kind=='phase':print(value,flush=True)
            elif kind=='offer_partial':a.output.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
        if a.case_file:
            data=json.loads(a.case_file.read_text())
            if data.get('schema_version')!=1 or a.case_key not in data.get('cases',{}):p.error('Unknown public case format or key')
            trip=data['cases'][a.case_key]['trip'];ctx.lodging_continue=False
            print('Public acceptance case: existing published directory identity, not a newly discovered directory result',flush=True)
        elif a.resume:
            trip=json.loads(a.resume.read_text());ctx.lodging_continue=True
        else:
            base=cat.resolve(a.target)
            if not base:
                with cat.inventory.connect() as db:
                    matches=[json.loads(r[0]) for r in db.execute("SELECT payload FROM places WHERE kind='settlement' AND json_extract(payload,'$.name')=?",(a.target,))]
                if a.target_id:matches=[m for m in matches if m['id']==a.target_id]
                if len(matches)!=1:p.error('Target not unambiguously resolved in local catalogue/inventory; use --target-id')
                base=matches[0]
            base=dict(base,inventory_place=True)
            from datetime import date
            days=(date.fromisoformat(a.end)-date.fromisoformat(a.start)).days+1
            from vacation_planner.core.planning.RoomParty import ages_from_text
            request=SearchRequest(children_ages=ages_from_text(a.children_ages),room_assignments=json.loads(a.room_assignments.read_text()) if a.room_assignments else [],earliest=a.start,latest=a.end,min_days=days,max_days=days,adults=a.adults,rooms=a.rooms,modes=['Zug'],lodging_radius_km=a.radius,activity_radius_km=a.radius,regional_queries=0,show_ideas=True,price_targets=0)
            request.validate();ctx.request=request
            service=DiscoveryService(cat,provider);service.diagnostics=SearchDiagnostics(request)
            trip=service.research(request,ctx,provider.origin('Berlin','',ctx),base,emit)
            if trip is None:p.error('No ordinary result produced; directory/criteria outcome remains open')
            print('Directory:',len(trip['lodging_research']['entries']),'unique properties',flush=True)
            a.output.with_suffix('.directory.json').write_text(json.dumps(trip,ensure_ascii=False,indent=2)+'\n')
        trip=provider.research_offers(trip,ctx,emit,categories=['lodging'])
        a.output.write_text(json.dumps(trip,ensure_ascii=False,indent=2)+'\n')
        print(json.dumps(trip['lodging_research']['metrics'],ensure_ascii=False),flush=True)


if __name__=='__main__':main()
