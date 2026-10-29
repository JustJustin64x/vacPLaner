"""Bounded real searches. No bookings, user accounts, images or paid endpoints.

Run: .venv/bin/python scripts/live_offers.py --live --output tmp/live-offers
Prices are volatile. This script deliberately verifies dates, identity, scope,
cost propagation and persistence rather than asserting a fixed fare.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

from src.vacation_planner.core.planning.DiscoveryService import DiscoveryService
from src.vacation_planner.core.planning.SearchContext import SearchContext
from src.vacation_planner.core.planning.SearchRequest import SearchRequest
from src.vacation_planner.core.planning.RankingService import RankingService
from src.vacation_planner.infrastructure.planning.DestinationCatalog import DestinationCatalog
from src.vacation_planner.infrastructure.planning.OpenTravelProvider import OpenTravelProvider
from src.vacation_planner.infrastructure.planning.TripStore import TripStore
from src.vacation_planner.infrastructure.planning.PdfTripPresenter import PdfTripPresenter


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live',action='store_true',help='Explizit echte, begrenzte Nur-Lese-Abfragen ausführen')
    parser.add_argument('--output',type=Path,default=Path('tmp/live-offers'))
    parser.add_argument('--case',action='append',help='Optional nur benannte Prüffälle ausführen')
    args=parser.parse_args()
    if not args.live:parser.error('--live ist für den echten Quellenabruf erforderlich')
    args.output.mkdir(parents=True,exist_ok=True)
    report={'checked_at':datetime.now(timezone.utc).isoformat(timespec='seconds'),'cases':[]}
    for label,destination,origin,start,end,adults,rooms in (
        ('rail-near','Brünn','Prag','2026-11-12','2026-11-14',2,1),
        ('lodging-near','Innsbruck','Berlin','2026-11-23','2026-11-25',2,1),
        ('rail-group-five','Brünn','Prag','2026-11-12','2026-11-14',5,3),
        ('rail-july-horizon','Brünn','Prag','2027-07-01','2027-07-07',5,3),
        ('requested-july-group','Innsbruck','Berlin','2027-07-01','2027-07-07',5,3),
        ('activity-bled','Bled','Berlin','2026-11-12','2026-11-14',5,3),
        ('activity-berlin','Berlin','Prag','2026-11-12','2026-11-14',2,1),
    ):
        if args.case and label not in args.case:continue
        store=TripStore(args.output/(label+'.sqlite3'));provider=OpenTravelProvider(store)
        catalog=DestinationCatalog();catalog.destinations=[catalog.resolve(destination)]
        request=SearchRequest(origin=origin,earliest=start,latest=end,min_days=(datetime.fromisoformat(end)-datetime.fromisoformat(start)).days+1,
                              max_days=(datetime.fromisoformat(end)-datetime.fromisoformat(start)).days+1,
                              adults=adults,rooms=rooms,modes=['Zug','Flug'],shortlist=3,surroundings=False,show_ideas=True,timeout_seconds=100,request_budget=8)
        context=SearchContext(seconds=100,budget=8);events=[]
        def emit(kind,value):
            if kind in ('phase','warning'):print(label,kind,value,flush=True);events.append({'kind':kind,'message':value})
        trips=DiscoveryService(catalog,provider).search(request,context,emit)
        case={'name':label,'parameters':request.to_dict(),'static_calls':context.calls,'price_calls':getattr(getattr(context,'price_context',None),'calls',0),'events':events,'trips':trips}
        for trip in trips:
            # Selecting a newly found alternative here is an explicit test action.
            priced=[i for i,l in enumerate(trip['lodgings']) if l.get('offer_id')]
            if priced:trip['selected_lodging']=priced[0]
            RankingService.recompute(trip)
            identifier=store.save('Echter Angebotsprüflauf · '+label,trip)
            reopened=store.load(identifier)
            case['persistence_ok']=reopened.get('offer_searches')==trip.get('offer_searches')
            model=PdfTripPresenter.present(reopened)
            case['pdf_model_cost']=model['cost'];case['selected_lodging']=model['lodging']
        report['cases'].append(case)
        (args.output/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    print('Report:',args.output/'report.json')


if __name__=='__main__':main()
