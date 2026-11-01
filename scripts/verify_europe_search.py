"""Reproducible bounded comparisons on the real application database.

Reads existing places/features; no country or PBF downloads. Does not save or
modify user trips. --live enables the normal provider's bounded web access.
"""
import argparse
import json
import resource
import sys
import time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.vacation_planner.entrypoints.gui.SurprisePlannerApplication import SurprisePlannerApplication
from src.vacation_planner.core.planning.SearchRequest import SearchRequest
from src.vacation_planner.core.planning.SearchContext import SearchContext
from src.vacation_planner.core.planning.DiscoveryService import DiscoveryService
from src.vacation_planner.infrastructure.planning.TripStore import timestamp

SCOPES=[('Alpen','AT',['Tyrol']),('Mittelmeer','HR',[]),('Atlantik','FR',['Brittany']),
        ('Ostsee','DE',['Mecklenburg-Vorpommern']),('Binnenland','PL',['Lower Silesia']),('Nordosteuropa','EE',[])]
CASES=[('Wandern und Ruhe',{'Wandern':5,'Ruhe':5}),('Baden und Wandern',{'Baden':5,'Wandern':5}),
       ('Kultur und Nachtleben',{'Kultur':5,'Feiern':5}),('Barhopping',{'Barhopping':5}),('Kleine Orte',{'Wandern':5,'Baden':5})]

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--live',action='store_true');parser.add_argument('--output',type=Path,default=Path('tmp/europe-verification'));parser.add_argument('--scope',action='append');parser.add_argument('--case',action='append')
    args=parser.parse_args()
    if not args.live:parser.error('--live bestätigt die normale begrenzte Quellenrecherche')
    args.output.mkdir(parents=True,exist_ok=True);start=time.monotonic();app=SurprisePlannerApplication();startup=time.monotonic()-start
    with app.store.connect() as db:before=db.execute('SELECT * FROM trips ORDER BY id').fetchall()
    report=dict(checked_at=timestamp(),startup_seconds=startup,inventory_counts=app.inventory.counts(),catalog_representatives=len(app.catalog.destinations),cases=[])
    for scope,code,regions in SCOPES:
        if args.scope and scope not in args.scope:continue
        for name,interests in CASES:
            if args.case and name not in args.case:continue
            request=SearchRequest(origin='Berlin',earliest='2027-07-01',latest='2027-07-31',min_days=7,max_days=7,adults=2,rooms=1,
                countries=[code],regions=regions,interests=interests,modes=['Zug'],shortlist=3,candidate_pool=10,regional_queries=0,price_targets=0,
                request_budget=4,timeout_seconds=120,show_ideas=True,target_type='kleiner Ort' if name=='Kleine Orte' else 'gemischt')
            context=SearchContext(seconds=120,budget=4);service=DiscoveryService(app.catalog,app.provider);events=[];trips=[];begin=time.monotonic();error=None
            def emit(kind,value):
                if kind in ('warning','phase'):events.append(dict(kind=kind,message=value))
                if kind=='result':trips.append(value)
            try:trips=service.search(request,context,emit)
            except (InterruptedError,ValueError,OSError) as exc:error=str(exc)
            elapsed=time.monotonic()-begin
            case=dict(scope=scope,name=name,parameters=request.to_dict(),seconds=elapsed,http_calls=context.calls,error=error,
                diagnostics=service.diagnostics.data,results=[dict(name=t['destination']['name'],id=t['destination']['id'],country=t['destination']['code'],
                type=t['destination']['type'],latitude=t['destination']['latitude'],longitude=t['destination']['longitude'],score=t['score'],interest_match=t['interest_match'],
                why=t['explanation'],evidence=t['interest_evidence'],filter_status=t['filter_status'],open_criteria=t['open_criteria'],missing_costs=t['cost_summary']['missing'],
                activities=[dict(name=a['name'],source=a['source'],distance_km=a.get('distance_km'),distance_kind=a.get('distance_kind'),access_research=a.get('access_research')) for a in t['activities']],
                alternatives_note='Belege werden je Kategorie gesättigt; Kombinationen nach schwächster Komponente begrenzt. Gemeinsame Aktivitäten und Nähe gruppieren Regionen grenzübergreifend. Untersuchte Kartierung ist keine bestätigte Erreichbarkeit.') for t in trips])
            report['cases'].append(case)
            with app.store.connect() as db:report['user_trips_unchanged']=before==db.execute('SELECT * FROM trips ORDER BY id').fetchall()
            report['max_rss_bytes']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            (args.output/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
            print(scope,name,round(elapsed,2),'s',len(trips),'results',context.calls,'HTTP',error,flush=True)
    print('REPORT',args.output/'report.json',flush=True)

if __name__=='__main__':main()
