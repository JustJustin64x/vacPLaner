"""Bounded real searches through the normal desktop application's discovery path.

Does not download countries. Set up local data in the application first.
Does not write test trips to the user's trip database or change preferences.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys
import time

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.vacation_planner.entrypoints.gui.SurprisePlannerApplication import SurprisePlannerApplication
from src.vacation_planner.core.planning.DiscoveryService import DiscoveryService
from src.vacation_planner.core.planning.SearchRequest import SearchRequest, next_july
from src.vacation_planner.core.planning.SearchContext import SearchContext
from src.vacation_planner.infrastructure.planning.TripStore import TripStore, timestamp


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live',action='store_true');parser.add_argument('--output',type=Path,default=Path('tmp/discovery-v3/searches'))
    parser.add_argument('--case',action='append',help='Optional einen der benannten Interessenfälle auswählen')
    args=parser.parse_args()
    if not args.live:parser.error('--live startet ausdrücklich echte begrenzte Recherche')
    args.output.mkdir(parents=True,exist_ok=True)
    begin=time.monotonic();app=SurprisePlannerApplication();startup=time.monotonic()-begin
    before=app.store.list();catalog=app.catalog;inventory=app.inventory
    with inventory.connect() as db:
        kinds=Counter()
        for (raw,) in db.execute('SELECT payload FROM places'):kinds[json.loads(raw)['feature_code']]+=1
        feature_count=db.execute('SELECT count(*) FROM features').fetchone()[0]
        entities=db.execute('SELECT count(*) FROM entities').fetchone()[0]
    report={'checked_at':timestamp(),'normal_app_catalog_count':len(catalog.destinations),'startup_seconds':round(startup,3),
            'coverage':inventory.coverage(),'feature_codes':dict(kinds),'unique_osm_features':feature_count,'wikidata_entities':entities,'cases':[]}
    earliest,latest=next_july()
    for name,interests,countries in (
        ('Wandern und Ruhe',{'Wandern':5,'Natur':4,'Ruhe':5},[]),
        ('Kultur und Nachtleben',{'Kultur':5,'Feiern':5},[]),
        ('Baden und Wandern',{'Baden':5,'Wandern':5},[]),
        ('Barhopping',{'Barhopping':5},[]),
    ):
        if args.case and name not in args.case:continue
        request=SearchRequest(origin='Berlin',earliest=earliest,latest=latest,adults=5,rooms=3,interests=interests,countries=countries,
            shortlist=3,candidate_pool=35,price_targets=0,regional_queries=0,timeout_seconds=100,request_budget=10,show_ideas=True)
        context=SearchContext(seconds=100,budget=10);events=[];trips=[];start=time.monotonic()
        def emit(kind,value):
            if kind in ('phase','warning'):print(name,kind,value,flush=True);events.append({'kind':kind,'message':value})
            if kind in ('result','offer_partial'):
                existing=next((i for i,t in enumerate(trips) if t['id']==value['id']),None)
                if existing is None:trips.append(value)
                else:trips[existing]=value
        service=DiscoveryService(catalog,app.provider)
        error=None
        try:trips=service.search(request,context,emit)
        except (InterruptedError,OSError,ValueError) as exc:error=str(exc)
        elapsed=time.monotonic()-start
        saved=TripStore(args.output/'verification-trips.sqlite3');checks=[]
        for trip in trips:
            key=saved.save('Live-Prüfung '+name,trip);opened=saved.load(key)
            checks.append(opened['destination']==trip['destination'] and opened['interest_evidence']==trip['interest_evidence'])
        (args.output/(name.replace(' ','-')+'.json')).write_text(json.dumps(trips,ensure_ascii=False,indent=2))
        report['cases'].append({'name':name,'parameters':request.to_dict(),'seconds':round(elapsed,3),'http_calls':context.calls,'error':error,
            'diagnostics':service.diagnostics.data,'persistence_ok':all(checks),
            'results':[{'name':t['destination']['name'],'id':t['destination']['id'],'country':t['destination']['code'],'type':t['destination']['type'],
                        'score':t['score'],'interest_match':t['interest_match'],'explanation':t['explanation'],'filter_status':t['filter_status'],
                        'missing':t['cost_summary']['missing'],'source':t['destination']['source']} for t in trips]})
        report['existing_saved_trips_unchanged']=before==app.store.list()
        (args.output/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    print('Report:',args.output/'report.json',flush=True)


if __name__=='__main__':main()
