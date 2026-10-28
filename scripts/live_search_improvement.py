"""One bounded, explicit live search. Fresh cache, recording public responses.
Usage: PYTHONPATH=. .venv/bin/python scripts/live_search_improvement.py
Never a scheduled monitor; no retries, at most 24 HTTP calls and 300 seconds.
"""
import json
import argparse
from pathlib import Path
from src.vacation_planner.core.planning.SearchRequest import SearchRequest
from src.vacation_planner.core.planning.SearchContext import SearchContext
from src.vacation_planner.core.planning.DiscoveryService import DiscoveryService
from src.vacation_planner.infrastructure.planning.DestinationCatalog import DestinationCatalog
from src.vacation_planner.infrastructure.planning.OpenTravelProvider import OpenTravelProvider
from src.vacation_planner.infrastructure.planning.PublicHttpClient import PublicHttpClient
from src.vacation_planner.infrastructure.planning.TripStore import TripStore,timestamp

args=argparse.ArgumentParser()
args.add_argument('--budget',type=int,default=24)
args.add_argument('--shortlist',type=int,default=6)
args.add_argument('--report',default='docs/SUCHLAUF_2026-10-28.json')
args=args.parse_args()
if not 4<=args.budget<=24:raise ValueError('Liveprüfung: 4–24 HTTP-Aufrufe')
root=Path('tmp/search-improvement/live');root.mkdir(parents=True,exist_ok=True)
run=root/timestamp().replace(':','-');run.mkdir()
class RecordingHttp(PublicHttpClient):
    def get(self,url,context):
        body,stamp=super().get(url,context)
        name=f'{context.calls:02d}'
        (run/(name+'.body')).write_text(body)
        calls.append(dict(url=url,retrieved_at=stamp,file=name+'.body'))
        return body,stamp
calls=[];events=[];results=[]
request=SearchRequest(earliest='2027-07-01',latest='2027-07-31',adults=5,rooms=3,budget='2000',
    interests={'Wandern':5,'Baden':5,'Feiern':5},request_budget=args.budget,shortlist=args.shortlist,timeout_seconds=300,show_ideas=True)
context=SearchContext(seconds=300,budget=args.budget)
service=DiscoveryService(DestinationCatalog(),OpenTravelProvider(TripStore(run/'live.sqlite3'),RecordingHttp()))
def emit(kind,value):
    if kind=='result':results.append(value)
    else:events.append(dict(kind=kind,value=value))
    if kind in ('phase','warning'):print(value,flush=True)
try:service.search(request,context,emit)
except InterruptedError as exc:print(str(exc),flush=True)
report=dict(started=run.name,request=request.to_dict(),calls=calls,http_calls=context.calls,
    diagnostic=service.diagnostics.data,results=results,events=events)
(run/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
Path(args.report).write_text(json.dumps({k:v for k,v in report.items() if k not in ('events','results')},ensure_ascii=False,indent=2))
summary=[dict(destination=t['destination']['name'],type=t['destination'].get('type'),base=t['destination'].get('base_name'),status=t['filter_status'],lodgings=[dict(name=l['name'],place=l['source_place'],distance_km=l['distance_km'],source=l['source']) for l in t['lodgings']],activities=[dict(name=a['name'],topics=a['topics'],place=a['source_place'],source=a['source']) for a in t['activities']],budget_ok=t['cost_summary']['budget_ok']) for t in results]
public=json.loads(Path(args.report).read_text());public['results']=summary
Path(args.report).write_text(json.dumps(public,ensure_ascii=False,indent=2))
print('REPORT',str(run/'report.json'),flush=True)
print('RESULTS',[(r['destination']['name'],r['filter_status'],len(r['lodgings']),len(r['activities'])) for r in results],flush=True)
