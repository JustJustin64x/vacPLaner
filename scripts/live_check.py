"""Manual, opt-in integration check; does not run inside the unit suite.

PYTHONPATH=. .venv/bin/python scripts/live_check.py
Only known free public sources, no accounts. Output stays in ignored tmp/.
"""
import json
from pathlib import Path
from src.vacation_planner.core.planning.SearchRequest import SearchRequest, next_july
from src.vacation_planner.core.planning.SearchContext import SearchContext
from src.vacation_planner.core.planning.DiscoveryService import DiscoveryService
from src.vacation_planner.infrastructure.planning.DestinationCatalog import DestinationCatalog
from src.vacation_planner.infrastructure.planning.OpenTravelProvider import OpenTravelProvider
from src.vacation_planner.infrastructure.planning.TripStore import TripStore, timestamp

output=Path('tmp/live-check');output.mkdir(parents=True,exist_ok=True)
criteria=json.loads(Path('docs/beispielsuche.json').read_text())
criteria['earliest'],criteria['latest']=next_july()
request=SearchRequest(**criteria)
context=SearchContext(seconds=300,budget=24)
store=TripStore(output/'check.sqlite3')
report={'checked_at':timestamp(),'request':criteria,'events':[],'results':[]}

def emit(kind,value):
    if kind=='result':report['results'].append(value)
    else:
        print(kind,value,flush=True)
        report['events'].append({'kind':kind,'message':value})
try:
    DiscoveryService(DestinationCatalog(),OpenTravelProvider(store)).search(request,context,emit)
except InterruptedError as exc:
    emit('warning',str(exc))
finally:
    report['calls']=context.calls
    (output/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print('Report:',output/'report.json')
assert report['results'], 'Keine Ergebnisse: Quellenstatus im Report prüfen'
assert any(len(t['lodgings'])>=2 for t in report['results']), 'Keine zwei realen Unterkunftsalternativen'
assert any(any(o.get('kilometers') for o in t['transports']) for t in report['results']), 'Keine echte Straßenroute'
assert all(t['cost_summary']['budget_ok'] is None for t in report['results']), 'Unvollständige Preise dürfen Budget nicht bestätigen'
